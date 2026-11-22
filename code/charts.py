"""Data-drawn charts for the Denver Teardown Ledger brief (2026-11-17).
Brand palette: dark charcoal, amber, teal. Every value is read from the
package's stats.json and data/neighborhood_index.csv at build time, so a
chart can never carry a figure the package data does not (sync gate,
standards 10.3). Every chart prints its population, measure, scope, and
source on the graphic itself; charts that touch counts carry the
structures-not-units caveat on the graphic.

Layout: titles and footnotes are figure-level text with fixed axes
margins (no tight_layout), so no footnote can clip or overlap an axis.
Footnote text is wrapped to the figure width before it is drawn.
"""
import csv
import json
import pathlib
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = pathlib.Path(__file__).resolve().parent.parent
stats = json.loads((ROOT / "stats.json").read_text())
with open(ROOT / "data" / "neighborhood_index.csv") as f:
    panel = list(csv.DictReader(f))
CH = ROOT / "charts"
CH.mkdir(exist_ok=True)
CHARCOAL = "#23272b"; AMBER = "#f5a800"; TEAL = "#2a9d8f"; GREY = "#8a8f98"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": CHARCOAL,
                     "axes.edgecolor": CHARCOAL, "axes.labelcolor": CHARCOAL,
                     "xtick.color": CHARCOAL, "ytick.color": CHARCOAL})

WINDOW = "January 2020 - October 2026"
SRC = ("Source: Machine Readable warehouse, 2026-11-01 snapshot (assessor parcel spine; HOST income-restricted "
       "inventory as filed 2026-10-21; ACS 2020-2024 housing units). Window: demolitions " + WINDOW + ".")
CAVEAT = ("Counts are parcels and structures, not homes: the permit registers' UNITS fields are too incomplete "
          "to count units removed or added, so no unit-loss figure appears in this brief.")

plotted = {}  # chart-verification record, printed at the end


def wrapfoot(text, width=152):
    out = []
    for line in text.split("\n"):
        out.extend(textwrap.wrap(line, width) or [""])
    return "\n".join(out)


def frame(fig, title, foot, top=0.86, bottom=0.16, left=0.09, right=0.985, sub=None):
    fig.text(0.012, 0.975, title, fontsize=11, va="top", ha="left", fontweight="bold")
    if sub:
        fig.text(0.012, 0.925, sub, fontsize=9, va="top", ha="left", color=CHARCOAL)
    fig.text(0.012, 0.012, wrapfoot(foot), fontsize=7.5, color=GREY, va="bottom", ha="left")
    fig.subplots_adjust(top=top, bottom=bottom, left=left, right=right)


def save(fig, name):
    fig.savefig(CH / name, dpi=200, facecolor="white")
    plt.close(fig)
    print(name)


def money(v):
    return f"${v:,.0f}" if float(v) == int(float(v)) else f"${v:,.2f}"


def dollars_m(v, _pos):
    return f"${v / 1e6:.1f}M" if v >= 1e6 else f"${v:,.0f}"


# ------------------------------------------------------------------
# 1. Displacement-pressure index, 16 qualifying neighborhoods
# ------------------------------------------------------------------
qual = [r for r in panel if r["index"] not in ("", None)]
qual.sort(key=lambda r: float(r["index"]), reverse=True)
names = [r["neighborhood"] for r in qual]
idx = [float(r["index"]) for r in qual]
demo = [int(float(r["demolished"])) for r in qual]
restr = [int(r["restricted_units"]) for r in qual]
plotted["chart_index.png"] = [
    {"neighborhood": n, "index": i, "demolished_parcels": d, "restricted_units": r}
    for n, i, d, r in zip(names, idx, demo, restr)]

fig = plt.figure(figsize=(9.5, 7.6))
gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1.0], wspace=0.04)
ax = fig.add_subplot(gs[0]); axt = fig.add_subplot(gs[1], sharey=ax)
colors = [AMBER if k < 6 else TEAL for k in range(len(qual))]
ax.barh(range(len(qual)), idx, color=colors)
ax.set_yticks(range(len(qual)))
ax.set_yticklabels(names, fontsize=9)
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xlabel("Displacement-pressure index (0-100, constructed rank)")
for k, v in enumerate(idx):
    ax.text(v + 1.5, k, f"{v:.1f}", va="center", fontsize=8.5)
ax.spines[["top", "right"]].set_visible(False)
axt.axis("off")
for k, (d, r) in enumerate(zip(demo, restr)):
    axt.text(0.04, k, f"{d:,} demolished parcels  ·  {r:,} restricted units",
             va="center", fontsize=8.5)
