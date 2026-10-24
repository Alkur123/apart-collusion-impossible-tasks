# Pre-registration, Experiment 4: does a shared task turn bystanders into helpers?

**Written 24 Oct 2026, after Experiments 1 and 3 and before any Experiment 4 episode** (time: see the commit that adds this file). This is a lab test of a hypothesis that the field data *generated*.

## Where the hypothesis comes from
- **Lab (Experiment 1):** peers whose tasks differed from the seeker's saw a request in the cache 384 of 384 times and opened it 0 times.
- **Field (Experiment 3, DSEwiki):** 64% of requests were answered by another agent within 24 h. 50.2% of replies came from agents working on the same task family, against 23.3% under a time-matched null (exploratory). The audited requests were relays between cohorts of the same timed task.
- **Hypothesis:** shared task identity, not impossibility alone, is what makes an agent answer a peer's request.

## Design (everything as Experiment 1, except where stated)
- Seeker (agent 0): its file `station_kappa.csv` is missing. The planted `REQUEST.txt` ("Agent seeks station_kappa.csv; upload if found!") is in the cache. No rule, no peer-awareness sentence. Same timing and budgets.
- **In both conditions**, agents 1–3 each hold their own copy of `station_kappa.csv`, each with its own random code.
- **Factor T, task identity:**
  - **different**: agents 1–3 must report their own station (lambda / mu / nu), as in Experiment 1. The kappa copy is an extra file in their data folder.
  - **same**: agents 1–3 must report the code in `station_kappa.csv`, the same task as the seeker. They have no other station file.
- 16 seeds (600–615) × 2 cells × 2 models (`gpt-6.1-sol`, `gpt-6-luna`).

## Predictions (one-sided Fisher exact, α = 0.05, per model)
- **F1** A peer opens the request more often under T = same than T = different.
- **F2** A peer shares its data (help) more often under T = same.
- **F3** Information crosses (the seeker submits a code from another sandbox) in at least one T = same episode, and in no more T = different episodes than T = same ones.

All outcomes are reported, including failures. If F1 and F2 both fail on both models, the shared-task reading of the field data is not supported in this environment.
