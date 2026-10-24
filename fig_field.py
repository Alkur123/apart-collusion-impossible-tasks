"""Figure 2: the field record (Experiment 3). Reads results/field_*.json, writes fig2.png."""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    f = json.loads((HERE / "results" / "field_summary.json").read_text(encoding="utf-8"))
    sh = json.loads((HERE / "results" / "field_shared_task.json").read_text(encoding="utf-8"))
    ink, ink2, grid, blue, gray = "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6", "#b9b8b3"
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.5, 3.0), gridspec_kw={"width_ratios": [1.15, 1]})
    # (a) answer rate by whether the name ever asked, per activity stratum
    strata = [k for k in f["H1"]["strata"] if k != "1"]
    for i, st in enumerate(strata):
        (x, y), (z, w) = f["H1"]["strata"][st]
        r1, r0 = x / (x + y), z / (z + w)
        a.barh(i + 0.18, r1, height=0.34, color=blue, zorder=2)
        a.barh(i - 0.18, r0, height=0.34, color=gray, zorder=2)
        a.text(r1 + 0.015, i + 0.18, f"{100 * r1:.0f}%  ({x}/{x + y})", va="center", fontsize=7.5, color=ink2)
        a.text(r0 + 0.015, i - 0.18, f"{100 * r0:.0f}%  ({z}/{z + w})", va="center", fontsize=7.5, color=ink2)
    a.set_yticks(range(len(strata)))
    a.set_yticklabels([f"{s} edits" for s in strata], fontsize=8, color=ink)
    a.set_xlim(0, 1.18)
    a.set_xticks([0, 0.5, 1]); a.set_xticklabels(["0%", "50%", "100%"], fontsize=7.5, color=ink2)
    a.set_title("(a) Share of names that answer someone else's request", fontsize=9, color=ink, loc="left")
    a.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=blue), plt.Rectangle((0, 0), 1, 1, color=gray)],
             labels=["name also asked for help", "name never asked"], fontsize=7.5, frameon=False, loc="lower right")
    lo, hi = f["H1"]["cmh_OR_95CI"]
    a.text(0, -0.85, f"Mantel–Haenszel odds ratio {f['H1']['cmh_pooled_OR']:.2f} (95% CI {lo:.2f}–{hi:.2f})", fontsize=7.5, color=ink2)
    # (b) same-task share of replies vs nulls
    vals = [("Observed", sh["observed_frac"], blue), ("Null: same-day shuffle", sh["time_matched_null_mean_frac"], gray),
            ("Null: full shuffle", sh["null_mean_frac"], gray)]
    for i, (lab, v, c) in enumerate(vals[::-1]):
        b.barh(i, v, height=0.55, color=c, zorder=2)
        b.text(v + 0.015, i, f"{100 * v:.1f}%", va="center", fontsize=8, color=ink2)
    b.set_yticks(range(len(vals))); b.set_yticklabels([v[0] for v in vals[::-1]], fontsize=8, color=ink)
    b.set_xlim(0, 0.75); b.set_xticks([0, 0.25, 0.5]); b.set_xticklabels(["0%", "25%", "50%"], fontsize=7.5, color=ink2)
    b.set_title(f"(b) Replies whose author works on the same task family (n = {sh['replies_with_family']:,})", fontsize=9, color=ink, loc="left")
    for ax in (a, b):
        ax.grid(axis="x", color=grid, lw=0.8, zorder=0)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(grid); ax.tick_params(length=0)
    fig.tight_layout()
    fig.savefig(HERE / "fig2.png", dpi=220, facecolor="white", bbox_inches="tight")


if __name__ == "__main__":
    main()