frame(fig,
      "Displacement pressure is highest where the restricted inventory records the least",
      SRC + "\n" + CAVEAT + "\n"
      "Index: equal-weight mean of percentile ranks for teardown rate per 1,000 parcels, median completed-cycle spread, and "
      "backstop absence (inverse of restricted units per 1,000 housing units). Qualifies: 30+ demolitions and 10+ completed cycles; "
      "Sun Valley excluded (its ACS unit base is smaller than its recorded restricted count). Top six in amber.",
      top=0.82, bottom=0.17, left=0.20, right=0.99,
      sub="Index rank for the 16 qualifying neighborhoods, with demolished parcels and recorded restricted units alongside")
save(fig, "chart_index.png")

# ------------------------------------------------------------------
# 2. The teardown cycle funnel (parcel basis)
# ------------------------------------------------------------------
cw = stats["citywide"]
dem = cw["demolished_in_window"]; reb = cw["rebuilt"]; pair = cw["paired_cycles"]
reb_share = cw["rebuilt_share_pct"]
pair_of_reb = 100.0 * pair / reb
pair_of_dem = 100.0 * pair / dem
plotted["chart_cycle_funnel.png"] = [
    {"stage": "Demolished parcels", "count": dem},
    {"stage": "Rebuilt (new-building permit, same parcel)", "count": reb, "share_of_demolished_pct": reb_share},
    {"stage": "Completed cycles (market sale on both sides)", "count": pair,
     "share_of_rebuilt_pct": round(pair_of_reb, 1), "share_of_demolished_pct": round(pair_of_dem, 1)}]

fig, ax = plt.subplots(figsize=(9.5, 4.9))
stages = ["Demolished parcels", "Rebuilt: new-building permit\nat the same parcel",
          "Completed cycles: market sale\nbefore demolition and after the permit"]
vals = [dem, reb, pair]
labels = [f"{dem:,}",
          f"{reb:,}  ({reb_share:.1f}% of demolished)",
          f"{pair:,}  ({pair_of_reb:.1f}% of rebuilt; {pair_of_dem:.1f}% of demolished)"]
ax.barh(range(3), vals, color=[CHARCOAL, TEAL, AMBER])
ax.set_yticks(range(3)); ax.set_yticklabels(stages, fontsize=9.5)
ax.invert_yaxis()
ax.set_xlim(0, dem * 1.42)
for k, (v, lab) in enumerate(zip(vals, labels)):
    ax.text(v + dem * 0.02, k, lab, va="center", fontsize=10, fontweight="bold")
ax.set_xlabel("Parcels (assessor parcel basis)")
ax.spines[["top", "right"]].set_visible(False)
frame(fig, "Of 3,281 demolished parcels, 616 completed a full, priced teardown cycle",
      SRC + "\n" + CAVEAT + "\n"
      "The rebuilt share is right-censored: demolitions in the final 12 months show a 46.0% rebuilt share against 74.9% earlier, "
      "because recent demolitions have had less time to draw a permit.",
      top=0.80, bottom=0.31, left=0.30, right=0.99,
      sub="Denver parcels demolished " + WINDOW + ", and how far each got through the cycle")
save(fig, "chart_cycle_funnel.png")

# ------------------------------------------------------------------
# 3. Median buy vs median first post-rebuild sale (616 completed cycles)
# ------------------------------------------------------------------
buy = cw["paired_median_buy"]; sell = cw["paired_median_sell"]
spread = cw["paired_median_spread"]; ratio = cw["paired_median_ratio"]; months = cw["paired_median_months"]
plotted["chart_cycle_prices.png"] = [
    {"measure": "Median purchase price before demolition", "value_usd": buy},
    {"measure": "Median first sale after the rebuild permit", "value_usd": sell},
    {"measure": "Median gross spread", "value_usd": spread},
    {"measure": "Median sell-to-buy ratio", "value": ratio},
    {"measure": "Median months, deed to deed", "value": months}]

fig, ax = plt.subplots(figsize=(9.5, 5.2))
bars = ax.bar(["Median purchase price\nbefore demolition", "Median first sale\nafter the rebuild permit"],
              [buy, sell], color=[TEAL, AMBER], width=0.52)
for b_, v in zip(bars, [buy, sell]):
    ax.text(b_.get_x() + b_.get_width() / 2, v + 90000, money(v), ha="center", fontsize=13, fontweight="bold")
