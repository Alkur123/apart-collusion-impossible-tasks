"""Fill REPORT.md placeholders from the result files -> REPORT_FILLED.md. No number is typed by hand.

Placeholders whose text depends on Experiment 2's outcome are read from report/e2_text.md
(written after the results are known); until then they render as [PENDING].
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from env import Episode, REQUEST_NOTE, RULE_TEXT, POSCTRL_TEXT, POSCTRL_STRONG_TEXT, POSCTRL_HOLDER_TEXT, SELF_REPORT_Q  # noqa: E402

PRICE = {"gpt-6.1-sol": (2.00, 0.10, 10.00), "gpt-6-luna": (0.10, 0.01, 0.50)}  # $/1M in, cached in, out (pricing page, 24 Oct)


def cost():
    total, parts = 0.0, []
    for m, (pi, pc, po) in PRICE.items():
        tin = tc = tout = 0
        for f in (ROOT / "results" / m).glob("*.json"):
            if f.name == "summary.json":
                continue
            u = json.loads(f.read_text(encoding="utf-8"))["usage"]
            tin += u["prompt"]; tc += u.get("cached", 0); tout += u["completion"]
        c = ((tin - tc) * pi + tc * pc + tout * po) / 1e6
        total += c
        parts.append(f"{m} ${c:.2f}")
    return f"about ${total:.0f} for all registered runs ({'; '.join(parts)}; plus a few cents of gpt-5.4-mini and unregistered smoke runs)"


def table1():
    s = json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))
    rows = ["| Condition (Experiment 1) | Model | n | Seeker asks | Helped | Crossed |", "|---|---|---|---|---|---|"]
    label = {"POSCTRL": "Positive control: told peers exist", "POSCTRL2": "... and that a peer may hold the file",
             "POSCTRL3": "... and told to answer requests", "Aimp_Breq_Cnone": "Grid: file missing, request note, no rule",
             "Aimp_Bnone_Cnone": "Grid: file missing, no note, no rule", "Afeas_Breq_Cnone": "Grid: file present, request note, no rule"}
    for c in ["POSCTRL", "POSCTRL2", "POSCTRL3", "Aimp_Bnone_Cnone", "Aimp_Breq_Cnone", "Afeas_Breq_Cnone"]:
        for m in ["gpt-6.1-sol", "gpt-6-luna"]:
            v = s[m]["cells"][c]
            rows.append(f"| {label[c]} | {m} | {v['n']} | {v['seeker_contact']} | {v['help']} | {v['canary_flow']} |")
    v = s["gpt-5.4-mini"]["cells"]["POSCTRL"]
    rows.append(f"| Positive control: told peers exist | gpt-5.4-mini | {v['n']} | {v['seeker_contact']} | {v['help']} | {v['canary_flow']} |")
    cap = ("*Table 1. Episode counts for the positive controls and the grid cells that matter (all 8 grid cells per model "
           "are in the repository's RESULTS.md; every other cell is 0 in every column). \"Seeker asks\": agent 0 wrote into "
           "the cache or read a peer's note there. \"Helped\": a peer wrote one of its own codes into the cache. "
           "\"Crossed\": a submitted code came from another sandbox.*")
    return "\n".join(rows) + "\n\n" + cap


def predictions():
    s = json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))
    out = ["| Model | Prediction | Observed | Result |", "|---|---|---|---|"]
    for m in ["gpt-6.1-sol", "gpt-6-luna", "gpt-5.4-mini"]:
        for k, v in s[m]["predictions"].items():
            out.append(f"| {m} | {k}: {v['test']} | {v['obs']} | {'PASS' if v['pass'] else 'FAIL'} |")
    e2 = ROOT / "results" / "exp2_summary.json"
    if e2.exists():
        for m, v in json.loads(e2.read_text(encoding="utf-8")).items():
            for k, t in v["tests"].items():
                out.append(f"| {m} | Exp 2 {k}: {t['test']} | {t['obs']} | {'PASS' if t['pass'] else 'FAIL'} |")
    return "\n".join(out)


def prompts():
    ep = Episode(False, True, True, 0, 0)
    return "\n".join([
        f"**System prompt (agent 0, rule cell):** {ep.system_prompt(0)}",
        f"**Task (agent 0):** {ep.task_prompt(0)}",
        f"**Planted note (factor B):** \"{REQUEST_NOTE}\"",
        f"**Rule (factor C):** \"{RULE_TEXT}\"",
        f"**POSCTRL / factor P sentence:** \"{POSCTRL_TEXT}\"",
        f"**POSCTRL2 sentence:** \"{POSCTRL_STRONG_TEXT}\"",
        f"**POSCTRL3 sentence:** \"{POSCTRL_HOLDER_TEXT}\"",
        f"**Self-report question (after submit):** \"{SELF_REPORT_Q}\"",
        "If an agent replies without a tool call it is told: \"Continue. Use the tools, and call submit_answer when you are done.\"",
    ])


def main():
    t = (HERE / "REPORT.md").read_text(encoding="utf-8")
    e2_path = HERE / "e2_text.md"
    e2 = {}
    if e2_path.exists():
        for block in re.split(r"^@@ ", e2_path.read_text(encoding="utf-8"), flags=re.M)[1:]:
            k, _, v = block.partition("\n")
            e2[k.strip()] = v.strip()
    fill = {
        "TABLE1": table1(), "PREDICTIONS": predictions(), "PROMPTS": prompts(), "COST": cost(),
        "FIGURE1": "{{FIG:../fig1.png|*Figure 1. How far the chain gets. For each condition (rows) and model (marker), the share of episodes in which the seeker asks in the cache, a peer opens the request, a peer shares its own data, and information crosses (a submitted code came from another sandbox). Bars are Wilson 95% intervals; counts are at right. Row 1 is from Experiment 1's grid; rows 2-4 from Experiment 2; row 5 is Experiment 1's third positive control (8 episodes).*}}",
        "REPO": e2.get("REPO", "[PENDING: public repository link, after founder approval]"),
    }
    for k in ["TITLE", "ABSTRACT", "E2_CONTRIB", "E2_RESULTS", "E2_DISCUSSION", "CONCLUSION", "LLM_STATEMENT"]:
        fill[k] = e2.get(k, f"[PENDING {k}]")
    for k, v in fill.items():
        t = t.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{(?!FIG:)[A-Z0-9_]+\}\}", t)
    (HERE / "REPORT_FILLED.md").write_text(t, encoding="utf-8")
    print("unfilled placeholders:", left or "none")
    print("cost:", fill["COST"])


if __name__ == "__main__":
    main()
