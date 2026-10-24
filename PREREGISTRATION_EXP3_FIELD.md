# Pre-registration, Experiment 3 (field): who answers requests on a real agent message board?

**Written 24 Oct 2026, before the data was downloaded or opened** (time: see the commit that adds this file). It replaces the API-funded Experiment 2 runs, which stopped when the API credit ran out (no Experiment 2 episode completed). Experiment 2's pre-registration stays on file as an unrun design.

## Data
The public export of self-identified OpenAI agents' edits to DSEwiki and related wikis, published by Von Arx, Byrd, Kitts and Larsen (4 Sep 2026) at https://collusion.wiki/explorer/download. The authors invite analyses ("We encourage others to take a look and write up their own analyses of this data"). Files used: `revisions.jsonl.gz` (one edit each, full saved text), `labels.jsonl.gz` (one self-assigned name each, with pages edited), `events.jsonl.gz`, `pages.jsonl.gz` and `manifest.json.gz`. We use names, pages, timestamps and text only. We never use the redacted IP fields and we make no attempt to identify anyone. We publish statistics only, never agent-written text, because some posts describe sandbox-evasion techniques.

## Units (frozen)
- **Added text** of a revision: the lines of the saved text that are not present in the previous revision of the same page. For the first revision of a page, all of its lines.
- **REQUEST revision:** the added text contains `?` **and** matches `(?i)\b(need|needs|anyone|please|help|looking for|who has|does anyone|seek|seeks|answer for|share)\b`.
- **REPLY revision:** a revision by name X on page P, after an earlier REQUEST revision on P by a different name Y, whose added text is not itself a REQUEST.
- **Requester:** a name with at least one REQUEST revision. **Responder:** a name with at least one REPLY revision.
- **Activity stratum:** the name's total revision count, binned 1 / 2–3 / 4–9 / ≥ 10.

## Hypotheses and tests
- **H1 (stuck helpers), primary.** Names that ask are more likely to answer others. One-sided Fisher exact test on Requester × Responder, plus a Cochran–Mantel–Haenszel test across activity strata, because a name with more edits has more chances to do both. **H1 is supported only if the CMH test is significant (α = 0.05) and the common odds ratio is above 1.** If only the unstratified test is significant, we report H1 as "explained by activity volume".
- **H2 (descriptive, contrast with the lab).** The fraction of REQUEST revisions followed by a REPLY from a different name on the same page within 24 h. The lab analogue is 0 of 384 peer-episodes opening a request.
- **H3 (descriptive).** Among responders, the median time from their own first REQUEST to their first REPLY: do agents ask before they answer?

## Known weaknesses, stated before looking
- Names are self-assigned. One agent can use several, and several runs can share one.
- The lexicon will misclassify some posts. We report the counts it produces, plus a hand-checkable sample of **20 matched and 20 unmatched revisions, by revision ID only**, so that anyone with the public data can audit them.
- "Asked" is a proxy for "stuck". We cannot see tasks or chain of thought.
- This is observational. It tests an association the lab result predicts, not a cause.
