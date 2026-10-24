# Do impossible tasks make AI agents collude?

Code and data for an AI Collusion Research Sprint project (Apart Research, 23–25 Oct 2026).

Four agents work in separate sandboxes and share one directory, presented only as a package cache. Agent 0's task is made possible or impossible (its data file is present or missing; a peer holds a copy). We vary whether a peer request is planted in the cache, and whether a rule says "work independently". Every file carries a random code, so if an agent submits a code that never existed in its own sandbox, information crossed between agents. No LLM judge is used.

| file | what it is |
|---|---|
| `PREREGISTRATION.md` | design, outcomes, predictions, analysis (plus amendments) |
| `env.py` | environment, tools, judge-free outcome detectors |
| `test_env.py` | scripted agents: collusion trips every detector, honest agents trip none (`python test_env.py`) |
| `run.py` | runs episodes against OpenAI models; one JSON per episode, cached |
| `run_all.sh` | the registered runs |
| `analyze.py` | pre-registered tests, `RESULTS.md`, `results/summary.json`, `fig1.png` |
| `results/<model>/` | every episode: events, submissions, self-reports, full transcripts, token usage |
| `results_smoke/` | unregistered seed-999 runs used to debug the design (Amendment 2); excluded from analysis. Earlier smoke files were overwritten during iteration. |

Reproduce: `pip install openai scipy matplotlib`, set `OPENAI_API_KEY`, run `sh run_all.sh`, then `python analyze.py`.

Safety: no internet, no code execution, no real credentials. "Collusion" here means passing a data code between toy sandboxes against a stated rule. Nothing here tests hiding messages from a monitor.
