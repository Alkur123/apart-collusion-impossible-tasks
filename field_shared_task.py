"""EXPLORATORY (post-hoc, NOT pre-registered): do agents that answer a request share the requester's task family?

Motivated by the hand audit of Experiment 3: requests were relays between cohorts of the same timed task.
For each REPLY (definition as in field_analysis.py), ask whether the replier has edited another page of the
same page_family. Baseline: 2,000 permutations shuffling which name made each reply. Statistics only.
"""
import gzip
import json
import pathlib
import random
import sys
from collections import Counter, defaultdict

import field_analysis as fa

HERE = pathlib.Path(__file__).resolve().parent


def main(d):
    d = pathlib.Path(d)
    revs = [json.loads(l) for l in gzip.open(d / "revisions.jsonl.gz", "rt", encoding="utf-8")]
    pages = {p["page_id"]: p for p in (json.loads(l) for l in gzip.open(d / "pages.jsonl.gz", "rt", encoding="utf-8"))}
    human = {l["label"] for l in (json.loads(x) for x in gzip.open(d / "labels.jsonl.gz", "rt", encoding="utf-8")) if l.get("is_human_handle")}
    fam = {pid: (p.get("page_family") or None) for pid, p in pages.items()}
    by = defaultdict(list)
    for r in revs:
        by[r["page_id"]].append(r)
    recs = []
    for pid, rs in by.items():
        rs.sort(key=lambda r: (r.get("seq") or 0, fa.ts(r) or 0))
        prev = set()
        for r in rs:
            lines = fa.decode(r).splitlines()
            added = "\n".join(l for l in lines if l not in prev)
            prev = set(lines)
            lab = r.get("label")
            if lab and lab not in human:
                recs.append({"page": pid, "label": lab, "t": fa.ts(r) or 0, "req": fa.is_request(added)})
    fams_of = defaultdict(set)
    for x in recs:
        if fam.get(x["page"]):
            fams_of[x["label"]].add(fam[x["page"]])
    replies = []
    per_page = defaultdict(list)
    for x in recs:
        per_page[x["page"]].append(x)
    for p, xs in per_page.items():
        xs.sort(key=lambda x: x["t"])
        req_by = []
        for x in xs:
            if not x["req"] and any(y != x["label"] for y in req_by) and fam.get(p):
                replies.append((p, x["label"], int(x["t"] // 86400)))
            if x["req"]:
                req_by.append(x["label"])

    def share(pairs):
        # replier edited ANOTHER page of the same family (exclude the reply page itself from evidence)
        n = 0
        for p, lab in pairs:
            other = {fam[q] for q in {x["page"] for x in recs if x["label"] == lab and x["page"] != p} if fam.get(q)}
            n += fam[p] in other
        return n

    # precompute other-page families per label for speed
    pages_of = defaultdict(set)
    for x in recs:
        pages_of[x["label"]].add(x["page"])

    def share_fast(pairs):
        n = 0
        for p, lab in pairs:
            n += any(fam.get(q) == fam[p] for q in pages_of[lab] if q != p)
        return n

    pairs = [(p, l) for p, l, _ in replies]
    obs = share_fast(pairs)
    rng = random.Random(0)
    labs = [l for _, l in pairs]
    null = []
    for _ in range(2000):
        rng.shuffle(labs)
        null.append(share_fast(list(zip([p for p, _ in pairs], labs))))
    null.sort()
    # time-matched null: shuffle repliers only among replies made on the same calendar day (UTC)
    by_day = defaultdict(list)
    for k, (_, _, day) in enumerate(replies):
        by_day[day].append(k)
    null_t = []
    for _ in range(2000):
        labs_t = [l for _, l in pairs]
        for ks in by_day.values():
            vals = [labs_t[k] for k in ks]
            rng.shuffle(vals)
            for k, v in zip(ks, vals):
                labs_t[k] = v
        null_t.append(share_fast(list(zip([p for p, _ in pairs], labs_t))))
    null_t.sort()
    out = {"replies_with_family": len(replies), "families": len(set(fam.values()) - {None}),
           "observed_same_family": obs, "observed_frac": obs / len(replies),
           "null_mean_frac": sum(null) / len(null) / len(replies), "null_p95_frac": null[int(0.95 * len(null))] / len(replies),
           "perm_p_one_sided": (1 + sum(v >= obs for v in null)) / (1 + len(null)),
           "time_matched_null_mean_frac": sum(null_t) / len(null_t) / len(replies),
           "time_matched_null_p95_frac": null_t[int(0.95 * len(null_t))] / len(replies),
           "time_matched_perm_p_one_sided": (1 + sum(v >= obs for v in null_t)) / (1 + len(null_t)),
           "n_days": len(by_day),
           "top_families_by_replies": Counter(fam[p] for p, _, _ in replies).most_common(5)}
    (HERE / "results" / "field_shared_task.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
