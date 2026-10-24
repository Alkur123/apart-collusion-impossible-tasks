"""Experiment 3 (field), as pre-registered in PREREGISTRATION_EXP3_FIELD.md (commit 3478105).

  python field_analysis.py <dir with the collusion.wiki export>
Statistics only: no agent-written text is written anywhere. Audit samples are revision ids.
"""
import base64
import gzip
import json
import pathlib
import random
import re
import statistics
import sys
import zlib
from collections import defaultdict
from datetime import datetime

from scipy.stats import fisher_exact
from statsmodels.stats.contingency_tables import StratifiedTable

HERE = pathlib.Path(__file__).resolve().parent
REQ_WORDS = re.compile(r"(?i)\b(need|needs|anyone|please|help|looking for|who has|does anyone|seek|seeks|answer for|share)\b")


def is_request(text):
    return "?" in text and bool(REQ_WORDS.search(text))


def decode(r):
    b, enc = r.get("body"), (r.get("body_encoding") or "").lower()
    if b is None:
        return ""
    if isinstance(b, str) and enc in ("", "utf-8", "utf8", "ascii", "latin1", "text", "plain"):
        return b  # the export stores text; body_encoding names its character set
    raw = base64.b64decode(b)
    if "zlib" in enc or "deflate" in enc:
        raw = zlib.decompress(raw)
    elif "gzip" in enc:
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", "replace")


def ts(r):
    for k in ("time", "write_date", "success_time", "request_time"):
        v = r.get(k)
        if v:
            try:
                return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
            except ValueError:
                try:
                    return float(v)
                except ValueError:
                    pass
    return None


def stratum(n):
    return "1" if n == 1 else "2-3" if n <= 3 else "4-9" if n <= 9 else "10+"


def main(d):
    d = pathlib.Path(d)
    revs = [json.loads(l) for l in gzip.open(d / "revisions.jsonl.gz", "rt", encoding="utf-8")]
    labels = [json.loads(l) for l in gzip.open(d / "labels.jsonl.gz", "rt", encoding="utf-8")]
    human = {l["label"] for l in labels if l.get("is_human_handle")}
    encs = defaultdict(int)
    for r in revs:
        encs[r.get("body_encoding")] += 1
    by_page = defaultdict(list)
    for r in revs:
        by_page[r["page_id"]].append(r)
    info = {"n_revisions": len(revs), "n_label_rows": len(labels), "n_human_handles_excluded": len(human),
            "body_encodings": dict(encs), "n_pages": len(by_page)}

    # Added text = lines not present in the previous revision of the same page.
    recs = []
    for pid, rs in by_page.items():
        rs.sort(key=lambda r: (r.get("seq") if r.get("seq") is not None else 0, ts(r) or 0))
        prev = set()
        for r in rs:
            body = decode(r)
            lines = body.splitlines()
            added = "\n".join(l for l in lines if l not in prev)
            prev = set(lines)
            lab = r.get("label")
            recs.append({"rev": r["rev_id"], "page": pid, "label": lab, "t": ts(r),
                         "req": is_request(added), "has_label": bool(lab) and lab not in human})
    agent = [x for x in recs if x["has_label"]]
    info["n_agent_revisions"] = len(agent)
    info["n_unlabelled_or_human_revisions"] = len(recs) - len(agent)

    # REPLY: a revision by X on page P after an earlier REQUEST on P by another name Y, not itself a request.
    pages = defaultdict(list)
    for x in agent:
        pages[x["page"]].append(x)
    for p, xs in pages.items():
        xs.sort(key=lambda x: x["t"] or 0)
        req_by = []
        for x in xs:
            x["reply"] = (not x["req"]) and any(y != x["label"] for y in req_by)
            if x["req"]:
                req_by.append(x["label"])
    names = defaultdict(lambda: {"n": 0, "req": False, "reply": False, "first_req": None, "first_reply": None})
    for x in agent:
        s = names[x["label"]]
        s["n"] += 1
        if x["req"]:
            s["req"] = True
            s["first_req"] = min(filter(None, [s["first_req"], x["t"]])) if x["t"] else s["first_req"]
        if x.get("reply"):
            s["reply"] = True
            s["first_reply"] = min(filter(None, [s["first_reply"], x["t"]])) if x["t"] else s["first_reply"]

    # H1
    a = sum(1 for s in names.values() if s["req"] and s["reply"])
    b = sum(1 for s in names.values() if s["req"] and not s["reply"])
    c = sum(1 for s in names.values() if not s["req"] and s["reply"])
    e = sum(1 for s in names.values() if not s["req"] and not s["reply"])
    orr, p = fisher_exact([[a, b], [c, e]], alternative="greater")
    tabs, strata_out = [], {}
    for st in ["1", "2-3", "4-9", "10+"]:
        ss = [s for s in names.values() if stratum(s["n"]) == st]
        t = [[sum(1 for s in ss if s["req"] and s["reply"]), sum(1 for s in ss if s["req"] and not s["reply"])],
             [sum(1 for s in ss if not s["req"] and s["reply"]), sum(1 for s in ss if not s["req"] and not s["reply"])]]
        strata_out[st] = t
        if min(sum(t[0]), sum(t[1]), t[0][0] + t[1][0], t[0][1] + t[1][1]) > 0:
            tabs.append(t)
    cmh = StratifiedTable(tabs) if tabs else None
    h1 = {"names": len(names), "table [[req&reply, req only],[reply only, neither]]": [[a, b], [c, e]],
          "fisher_OR": orr, "fisher_p_one_sided": p, "strata": strata_out}
    if cmh:
        test = cmh.test_null_odds(correction=True)
        lo, hi = cmh.oddsratio_pooled_confint()
        h1 |= {"cmh_pooled_OR": cmh.oddsratio_pooled, "cmh_OR_95CI": [lo, hi], "cmh_statistic": test.statistic,
               "cmh_p_two_sided": test.pvalue, "strata_used": len(tabs)}
        h1["supported"] = bool(test.pvalue < 0.05 and cmh.oddsratio_pooled > 1)
    # H2
    reqs = [x for x in agent if x["req"]]
    answered = 0
    for x in reqs:
        later = [y for y in pages[x["page"]] if y["label"] != x["label"] and not y["req"]
                 and y["t"] and x["t"] and 0 < y["t"] - x["t"] <= 86400]
        answered += bool(later)
    h2 = {"request_revisions": len(reqs), "answered_by_other_within_24h": answered,
          "fraction": answered / len(reqs) if reqs else None}
    # H3
    lags = [(s["first_reply"] - s["first_req"]) / 3600 for s in names.values()
            if s["reply"] and s["first_req"] and s["first_reply"]]
    h3 = {"responders_who_also_asked": len(lags),
          "asked_before_answering": sum(1 for l in lags if l > 0),
          "median_hours_first_request_to_first_reply": statistics.median(lags) if lags else None}
    # audit sample (ids only)
    rng = random.Random(0)
    audit = {"matched_request_rev_ids": [x["rev"] for x in rng.sample(reqs, min(20, len(reqs)))],
             "unmatched_rev_ids": [x["rev"] for x in rng.sample([x for x in agent if not x["req"]], 20)]}
    out = {"info": info, "H1": h1, "H2": h2, "H3": h3, "audit": audit}
    (HERE / "results" / "field_summary.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main(sys.argv[1])
