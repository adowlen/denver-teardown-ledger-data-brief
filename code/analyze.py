#!/usr/bin/env python3
"""Meta-analysis: Denver - The Teardown Ledger (DRAFT, not published).

Joins four published Machine Readable layers on the parcel spine:
  - assessor sales keystone (2026-10-16 brief): market sales, teardown
    lifecycle (demolition -> new-building permit -> paired buy/sell)
  - permits x demolitions (2026-10-15 brief): the permit-register basis
  - HOST Affordable Housing Inventory (2026-10-21 brief): income-
    restricted units and projects by statistical neighborhood
  - neighborhood sales panel (2026-10-16 brief): sub-$500K share change

Definitions replicate code/analyze.py of the sales keystone package
EXACTLY for the lifecycle. SNAPSHOT NOTE: the October briefs ran on the
warehouse's 2026-10-15 snapshot; the warehouse re-snapshotted the same
services on 2026-11-01 (stack manifest: sales snapshot_date 2026-11-01,
service last edit 2026-10-29), and this package computes on the
2026-11-01 snapshot. The lifecycle controls are therefore run as a
RECONCILIATION against the published figures, with deltas recorded,
not as equality asserts: deeds and permits recorded between the two
snapshots legitimately move the counts by small amounts.

Market sale = INSTRUMENT in (WD, SW) and SALE_PRICE > 0 (the cleaned
layer's is_market_sale flag). Window: first demolition date from
2020-01-01 to 2026-10-12, the sales package's WIN0/WIN1 (kept identical
so this analysis covers the same window as the briefs it joins). Sales
are used through the 2026-11-01 snapshot date. Prices are nominal
dollars as recorded; prices are never summed across parcels
(multi-parcel transactions repeat one price).

Run: ~/workspace/tools/venv-data/bin/python code/analyze.py
Writes: stats.json, data/neighborhood_index.csv, data/paired_cycles.csv,
data/audit_output.txt (Section 10 pre-flight evidence).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

STACK = Path("/home/hatch/workspace/goals/daily-civic-data-brief/hidden_files/stack/denver")
HF = Path("/home/hatch/workspace/goals/daily-civic-data-brief/hidden_files")
PKG = Path(__file__).resolve().parent.parent
WIN0, WIN1 = pd.Timestamp("2020-01-01"), pd.Timestamp("2026-10-12")
SNAPSHOT_DATE = pd.Timestamp("2026-11-01")  # warehouse re-snapshot (manifest)

audit = []


def log(msg):
    audit.append(str(msg))
    print(msg)


# ---------------------------------------------------------------- load
sales = pd.read_parquet(STACK / "layers/sales_clean.parquet")
spine = pd.read_parquet(STACK / "joins/parcel_spine_v6.parquet")
permits = pd.read_parquet(STACK / "layers/permits_clean.parquet")
demos = pd.read_parquet(STACK / "layers/demolitions_clean.parquet")
aff = pd.read_csv(HF / "denver-affordable-housing-brief-2026-10-21/data/neighborhood_panel_affordable.csv")
nbsales = pd.read_csv(HF / "sales-keystone-brief-2026-10-16/data/neighborhood_sales.csv")

# ------------------------------------------------- Section 10 pre-flight
log("== Section 10.1 pre-flight audit ==")
# 10.1.1 sentinel scan: SALE_PRICE 0/null is "no stated consideration",
# never a price. The market-sale flag must exclude all of them.
zero_or_null = sales["SALE_PRICE"].isna() | (sales["SALE_PRICE"] <= 0)
assert not sales.loc[zero_or_null, "is_market_sale"].any(), "market flag leaks zero/null prices"
log(f"sales rows total={len(sales)}; zero/null/nonpositive price rows={int(zero_or_null.sum())}; "
    f"market-sale rows among them=0 (asserted)")
# 10.1.4 categorical exhaustiveness before any filter on INSTRUMENT
log("INSTRUMENT counter (full sales table): " +
    json.dumps({str(k): int(v) for k, v in sales["INSTRUMENT"].value_counts(dropna=False).items()}))
log("D_CLASS_N counter (top 12): " +
    json.dumps({str(k): int(v) for k, v in sales["D_CLASS_N"].value_counts(dropna=False).head(12).items()}))
# 10.1.2 polarity sample: 3 rows inside / 3 outside the market filter
inside = sales[sales["is_market_sale"]].head(3)[["INSTRUMENT", "SALE_PRICE", "SALE_YEAR"]]
outside = sales[(sales["INSTRUMENT"].isin(["QC", "PR", "DC"]))].head(3)[["INSTRUMENT", "SALE_PRICE", "SALE_YEAR"]]
log("polarity sample INSIDE market filter:\n" + inside.to_string(index=False))
log("polarity sample OUTSIDE (QC/PR/DC):\n" + outside.to_string(index=False))

# --------------------------------------- replicate sales-package population
mkt = sales[sales["is_market_sale"]].copy()
mkt["sale_date"] = pd.to_datetime(mkt["sale_date"])
mkt["tx_size"] = mkt.groupby("RECEPTION_NUM")["PARID"].transform("size")
m_all = mkt[mkt["SALE_YEAR"] >= 2020].copy()
N_FUTURE_DATED = int((m_all["sale_date"] > SNAPSHOT_DATE).sum())
mkt = mkt[mkt["sale_date"] <= SNAPSHOT_DATE].copy()
log(f"population on 2026-11-01 snapshot: market sales 2020+ = {len(m_all)} "
    f"(published 2026-10-15 snapshot: 105,585; delta {len(m_all) - 105585:+d}); "
    f"rows dated after the snapshot and excluded from dated figures = {N_FUTURE_DATED}")
assert len(m_all) > 105585  # refreshed snapshot must be a superset in count

sp = spine.copy()
for c in ["first_demolition_date", "first_new_building_permit_date"]:
    sp[c] = pd.to_datetime(sp[c])
sales_by_parcel = {k: g.sort_values(["sale_date", "RECEPTION_NUM"], kind="mergesort")
                   for k, g in mkt.groupby("schednum")}

# Boundary-tie rule (deterministic; found by the independent verifier):
# 56 demolished parcels carry more than one market sale on their last
# pre-demolition date (same-day deed clusters: a warranty deed and a
# special warranty deed recorded the same day, occasionally a $10
# nominal deed recorded later against the same sale date). Rule: among
# sales tied on the boundary date, nominal prices (<= $100) never win
# when another tied sale exceeds $100; the winner is then the highest
# RECEPTION_NUM on the buy side (last deed recorded that day) and the
# lowest on the exit side (first deed recorded that day). The verifier
# implements the same rule independently; the counts it moves are
# recorded in verification.md.
TIE_STATS = {"buy_ties": 0, "buy_nominal_excluded": 0, "exit_ties": 0, "exit_nominal_excluded": 0}


def pick_boundary(cands, side):
    """cands: sales on the single boundary date, sorted by RECEPTION_NUM."""
    if len(cands) > 1:
        TIE_STATS[f"{side}_ties"] += 1
        real = cands[cands["SALE_PRICE"] > 100]
        if len(real) and len(real) < len(cands):
            TIE_STATS[f"{side}_nominal_excluded"] += 1
            cands = real
    return cands.iloc[-1] if side == "buy" else cands.iloc[0]


def lifecycle(frame):
    """Verbatim replication of the sales package lifecycle()."""
    d = frame[(frame["first_demolition_date"] >= WIN0) & (frame["first_demolition_date"] <= WIN1)]
    reb = d[d["demolished_then_rebuilt"] == True]  # noqa: E712
    buys, exits, paired = [], [], []
    for _, row in reb.iterrows():
        g = sales_by_parcel.get(row["schednum"])
        if g is None:
            continue
        dd = row["first_demolition_date"]
        pd_ = row["first_new_building_permit_date"]
        pre = g[g["sale_date"] < dd]
        post = g[g["sale_date"] > pd_] if pd.notna(pd_) else g.iloc[0:0]
        b = pick_boundary(pre[pre["sale_date"] == pre["sale_date"].max()], "buy") if len(pre) else None
        e = pick_boundary(post[post["sale_date"] == post["sale_date"].min()], "exit") if len(post) else None
        if b is not None:
            buys.append(b)
        if e is not None:
            exits.append(e)
        if b is not None and e is not None:
            paired.append({"schednum": row["schednum"], "neighborhood": row["neighborhood"],
                           "buy": b["SALE_PRICE"], "sell": e["SALE_PRICE"],
                           "spread": e["SALE_PRICE"] - b["SALE_PRICE"],
                           "ratio": e["SALE_PRICE"] / b["SALE_PRICE"],
                           "months": (e["sale_date"] - b["sale_date"]).days / 30.4375,
                           "buy_date": b["sale_date"], "sell_date": e["sale_date"],
                           "demolition_date": dd, "permit_date": pd_})
    pa = pd.DataFrame(paired)
    out = {"demolished": int(len(d)), "rebuilt": int(len(reb)),
           "paired": int(len(pa))}
    if len(pa):
        out.update({"median_buy": float(pa["buy"].median()),
                    "median_sell": float(pa["sell"].median()),
                    "median_spread": float(pa["spread"].median())})
    return out, pa, d, reb


city, paired_all, demo_all, reb_all = lifecycle(sp)
PUBLISHED = {"citywide": {"demolished": 3297, "rebuilt": 2335, "paired": 611,
                          "median_buy": 650000.0, "median_sell": 2299525.0,
                          "median_spread": 1635000.0},
             "washington_park": {"demolished": 268, "rebuilt": 237, "paired": 85,
                                 "median_spread": 2140000.0}}
log(f"RECONCILIATION citywide (2026-11-01 snapshot): {city}")
log(f"RECONCILIATION citywide (published, 2026-10-15 snapshot): {PUBLISHED['citywide']}")
wp, _, _, _ = lifecycle(sp[sp["neighborhood"] == "Washington Park"])
log(f"RECONCILIATION Washington Park (2026-11-01 snapshot): {wp}")
log(f"RECONCILIATION Washington Park (published): {PUBLISHED['washington_park']}")
# Sanity band: a re-snapshot two weeks later moves counts by recordings,
# not by structure. Anything beyond ~3% would signal a definition break.
for k in ["demolished", "rebuilt", "paired"]:
    delta_pct = abs(city[k] - PUBLISHED["citywide"][k]) / PUBLISHED["citywide"][k] * 100
    assert delta_pct <= 3.0, (k, city[k], PUBLISHED["citywide"][k])
log("RECONCILIATION WITHIN BAND: all lifecycle counts within 3% of the published figures; "
    "deltas are recordings posted between the 2026-10-15 and 2026-11-01 snapshots.")

# --------------------------------------- removed stock (all demolished)
# For every demolished parcel (rebuilt or not): last market sale strictly
# before the demolition date = the observable price of the stock removed.
removed = []
for _, row in demo_all.iterrows():
    g = sales_by_parcel.get(row["schednum"])
    if g is None:
        continue
    pre = g[g["sale_date"] < row["first_demolition_date"]]
    if len(pre):
        b = pick_boundary(pre[pre["sale_date"] == pre["sale_date"].max()], "buy")
        removed.append({"schednum": row["schednum"], "neighborhood": row["neighborhood"],
                        "buy": b["SALE_PRICE"], "buy_date": b["sale_date"],
                        "rebuilt": bool(row["demolished_then_rebuilt"])})
rem = pd.DataFrame(removed)
log(f"demolished parcels with an observable pre-demolition market buy: {len(rem)} of {len(demo_all)}")
log("boundary tie rule stats (lifecycle + removed passes combined): " + json.dumps(TIE_STATS))

# ------------------------------------------------------- UNITS coverage
per = permits.copy(); per["date"] = pd.to_datetime(per["date"])
nbp = per[(per["is_new_building"]) & (per["active"]) & (per["date"] >= WIN0) & (per["date"] <= WIN1)]
dm = demos.copy(); dm["date"] = pd.to_datetime(dm["date"])
wrk = dm[(dm["is_wreck"]) & (dm["active"]) & (dm["date"] >= WIN0) & (dm["date"] <= WIN1)]
def units_stats(frame):
    raw = frame["UNITS"]
    present = raw.notna() & (raw.astype(str).str.strip() != "")
    numeric = pd.to_numeric(raw, errors="coerce")
    return {
        "rows": int(len(frame)),
        "units_present_pct": round(float(present.mean() * 100), 1),
        "units_numeric_pct": round(float(numeric.notna().mean() * 100), 1),
        "units_positive_pct": round(float((numeric > 0).mean() * 100), 1),
        "units_zero_rows": int((numeric == 0).sum()),
    }


units_cov = {"new_building_permits": units_stats(nbp), "demolition_permits": units_stats(wrk)}
log("UNITS coverage: " + json.dumps(units_cov))
log(f"permit-register window counts on the refreshed layers: new-building "
    f"{units_cov['new_building_permits']['rows']} (published 11,585), demolition "
    f"{units_cov['demolition_permits']['rows']} (published 3,837)")

# --------------------------------------------------- neighborhood panel
parcels_by_nb = sp.groupby("neighborhood").size().rename("parcels_total")
demo_ct = demo_all.groupby("neighborhood").size().rename("demolished")
reb_ct = reb_all.groupby("neighborhood").size().rename("rebuilt")
paired_g = paired_all.groupby("neighborhood").agg(
    paired_n=("spread", "size"), paired_median_buy=("buy", "median"),
    paired_median_sell=("sell", "median"), paired_median_spread=("spread", "median"),
    paired_median_ratio=("ratio", "median"),
    paired_buys_le500k=("buy", lambda s: int((s <= 500_000).sum())))
rem_g = rem.groupby("neighborhood").agg(
    removed_with_buy_n=("buy", "size"), removed_median_buy=("buy", "median"),
    removed_le500k_n=("buy", lambda s: int((s <= 500_000).sum())))
panel = pd.concat([parcels_by_nb, demo_ct, reb_ct, paired_g, rem_g], axis=1).fillna(
    {"demolished": 0, "rebuilt": 0, "paired_n": 0, "paired_buys_le500k": 0,
     "removed_with_buy_n": 0, "removed_le500k_n": 0})
panel = panel.reset_index().rename(columns={"index": "neighborhood"})
panel = panel.merge(aff, on="neighborhood", how="left")
panel = panel.merge(nbsales[["neighborhood", "median_sfr", "share_le500_2020_21_pct",
                             "share_le500_2024_25_pct", "share_le500_change_pts"]],
                    on="neighborhood", how="left")
assert panel["restricted_units"].notna().all(), "affordable panel must cover every spine neighborhood"
n_unassigned_parcels = int(sp["neighborhood"].isna().sum())
n_unassigned_demolished = int(demo_all["neighborhood"].isna().sum())
assert panel["parcels_total"].sum() + n_unassigned_parcels == len(sp)
assert panel["demolished"].sum() + n_unassigned_demolished == len(demo_all)
log(f"join coverage: parcels with a statistical neighborhood "
    f"{len(sp) - n_unassigned_parcels} of {len(sp)} "
    f"({(len(sp) - n_unassigned_parcels) / len(sp) * 100:.2f}%); demolished parcels unassigned "
    f"{n_unassigned_demolished} of {len(demo_all)} (counted citywide, in no neighborhood row)")
panel["teardown_rate_per_1000_parcels"] = panel["demolished"] / panel["parcels_total"] * 1000
panel["rebuilt_share_pct"] = np.where(panel["demolished"] > 0,
                                      panel["rebuilt"] / panel["demolished"] * 100, np.nan)
panel["removed_le500k_share_pct"] = np.where(panel["removed_with_buy_n"] > 0,
                                             panel["removed_le500k_n"] / panel["removed_with_buy_n"] * 100, np.nan)
panel["zero_restricted"] = panel["restricted_units"] == 0

# ---------------------------------------------------------------- index
# Qualifying rule (small-numbers standards): at least 30 demolitions in
# the window AND at least 10 completed paired cycles. Sun Valley is
# excluded from ranking for the reason the 2026-10-21 brief printed:
# its ACS housing-unit base (502.9) is smaller than its recorded
# restricted-unit count (1,196), so its backstop rate cannot be ranked.
MIN_DEMO, MIN_PAIRED = 30, 10
q = panel[(panel["demolished"] >= MIN_DEMO) & (panel["paired_n"] >= MIN_PAIRED)
          & (panel["neighborhood"] != "Sun Valley")].copy()


def pct_rank(s):
    return s.rank(method="average", pct=True) * 100


q["score_teardown"] = pct_rank(q["teardown_rate_per_1000_parcels"])
q["score_price"] = pct_rank(q["paired_median_spread"])
q["score_backstop_absence"] = 100 - pct_rank(q["restricted_per_1000_units"])
q["index"] = q[["score_teardown", "score_price", "score_backstop_absence"]].mean(axis=1).round(1)
q = q.sort_values("index", ascending=False)
panel = panel.merge(q[["neighborhood", "score_teardown", "score_price",
                       "score_backstop_absence", "index"]], on="neighborhood", how="left")
panel = panel.sort_values("index", ascending=False, na_position="last")

# ------------------------------------------------------- headline pools
zero_nb = set(panel.loc[panel["zero_restricted"], "neighborhood"])
demo_in_zero = int(panel.loc[panel["zero_restricted"], "demolished"].sum())
paired_zero = paired_all[paired_all["neighborhood"].isin(zero_nb)]
paired_nonzero = paired_all[~paired_all["neighborhood"].isin(zero_nb)]
rem_zero = rem[rem["neighborhood"].isin(zero_nb)]
low_backstop = panel[panel["restricted_per_1000_units"] < 82.0]  # below citywide rate
demo_low_backstop = int(low_backstop["demolished"].sum())
spearman = panel[panel["demolished"] >= MIN_DEMO][
    ["teardown_rate_per_1000_parcels", "restricted_per_1000_units"]].corr(method="spearman").iloc[0, 1]

# ------------------------------------- supplementary checks for the brief
# Censoring (Section 12.3): rebuilt share for final-12-month demolitions.
recent_cut = WIN1 - pd.DateOffset(months=12)
recent_demo = demo_all[demo_all["first_demolition_date"] > recent_cut]
earlier_demo = demo_all[demo_all["first_demolition_date"] <= recent_cut]
censoring = {
    "demolitions_final_12_months": int(len(recent_demo)),
    "rebuilt_share_final_12_months_pct": round(float(recent_demo["demolished_then_rebuilt"].mean() * 100), 1),
    "demolitions_earlier": int(len(earlier_demo)),
    "rebuilt_share_earlier_pct": round(float(earlier_demo["demolished_then_rebuilt"].mean() * 100), 1),
}
# Boundary near misses (Section 12.2) on this snapshot, rebuilt parcels.
bnd = {"on_demolition_date": 0, "on_permit_date": 0, "between_demolition_and_permit": 0}
for _, row in reb_all.iterrows():
    g = sales_by_parcel.get(row["schednum"])
    if g is None:
        continue
    dd, pd_ = row["first_demolition_date"], row["first_new_building_permit_date"]
    bnd["on_demolition_date"] += int((g["sale_date"] == dd).sum())
    if pd.notna(pd_):
        bnd["on_permit_date"] += int((g["sale_date"] == pd_).sum())
        bnd["between_demolition_and_permit"] += int(((g["sale_date"] > dd) & (g["sale_date"] < pd_)).sum())
# Why some high-demolition neighborhoods close few paired cycles: for
# every rebuilt parcel, record which side of the cycle is missing (no
# pre-demolition market buy on the parcel, or no post-permit market sale
# on the parcel). The spine's successor-rebuild flag fires for no
# demolished parcel in this snapshot (checked; recorded, not used).
demo_succ = demo_all["demolished_then_rebuilt_successor"] == True  # noqa: E712
missing_side = {}
for _, row in reb_all.iterrows():
    g = sales_by_parcel.get(row["schednum"])
    has_buy = has_exit = False
    if g is not None:
        has_buy = bool((g["sale_date"] < row["first_demolition_date"]).any())
        pd_ = row["first_new_building_permit_date"]
        has_exit = bool((g["sale_date"] > pd_).any()) if pd.notna(pd_) else False
    key = (row["neighborhood"], has_buy, has_exit)
    missing_side[key] = missing_side.get(key, 0) + 1


def missing_summary(frame_rows):
    tot = {"rebuilt": 0, "with_buy": 0, "with_exit": 0, "paired": 0}
    for (nb, hb, he), n in missing_side.items():
        if frame_rows is None or nb in frame_rows:
            tot["rebuilt"] += n
            tot["with_buy"] += n if hb else 0
            tot["with_exit"] += n if he else 0
            tot["paired"] += n if (hb and he) else 0
    return tot


under10 = panel[(panel["demolished"] >= MIN_DEMO)
                & (panel["paired_n"] < MIN_PAIRED)]["neighborhood"].tolist()
successor = {
    "spine_successor_rebuild_flag_on_demolished_parcels": int(demo_succ.sum()),
    "missing_side_citywide": missing_summary(None),
    "missing_side_under10paired_neighborhoods": missing_summary(set(under10)),
    "under10paired_neighborhoods": under10,
}
top6 = q.head(6)
focus_names = ["Berkeley", "West Colfax", "Overland", "Five Points", "Villa Park",
               "Baker", "Rosedale", "Sunnyside", "Highland", "Cherry Creek"]
focus = panel[panel["neighborhood"].isin(focus_names)][
    ["neighborhood", "demolished", "rebuilt", "paired_n", "removed_with_buy_n",
     "removed_median_buy", "removed_le500k_share_pct", "restricted_units",
     "restricted_per_1000_units"]].round(2).to_dict("records")
log("censoring: " + json.dumps(censoring))
log("boundary: " + json.dumps(bnd))
log("missing side: " + json.dumps(successor["missing_side_citywide"]))
log("missing side (under-10-paired neighborhoods): " +
    json.dumps(successor["missing_side_under10paired_neighborhoods"]))

stats = {
    "meta": {
        "brief": "Denver: The Teardown Ledger (meta-analysis, DRAFT - not published)",
        "built": "2026-11-17",
        "window": "first demolition date 2020-01-01 to 2026-10-12 (the source briefs' window); "
                  "warehouse snapshot 2026-11-01 (the October briefs used the 2026-10-15 snapshot; "
                  "see reconciliation)",
        "bases": "Parcel basis (assessor spine) for demolitions, rebuilds and paired cycles; "
                 "permit-register basis (11,585 new-building permits, 3,837 demolition permits) "
                 "is the 2026-10-15 brief's basis and is NOT mixed into parcel-basis figures.",
        "index_method": "Equal-weight mean of three percentile ranks across qualifying "
                        "neighborhoods (demolitions >= 30 and paired cycles >= 10; Sun Valley "
                        "excluded, see caveats): teardown rate per 1,000 parcels; median paired "
                        "gross spread; backstop absence = 100 - percentile of restricted units "
                        "per 1,000 ACS housing units.",
    },
    "reconciliation_against_2026_10_16_package": {
        "note": "Published figures ran on the warehouse 2026-10-15 snapshot; this package "
                "runs on the 2026-11-01 re-snapshot of the same services. Deltas are "
                "recordings posted between snapshots.",
        "published": PUBLISHED,
        "this_snapshot_citywide": city, "this_snapshot_washington_park": wp},
    "citywide": {
        "parcels_total": int(len(sp)),
        "parcels_without_neighborhood": n_unassigned_parcels,
        "demolished_without_neighborhood": n_unassigned_demolished,
        "demolished_in_window": int(len(demo_all)),
        "rebuilt": int(len(reb_all)),
        "rebuilt_share_pct": round(len(reb_all) / len(demo_all) * 100, 1),
        "paired_cycles": int(len(paired_all)),
        "paired_median_buy": float(paired_all["buy"].median()),
        "paired_median_sell": float(paired_all["sell"].median()),
        "paired_median_spread": float(paired_all["spread"].median()),
        "paired_median_ratio": round(float(paired_all["ratio"].median()), 2),
        "paired_median_months": round(float(paired_all["months"].median()), 1),
        "removed_with_observable_buy": int(len(rem)),
        "removed_median_buy": float(rem["buy"].median()),
        "removed_buys_le500k": int((rem["buy"] <= 500_000).sum()),
        "removed_buys_le500k_share_pct": round(float((rem["buy"] <= 500_000).mean() * 100), 1),
        "share_le500k_citywide_2020": 57.2, "share_le500k_citywide_2025": 47.4,
    },
    "units_coverage": units_cov,
    "zero_backstop_neighborhoods": {
        "neighborhoods": sorted(zero_nb),
        "count": len(zero_nb),
        "demolished_parcels_in_them": demo_in_zero,
        "share_of_all_demolished_pct": round(demo_in_zero / len(demo_all) * 100, 1),
        "paired_cycles_in_them": int(len(paired_zero)),
        "paired_median_spread_in_them": float(paired_zero["spread"].median()) if len(paired_zero) else None,
        "paired_median_spread_elsewhere": float(paired_nonzero["spread"].median()),
        "removed_buys_le500k_in_them": int((rem_zero["buy"] <= 500_000).sum()),
        "removed_with_buy_in_them": int(len(rem_zero)),
    },
    "below_citywide_backstop_rate": {
        "threshold_per_1000": 82.0,
        "neighborhoods": int(len(low_backstop)),
        "demolished_parcels_in_them": demo_low_backstop,
        "share_of_all_demolished_pct": round(demo_low_backstop / len(demo_all) * 100, 1),
    },
    "spearman_teardown_rate_vs_restricted_rate_min30demo": round(float(spearman), 3),
    "censoring": censoring,
    "boundary_sales_section_12_2": bnd,
    "boundary_tie_rule": {
        "rule": "Among market sales tied on a boundary date: nominal prices (<= $100) never "
                "win when another tied sale exceeds $100; then highest RECEPTION_NUM wins on "
                "the buy side, lowest on the exit side.",
        "counts_across_lifecycle_and_removed_passes": TIE_STATS,
        "origin": "Independent verifier found a 2-parcel discrepancy in the at-or-under-$500K "
                  "removed count (422 vs 424) traced to same-day deed clusters; 56 demolished "
                  "parcels have more than one market sale on their last pre-demolition date, "
                  "51 of them at differing prices.",
    },
    "successor_rebuilds": successor,
    "paired_share_in_zero_backstop_pct": round(len(paired_zero) / len(paired_all) * 100, 1),
    "top6_combined": {
        "neighborhoods": top6["neighborhood"].tolist(),
        "demolished": int(top6["demolished"].sum()),
        "paired_cycles": int(top6["paired_n"].sum()),
        "restricted_units_combined": int(top6["restricted_units"].sum()),
        "zero_restricted_among_them": int((top6["restricted_units"] == 0).sum()),
    },
    "focus_neighborhoods_detail": focus,
    "qualifying_neighborhoods_ranked": int(len(q)),
    "neighborhoods_with_30plus_demolitions": int((panel["demolished"] >= MIN_DEMO).sum()),
    "neighborhoods_with_30plus_demolitions_but_under_10_paired": int(
        ((panel["demolished"] >= MIN_DEMO) & (panel["paired_n"] < MIN_PAIRED)).sum()),
    "top10_index": q.head(10)[["neighborhood", "index", "demolished", "teardown_rate_per_1000_parcels",
                               "paired_n", "paired_median_buy", "paired_median_sell",
                               "paired_median_spread", "restricted_units",
                               "restricted_per_1000_units"]].round(2).to_dict("records"),
    "sun_valley": panel[panel["neighborhood"] == "Sun Valley"][
        ["demolished", "rebuilt", "paired_n", "restricted_units", "restricted_per_1000_units"]
    ].to_dict("records"),
}

panel_out = panel[["neighborhood", "parcels_total", "demolished", "teardown_rate_per_1000_parcels",
                   "rebuilt", "rebuilt_share_pct", "paired_n", "paired_median_buy",
                   "paired_median_sell", "paired_median_spread", "paired_median_ratio",
                   "paired_buys_le500k", "removed_with_buy_n", "removed_median_buy",
                   "removed_le500k_n", "removed_le500k_share_pct", "projects", "restricted_units",
                   "restricted_per_1000_units", "acs_units", "median_sfr", "share_le500_2020_21_pct",
                   "share_le500_2024_25_pct", "share_le500_change_pts",
                   "score_teardown", "score_price", "score_backstop_absence", "index"]]
panel_out.to_csv(PKG / "data/neighborhood_index.csv", index=False)
paired_all.assign(buy_date=paired_all["buy_date"].dt.date, sell_date=paired_all["sell_date"].dt.date,
                  demolition_date=paired_all["demolition_date"].dt.date,
                  permit_date=paired_all["permit_date"].dt.date).to_csv(
    PKG / "data/paired_cycles.csv", index=False)
(PKG / "stats.json").write_text(json.dumps(stats, indent=1))
(PKG / "data/audit_output.txt").write_text("\n".join(audit) + "\n")
log("WROTE stats.json, data/neighborhood_index.csv, data/paired_cycles.csv")
print(json.dumps(stats["top10_index"], indent=1))
print("zero backstop:", json.dumps(stats["zero_backstop_neighborhoods"], indent=1))
print("citywide removed:", stats["citywide"]["removed_with_observable_buy"],
      stats["citywide"]["removed_buys_le500k"], stats["citywide"]["removed_buys_le500k_share_pct"])
print("spearman:", stats["spearman_teardown_rate_vs_restricted_rate_min30demo"])
print("sun valley:", stats["sun_valley"])
