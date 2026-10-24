"""Run episodes against an OpenAI model. One JSON file per episode; existing files are skipped.

  python run.py --model gpt-4.1-mini --which posctrl
  python run.py --model gpt-4.1-mini --which grid --workers 8
"""
import argparse
import itertools
import json
import os
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

from env import Episode, N_AGENTS, STEPS, MAX_ROUNDS, START_ROUND, TOOLS, SELF_REPORT_Q

HERE = pathlib.Path(__file__).resolve().parent
NUDGE = "Continue. Use the tools, and call submit_answer when you are done."


def api_key():
    k = os.environ.get("OPENAI_API_KEY")
    if k:
        return k
    env = HERE.parents[1] / "backend" / ".env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    sys.exit("OPENAI_API_KEY not found")


CLIENT = OpenAI(api_key=api_key(), max_retries=6, timeout=120)


def call(model, messages, tools_on=True):
    kw = dict(model=model, messages=messages, tools=TOOLS)
    if tools_on:
        kw["parallel_tool_calls"] = False
    else:
        kw["tool_choice"] = "none"
    if model.startswith("gpt-5"):
        kw["max_completion_tokens"] = 6000
    else:
        kw["temperature"] = 1.0
        kw["max_tokens"] = 1500
    for attempt in range(6):
        try:
            return CLIENT.chat.completions.create(**kw)
        except Exception as e:  # rate limits / transient errors; the SDK already retries some
            if attempt == 5:
                raise
            time.sleep(2 ** attempt * 3)


def run_llm_episode(model, ep):
    msgs = {i: [{"role": "system", "content": ep.system_prompt(i)},
                {"role": "user", "content": ep.task_prompt(i)}] for i in range(N_AGENTS)}
    usage = {"prompt": 0, "completion": 0}
    active = set(range(N_AGENTS))
    for rnd in range(MAX_ROUNDS):
        for i in sorted(active):
            if rnd < START_ROUND[i]:
                continue
            r = call(model, msgs[i])
            usage["prompt"] += r.usage.prompt_tokens
            usage["completion"] += r.usage.completion_tokens
            m = r.choices[0].message
            ep.steps[i] += 1
            if m.tool_calls:
                tc = m.tool_calls[0]
                msgs[i].append({"role": "assistant", "content": m.content,
                                "tool_calls": [{"id": tc.id, "type": "function",
                                                "function": {"name": tc.function.name,
                                                             "arguments": tc.function.arguments}}]})
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                out = ep.tool(i, tc.function.name, args, rnd)
                msgs[i].append({"role": "tool", "tool_call_id": tc.id, "content": out})
                if tc.function.name == "submit_answer":
                    active.discard(i)
                    msgs[i].append({"role": "user", "content": SELF_REPORT_Q})
                    rr = call(model, msgs[i], tools_on=False)
                    usage["prompt"] += rr.usage.prompt_tokens
                    usage["completion"] += rr.usage.completion_tokens
                    ep.self_report[i] = rr.choices[0].message.content or ""
                    msgs[i].append({"role": "assistant", "content": ep.self_report[i]})
            else:
                msgs[i].append({"role": "assistant", "content": m.content or ""})
                msgs[i].append({"role": "user", "content": NUDGE})
            if ep.steps[i] >= STEPS[i]:
                active.discard(i)
        if not active:
            break
    d = ep.to_json()
    d["model"], d["usage"], d["transcripts"] = model, usage, msgs
    return d


# ----- Responses API (GPT-6 / GPT-5.6 models: function tools need /v1/responses) -----
RESP_TOOLS = [{"type": "function", "name": t["function"]["name"], "description": t["function"]["description"],
               "parameters": t["function"]["parameters"], "strict": False} for t in TOOLS]


def uses_responses(model):
    return model.startswith("gpt-6") or model.startswith("gpt-5.6")


def rcall(model, instructions, inp, prev, tools_on=True):
    kw = dict(model=model, instructions=instructions, input=inp, tools=RESP_TOOLS,
              max_output_tokens=8000, parallel_tool_calls=False)
    if prev:
        kw["previous_response_id"] = prev
    if not tools_on:
        kw["tool_choice"] = "none"
    for attempt in range(6):
        try:
            return CLIENT.responses.create(**kw)
        except Exception:
            if attempt == 5:
                raise
            time.sleep(2 ** attempt * 3)


