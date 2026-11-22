#!/usr/bin/env python3
"""Independent verification for the Teardown Ledger meta-analysis.

Separate implementation from code/analyze.py (Section 11 method
diversity): paired cycles are rebuilt with vectorized merges instead of
per-parcel dict iteration; demolition geography is cross-checked on the
permit register (a different basis from the parcel spine); the HOST
inventory is re-summed from the 2026-10-21 package's raw pull.

Run: ~/workspace/tools/venv-data/bin/python code/verify_independent.py
Writes data/verification_ledger.csv and prints the ledger.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

STACK = Path("/home/hatch/workspace/goals/daily-civic-data-brief/hidden_files/stack/denver")
HF = Path("/home/hatch/workspace/goals/daily-civic-data-brief/hidden_files")
PKG = Path(__file__).resolve().parent.parent
WIN0, WIN1 = pd.Timestamp("2020-01-01"), pd.Timestamp("2026-10-12")
SNAP = pd.Timestamp("2026-11-01")
stats = json.loads((PKG / "stats.json").read_text())
ledger = []


def check(name, builder, verifier, tol=0):
    ok = (builder == verifier) if tol == 0 else abs(builder - verifier) <= tol
    ledger.append({"figure": name, "builder": builder, "verifier": verifier,
                   "status": "REPRODUCED" if ok else "MISMATCH"})
    print(f"{'OK ' if ok else 'BAD'} {name}: builder={builder} verifier={verifier}")


sales = pd.read_parquet(STACK / "layers/sales_clean.parquet")
spine = pd.read_parquet(STACK / "joins/parcel_spine_v6.parquet")
mkt = sales[sales["is_market_sale"]].copy()
mkt["sale_date"] = pd.to_datetime(mkt["sale_date"])
mkt = mkt[mkt["sale_date"] <= SNAP]

sp = spine.copy()
for c in ["first_demolition_date", "first_new_building_permit_date"]:
    sp[c] = pd.to_datetime(sp[c])
demo = sp[(sp["first_demolition_date"] >= WIN0) & (sp["first_demolition_date"] <= WIN1)]
reb = demo[demo["demolished_then_rebuilt"] == True]  # noqa: E712
check("demolished parcels in window", stats["citywide"]["demolished_in_window"], len(demo))
check("rebuilt parcels", stats["citywide"]["rebuilt"], len(reb))

# --- vectorized paired cycles (different code path from the builder)
j = reb[["schednum", "neighborhood", "first_demolition_date",
         "first_new_building_permit_date"]].merge(
    mkt[["schednum", "sale_date", "SALE_PRICE", "RECEPTION_NUM"]], on="schednum", how="inner")


def boundary_pick(frame, date_col, side):
    """Independent implementation of the package's boundary-tie rule:
    restrict to the boundary date; drop nominal prices (<= $100) when a
    real price is tied with them; buy side takes the highest
    RECEPTION_NUM on the last date, exit side the lowest on the first."""
    d = frame.groupby("schednum")[date_col].transform(
        "max" if side == "buy" else "min")
    tied = frame[frame[date_col] == d].copy()
    real = tied[tied["SALE_PRICE"] > 100].groupby("schednum")["SALE_PRICE"].size()
    tied["has_real"] = tied["schednum"].map(real).fillna(0) > 0
    tied = tied[(tied["SALE_PRICE"] > 100) | (~tied["has_real"])]
    tied = tied.sort_values("RECEPTION_NUM")
    pick = tied.groupby("schednum").tail(1) if side == "buy" else tied.groupby("schednum").head(1)
    return pick[["schednum", "SALE_PRICE"]]


pre = j[j["sale_date"] < j["first_demolition_date"]]
buy = boundary_pick(pre, "sale_date", "buy").rename(columns={"SALE_PRICE": "buy"})
post = j[j["sale_date"] > j["first_new_building_permit_date"]]
sell = boundary_pick(post, "sale_date", "exit").rename(columns={"SALE_PRICE": "sell"})
pairs = buy.merge(sell, on="schednum", how="inner")
pairs["spread"] = pairs["sell"] - pairs["buy"]
cw = stats["citywide"]
check("paired cycles", cw["paired_cycles"], len(pairs))
check("paired median buy", cw["paired_median_buy"], float(pairs["buy"].median()))
check("paired median sell", cw["paired_median_sell"], float(pairs["sell"].median()))
check("paired median spread", cw["paired_median_spread"], float(pairs["spread"].median()))

# --- removed stock, vectorized
jd = demo[["schednum", "first_demolition_date"]].merge(
    mkt[["schednum", "sale_date", "SALE_PRICE", "RECEPTION_NUM"]], on="schednum", how="inner")
pred = jd[jd["sale_date"] < jd["first_demolition_date"]]
last_buy = boundary_pick(pred, "sale_date", "buy")
check("demolished with observable pre-demo buy", cw["removed_with_observable_buy"],
      int(last_buy["schednum"].nunique()))
check("removed buys at or under $500K", cw["removed_buys_le500k"],
      int((last_buy["SALE_PRICE"] <= 500_000).sum()))
check("removed median buy", cw["removed_median_buy"], float(last_buy["SALE_PRICE"].median()))

# --- zero-backstop pools
panel = pd.read_csv(PKG / "data/neighborhood_index.csv")
zero_nb = set(panel.loc[panel["restricted_units"] == 0, "neighborhood"])
z = stats["zero_backstop_neighborhoods"]
nb_of = demo.set_index("schednum")["neighborhood"]
check("demolished parcels in zero-restricted neighborhoods",
      z["demolished_parcels_in_them"], int(nb_of.isin(zero_nb).sum()))
pz = pairs[pairs["schednum"].isin(nb_of[nb_of.isin(zero_nb)].index)]
check("paired cycles in zero-restricted neighborhoods", z["paired_cycles_in_them"], len(pz))
check("paired median spread in zero-restricted neighborhoods",
      z["paired_median_spread_in_them"], float(pz["spread"].median()))
pnz = pairs[~pairs["schednum"].isin(nb_of[nb_of.isin(zero_nb)].index)]
check("paired median spread elsewhere", z["paired_median_spread_elsewhere"],
      float(pnz["spread"].median()))

# --- HOST inventory re-summed from the raw 2026-10-21 pull
raw = json.loads((HF / "denver-affordable-housing-brief-2026-10-21/data/raw.json").read_text())
feats = raw["features"] if isinstance(raw, dict) and "features" in raw else raw
attrs = [f["attributes"] if "attributes" in f else f for f in feats]
inv = pd.DataFrame(attrs)
check("HOST inventory projects (raw pull)", 497, len(inv))
check("HOST inventory restricted units (raw pull)", 29474,
      int(inv["RESTRICTED_UNITS"].sum()))
by_nb = inv.groupby("NEIGHBORHOOD")["RESTRICTED_UNITS"].sum()
zero_from_raw = sorted(set(panel["neighborhood"]) - set(by_nb[by_nb > 0].index))
check("zero-restricted neighborhood list matches raw pull",
      ",".join(sorted(zero_nb)), ",".join(zero_from_raw))
check("panel restricted units total", int(panel["restricted_units"].sum()),
      int(by_nb.sum()))

# --- permit-register cross-check (different basis, reported as such)
demos = pd.read_parquet(STACK / "layers/demolitions_clean.parquet")
demos["date"] = pd.to_datetime(demos["date"])
wrk = demos[(demos["is_wreck"]) & (demos["active"]) &
            (demos["date"] >= WIN0) & (demos["date"] <= WIN1)]
reg = wrk.groupby("NEIGHBORHOOD").size().rename("register_demolitions")
spn = demo.groupby("neighborhood").size().rename("spine_demolished")
both = pd.concat([reg, spn], axis=1).dropna()
rho = both.corr(method="spearman").iloc[0, 1]
print(f"cross-basis check: permit-register vs parcel-spine neighborhood demolition "
      f"counts, Spearman rho = {rho:.3f} over {len(both)} neighborhoods "
      f"(bases differ by construction; recorded, not reconciled)")
ledger.append({"figure": "Spearman rho, register vs spine demolition counts by neighborhood",
               "builder": round(float(rho), 3), "verifier": "cross-basis",
               "status": "RECORDED"})
top_reg = reg.sort_values(ascending=False).head(3).index.tolist()
top_spn = spn.sort_values(ascending=False).head(3).index.tolist()
print(f"top-3 demolition neighborhoods, register basis: {top_reg}; spine basis: {top_spn}")
ledger.append({"figure": "top-3 neighborhoods agree across bases",
               "builder": str(top_spn), "verifier": str(top_reg), "status": "RECORDED"})

# --- index table spot recomputation (Washington Park, from panel inputs)
wp_row = panel[panel["neighborhood"] == "Washington Park"].iloc[0]
check("Washington Park demolished (panel)", 268, int(wp_row["demolished"]))
check("Washington Park teardown rate per 1,000 parcels",
      75.0, round(float(wp_row["demolished"] / wp_row["parcels_total"] * 1000), 1), tol=0.05)

pd.DataFrame(ledger).to_csv(PKG / "data/verification_ledger.csv", index=False)
bad = [r for r in ledger if r["status"] == "MISMATCH"]
print(f"\nLEDGER: {len(ledger)} rows, {len(bad)} mismatches")
assert not bad