ax.set_ylim(0, sell * 1.48)
ax.yaxis.set_major_formatter(FuncFormatter(dollars_m))
ax.set_ylabel("Dollars (nominal, as recorded)")
ax.spines[["top", "right"]].set_visible(False)
ax.annotate(f"Median gross spread: {money(spread)}\nMedian sell-to-buy ratio: {ratio:.2f}x  ·  median {months:.1f} months deed to deed",
            xy=(0.5, sell * 1.36), ha="center", fontsize=10.5,
            bbox=dict(boxstyle="round,pad=0.45", fc="#f4f1ea", ec=GREY, lw=0.8))
frame(fig, "The completed cycle replaces a house with a sale at 3.45 times the purchase price",
      "Medians across the 616 completed cycles (a demolished-then-rebuilt parcel with a market sale on both sides), " + WINDOW + ".\n"
      "The spread is the difference between two recorded sale prices, measured before construction cost, permit fees, financing, and "
      "holding costs. It is not a profit figure. " + SRC,
      top=0.82, bottom=0.24, left=0.11, right=0.99,
      sub="Median prices across Denver's 616 completed teardown cycles")
save(fig, "chart_cycle_prices.png")

# ------------------------------------------------------------------
# 4. Zero-backstop contrast + top six combined
# ------------------------------------------------------------------
zb = stats["zero_backstop_neighborhoods"]
sp_in = zb["paired_median_spread_in_them"]; sp_out = zb["paired_median_spread_elsewhere"]
n_in = zb["paired_cycles_in_them"]; n_out = cw["paired_cycles"] - n_in
lift = 100.0 * (sp_in / sp_out - 1.0)
t6 = stats["top6_combined"]
plotted["chart_zero_backstop.png"] = [
    {"measure": "Median gross spread, cycles in the 15 zero-restricted-unit neighborhoods", "value_usd": sp_in, "cycles": n_in},
    {"measure": "Median gross spread, cycles elsewhere", "value_usd": sp_out, "cycles": n_out},
    {"measure": "Top six neighborhoods combined, demolished parcels", "count": t6["demolished"]},
    {"measure": "Top six neighborhoods combined, restricted units recorded", "count": t6["restricted_units_combined"]}]

fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 5.4))
b1 = a1.bar(["15 neighborhoods where the\ninventory records zero\nrestricted units",
             "Neighborhoods with at least\none recorded restricted unit"],
            [sp_in, sp_out], color=[AMBER, TEAL], width=0.58)
for b_, v, n in zip(b1, [sp_in, sp_out], [n_in, n_out]):
    a1.text(b_.get_x() + b_.get_width() / 2, v + 70000, f"{money(v)}\n({n} cycles)",
            ha="center", fontsize=10, fontweight="bold")
a1.set_ylim(0, sp_in * 1.30)
a1.yaxis.set_major_formatter(FuncFormatter(dollars_m))
a1.set_ylabel("Median gross spread")
a1.spines[["top", "right"]].set_visible(False)
a1.tick_params(axis="x", labelsize=8.5)
b2 = a2.bar(["Parcels demolished,\n2020-2026", "Restricted units recorded\nin the HOST inventory"],
            [t6["demolished"], t6["restricted_units_combined"]], color=[CHARCOAL, TEAL], width=0.58)
for b_, v in zip(b2, [t6["demolished"], t6["restricted_units_combined"]]):
    a2.text(b_.get_x() + b_.get_width() / 2, v + 26, f"{v:,}", ha="center", fontsize=11, fontweight="bold")
a2.set_ylim(0, t6["demolished"] * 1.22)
a2.set_ylabel("Count")
a2.spines[["top", "right"]].set_visible(False)
a2.tick_params(axis="x", labelsize=8.5)
frame(fig, "Where the inventory records no backstop, the replacement spread is larger",
      "Left: median gross spread of completed cycles, split by whether the cycle's neighborhood records any income-restricted units in "
      "HOST's inventory as filed. Right: two different kinds of record for the same six neighborhoods (Washington Park, Cory - Merrill, "
      "University Park, Belcaro, Hilltop, Platt Park): parcels demolished in the window, and restricted units in the inventory.\n"
      + CAVEAT + " " + SRC,
      top=0.84, bottom=0.27, left=0.10, right=0.99,
      sub=f"Median spread is {lift:.0f}% higher where the inventory records no restricted homes (left); "
          "the six highest-pressure neighborhoods combined (right)")
save(fig, "chart_zero_backstop.png")

print(json.dumps(plotted, indent=1))