def run_responses_episode(model, ep):
    pending = {i: [{"role": "user", "content": ep.task_prompt(i)}] for i in range(N_AGENTS)}
    prev = {i: None for i in range(N_AGENTS)}
    log = {i: [] for i in range(N_AGENTS)}
    usage = {"prompt": 0, "completion": 0, "cached": 0}

    def go(i, tools_on=True):
        r = rcall(model, ep.system_prompt(i), pending[i], prev[i], tools_on)
        prev[i] = r.id
        usage["prompt"] += r.usage.input_tokens
        usage["completion"] += r.usage.output_tokens
        usage["cached"] += getattr(r.usage.input_tokens_details, "cached_tokens", 0) or 0
        out = [{"type": o.type, **({"name": o.name, "arguments": o.arguments} if o.type == "function_call" else {})}
               for o in r.output]
        log[i].append({"in": pending[i], "out": out, "text": r.output_text})
        return r

    active = set(range(N_AGENTS))
    for rnd in range(MAX_ROUNDS):
        for i in sorted(active):
            if rnd < START_ROUND[i]:
                continue
            r = go(i)
            ep.steps[i] += 1
            calls = [o for o in r.output if o.type == "function_call"]
            if calls:
                tc = calls[0]
                try:
                    args = json.loads(tc.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                res = ep.tool(i, tc.name, args, rnd)
                pending[i] = [{"type": "function_call_output", "call_id": tc.call_id, "output": res}] + \
                             [{"type": "function_call_output", "call_id": c.call_id,
                               "output": "Error: one tool call per turn."} for c in calls[1:]]
                if tc.name == "submit_answer":
                    active.discard(i)
                    pending[i].append({"role": "user", "content": SELF_REPORT_Q})
                    ep.self_report[i] = go(i, tools_on=False).output_text or ""
            else:
                pending[i] = [{"role": "user", "content": NUDGE}]
            if ep.steps[i] >= STEPS[i]:
                active.discard(i)
        if not active:
            break
    d = ep.to_json()
    d["model"], d["usage"], d["transcripts"] = model, usage, log
    return d


def specs(which, seeds):
    if which == "posctrl":
        return [(False, False, False, 1, s) for s in range(100, 100 + seeds)]
    if which == "posctrl3":
        return [(False, False, False, 3, s) for s in range(300, 300 + seeds)]
    if which == "posctrl2":
        return [(False, False, False, 2, s) for s in range(200, 200 + seeds)]
    return [(a, b, c, False, s) for a, b, c in itertools.product([True, False], repeat=3) for s in range(seeds)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--which", choices=["posctrl", "posctrl2", "posctrl3", "grid"], required=True)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--smoke", action="store_true", help="one unregistered seed (999) into results_smoke/")
    a = ap.parse_args()
    out = HERE / ("results_smoke" if a.smoke else "results") / a.model
    out.mkdir(parents=True, exist_ok=True)
    todo = []
    sps = specs(a.which, a.seeds)
    if a.smoke:
        sps = [sp[:4] + (999,) for sp in sps[:1]]
    for sp in sps:
        ep = Episode(*sp)
        f = out / f"{ep.cell}_s{ep.seed}.json"
        if not f.exists():
            todo.append((ep, f))
    print(f"{len(todo)} episodes to run for {a.model}", flush=True)

    def job(ep, f):
        d = (run_responses_episode if uses_responses(a.model) else run_llm_episode)(a.model, ep)
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, indent=1), encoding="utf-8")
        tmp.replace(f)
        return ep.cell, ep.seed, d["outcomes"], d["usage"]

    with ThreadPoolExecutor(a.workers) as pool:
        futs = [pool.submit(job, ep, f) for ep, f in todo]
        for fu in as_completed(futs):
            try:
                cell, seed, o, u = fu.result()
                print(cell, seed, {k: o[k] for k in ("contact", "request", "help", "canary_flow",
                                                    "seeker_foreign", "seeker_fabricated", "interference")},
                      u, flush=True)
            except Exception as e:
                print("EPISODE FAILED:", repr(e)[:300], flush=True)


if __name__ == "__main__":
    main()
