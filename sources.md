# Sources - Denver: The Teardown Ledger (meta-analysis, DRAFT, built 2026-11-17)

This package joins four previously published Machine Readable analyses.
It introduces no new external source. All computation runs on the
Machine Readable Denver warehouse (hidden_files/stack/denver), whose
layers are snapshots of City and County of Denver open data services
(host: services1.arcgis.com/zdB7qR0BtYrg0Xpl).

## Snapshot note (read first)

The October briefs ran on the warehouse's 2026-10-15 snapshot. The
warehouse re-snapshotted the same services on 2026-11-01 (stack
manifest.json: assessor sales snapshot_date 2026-11-01, service last
edit 2026-10-29T09:47:14Z; cleaned layers rebuilt 2026-11-01). This
package computes on the 2026-11-01 snapshot and keeps the source
briefs' analysis window (demolitions from 2020-01-01 to 2026-10-12) so
it covers the same period they published. Citywide lifecycle figures
on the two snapshots differ by recordings posted between them; the
reconciliation is recorded in verification.md and disclosed in the
brief's data notes. No figure in this package mixes snapshots.

## Layers used

1. Assessor sales (warehouse layer sales_clean.parquet; snapshot
   2026-11-01; 314,041 rows, SALE_YEAR 2015-2026): City and County of
   Denver Real Property Sales and Transfers, ArcGIS FeatureServer
   table 51 of ODC_real_property_sales_and_transfers. Market sale =
   INSTRUMENT in (WD, SW) and SALE_PRICE > 0 (the layer's
   is_market_sale flag; definition from the 2026-10-16 keystone
   package's prep memo, including its stated direction of error).
   Sale dates composed from SALE_YEAR + SALE_MONTHDAY in the layer
   build. One market-sale row dated after the snapshot (2026-12-30)
   is excluded from every dated figure.
2. Parcel spine (warehouse joins/parcel_spine_v6.parquet; 240,496
   parcels): assessor parcels (ODC_PROP_PARCELS_A, layer 245)
   carrying each parcel's statistical neighborhood (centroid join,
   99.96 percent assigned; 106 parcels unassigned, none of them
   demolished in the window), first demolition date, first
   new-building permit date, and the demolished-then-rebuilt flag,
   built by the warehouse from the permit layers below.
3. Permits and demolitions (warehouse layers permits_clean.parquet,
   demolitions_clean.parquet): Denver development services permit
   registers as cleaned for the 2026-10-15 permits x demolitions
   package (wreck classification, active/cancelled handling, and
   parcel matching are that package's, carried in the layers). Used
   here for the UNITS-field coverage figures and the cross-basis
   demolition-geography check only; the brief's demolition counts are
   parcel-basis (spine), and the two bases are never mixed in one
   figure.
4. HOST Affordable Housing Inventory (package
   denver-affordable-housing-brief-2026-10-21, data/raw.json and
   data/neighborhood_panel_affordable.csv): HOST_AFFORDABLEHOUSING
   layer pulled in full 2026-10-21: 497 projects, 29,474 restricted
   units as filed. Neighborhood rates divide restricted units by ACS
   housing units (ACS 2020-2024 5-year table B25001, allocated to the
   78 statistical neighborhoods by tract area; panel total 359,351.5
   units; citywide rate 82.0 restricted units per 1,000 housing
   units). Two projects (85 units) carry no neighborhood and are in
   citywide totals only, so neighborhood restricted units sum to
   29,389.
5. Neighborhood sales panel (package sales-keystone-brief-2026-10-16,
   data/neighborhood_sales.csv): per-neighborhood market-sale counts,
   medians, and shares of sales at or under $500,000 for 2020-21 and
   2024-25, computed on the 2026-10-15 snapshot. Used here only for
   the citywide context figure (share of sales at or under $500,000:
   57.2 percent in 2020, 47.4 percent in 2025, from that package's
   stats.json) and neighborhood median single-family prices.

## Context figures cited from earlier briefs (not recomputed)

- Blueprint Denver growth areas: 2,940 of 11,559 new buildings
  permitted 2020 to October 2026 were inside designated growth areas
  (25.4 percent; 74.6 percent outside), from the 2026-10-11 Denver
  Housing Permits package (output/stats.json).
- Citywide lifecycle on the 2026-10-15 snapshot (3,297 demolished
  parcels, 2,335 rebuilt, 611 paired cycles, median gross spread
  $1,635,000), from the 2026-10-16 package's stats.json; cited only
  in the reconciliation.

## Derived figures

Every rate, share, percentile rank, index score, ratio, and per-day
figure in the brief is derived from the layers above by
code/analyze.py and labeled derived where the series' style requires.
Prices are nominal dollars as recorded, never summed across parcels
(multi-parcel transactions repeat one price per parcel row in the
source).
