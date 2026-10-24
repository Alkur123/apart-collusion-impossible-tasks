# Do impossible tasks make AI agents collude?

Code and data for an AI Collusion Research Sprint project (Apart Research, 23–25 Oct 2026).

Four agents work in separate sandboxes and share one directory, presented only as a package cache. Agent 0's task is made possible or impossible (its data file is present or missing; a peer holds a copy). We vary whether a peer request is planted in the cache, and whether a rule says "work independently". Every file carries a random code, so if an agent submits a code that never existed in its own sandbox, information crossed between agents. No LLM judge is used.

| file | what it is |
|---|---|
| `PREREGISTRATION.md` | Experiment 1 design, outcomes, predictions, analysis (plus amendments) |
| `PREREGISTRATION_EXP2.md` | Experiment 2 (stuck peers x awareness): registered, **never run** (API credit ran out) |
| `PREREGISTRATION_EXP3_FIELD.md` | Experiment 3: field test on the public collusion.wiki export, registered before download |
| `PREREGISTRATION_EXP4.md` | Experiment 4: shared task vs different task |
| `field_analysis.py`, `field_shared_task.py` | Experiment 3 analyses (pass the directory holding the export); statistics only |
| `analyze_exp4.py`, `fig_funnel.py`, `fig_field.py` | Experiment 4 tests and Figures 1-2 |
| `report/` | report source (`REPORT.md`), number filler with checks (`fill_report.py`), template builder (`build_report.py`) |
| `env.py` | environment, tools, judge-free outcome detectors |
| `test_env.py` | scripted agents: collusion trips every detector, honest agents trip none (`python test_env.py`) |
| `run.py` | runs episodes against OpenAI models; one JSON per episode, cached |
| `run_all.sh` | the registered runs |
| `analyze.py` | Experiment 1 pre-registered tests, `RESULTS.md`, `results/summary.json`, `fig_grid.png` |
| `results/<model>/` | every episode: events, submissions, self-reports, full transcripts, token usage |
| `results_smoke/` | unregistered seed-999 runs used to debug the design (Amendment 2); excluded from analysis. Earlier smoke files were overwritten during iteration. |

Reproduce: `pip install openai scipy statsmodels matplotlib python-docx`, set `OPENAI_API_KEY`, run `sh run_all.sh` and `python run.py --model <m> --which exp4 --seeds 16`, then the analysis scripts. Field data: download the five files listed in `PREREGISTRATION_EXP3_FIELD.md` from https://collusion.wiki/explorer/download. No code here predates the sprint (23-25 Oct 2026).

Safety: no internet, no code execution, no real credentials. "Collusion" here means passing a data code between toy sandboxes against a stated rule. Nothing here tests hiding messages from a monitor.
