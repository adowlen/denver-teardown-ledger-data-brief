# Verification - Denver: The Teardown Ledger (DRAFT)

Builder: code/analyze.py. Independent verifier:
code/verify_independent.py (separate implementation: vectorized
merge-based cycle construction instead of per-parcel iteration;
HOST inventory re-summed from the 2026-10-21 package's raw pull;
demolition geography cross-checked on the permit register).
Full ledger: data/verification_ledger.csv (21 rows, 0 mismatches).

## Reconciliation against the published packages (snapshot change)

The October briefs ran on the warehouse's 2026-10-15 snapshot; this
package runs on the 2026-11-01 re-snapshot of the same services
(sources.md). Same window, same definitions.

| Figure | Published (2026-10-15 snapshot) | This package (2026-11-01 snapshot) |
|---|---|---|
| Market sales, 2020+ | 105,585 | 105,998 (+413 recordings) |
| Parcels demolished in window | 3,297 | 3,281 |
| Rebuilt parcels | 2,335 (70.8%) | 2,326 (70.9%) |
| Paired cycles | 611 | 616 |
| Paired median buy | $650,000 | $650,000 |
| Paired median sell | $2,299,525 | $2,299,762.50 |
| Paired median gross spread | $1,635,000 | $1,635,000 |
| Washington Park demolished / rebuilt / paired | 268 / 237 / 85 | 268 / 237 / 87 |
| Washington Park median spread | $2,140,000 | $2,140,000 |
| New-building permits in window (register) | 11,585 | 11,585 |
| Demolition permits in window (register) | 3,837 | 3,836 |

All lifecycle counts moved by less than 0.6 percent. The demolished
count fell by 16 on the refresh (permit records restated or withdrawn
in the source between snapshots); the paired count rose by 5 (exits
recorded between snapshots). Medians are unchanged to the dollar on
buy and spread.

## Pre-flight audit (Section 10), evidence in data/audit_output.txt

- 10.1.1 Sentinels: 56,182 sales rows carry SALE_PRICE of 0, null, or
  negative; asserted that none of them carries the market-sale flag.
  UNITS values of 0 in the permit registers (31 new-building, 33
  demolition rows) are counted separately from missing values and are
  never read as a unit count.
- 10.1.2 Polarity: 3-row samples inside the market filter (WD/SW,
  positive prices) and outside it (QC rows at $10 consideration)
  printed in the audit output and checked against the filter comment.
- 10.1.3 Unit agreement: demolitions, rebuilds, and cycles are counted
  in parcels on both sides of every rate; teardown rates divide
  parcels by parcels; restricted rates divide units by ACS housing
  units and are labeled as such wherever they appear. Prices are
  never summed across parcels.
- 10.1.4 Exhaustiveness: full Counter() of INSTRUMENT (56 values) and
  the top of D_CLASS_N recorded in the audit output before the
  market-sale filter was applied.
- 10.1.5 Nullable denominators: neighborhood shares are computed on
  full stated populations; the panel asserts that assigned parcels
  (240,390) plus unassigned parcels (106) equal the spine total
  (240,496), and that neighborhood demolitions plus unassigned
  demolitions (0) equal the citywide count (3,281).
- 10.2 Join hygiene: sales-to-parcel keying is the warehouse's
  verified schednum join (see the 2026-10-15 prep memo: 98.54 percent
  of sales rows matched to a current parcel on the earlier snapshot).
  Cross-basis control: neighborhood demolition counts on the
  permit-register basis vs the parcel-spine basis correlate at
  Spearman rho 0.974 over 77 neighborhoods, and the top three
  neighborhoods are identical on both bases (Washington Park,
  Berkeley, Sloan Lake). The bases are reported separately and never
  averaged.
- 10.2 Built-in control: the Washington Park lifecycle, computed as a
  control neighborhood by the 2026-10-16 package, is recomputed here
  and matches on demolished (268), rebuilt (237), and median spread
  ($2,140,000); paired cycles rose 85 to 87 on recordings posted
  between snapshots.
- 12.2 Boundary distribution: among rebuilt parcels, 0 market sales
  fall on the demolition date, 1 falls on the permit date, and 76
  fall between demolition and permit (published, earlier snapshot:
  0 / 1 / 77). The strict orderings (buy before demolition, exit
  after permit) exclude those 76 by construction; they are most
  plausibly sales of the cleared lot or of the parcel mid-project.
- 12.2 Tie rule (verifier finding, fixed and re-verified): the first
  verifier pass found the at-or-under-$500,000 removed count differed
  by 2 (builder 422, verifier 424). Cause: 56 demolished parcels have
  more than one market sale on their last pre-demolition date
  (same-day deed clusters; 51 at differing prices, including $10
  nominal deeds recorded against the same sale date). Both
  implementations now apply one printed rule: among sales tied on a
  boundary date, nominal prices (at or under $100) never win when
  another tied sale exceeds $100; then the highest reception number
  wins on the buy side and the lowest on the exit side. Under the
  rule the count is 421 and the removed-stock median buy is $711,000;
  both implementations reproduce both figures. Across the lifecycle
  and removed-stock passes the rule met 101 buy-side ties and 5
  nominal exclusions, and 1 exit-side tie.
- 12.3 Censoring: rebuilt shares are right-censored. Demolitions in
  the final 12 months of the window (459 parcels) show a rebuilt
  share of 46.0 percent; demolitions earlier in the window (2,822)
  show 74.9 percent. The brief's index uses demolition rates and
  completed-cycle prices, not raw rebuilt shares, for this reason,
  and the censoring figures print in the brief's data notes.
- 12.4 One basis per number: parcel-basis and permit-register-basis
  counts are never combined in one figure; where both appear, each
  is labeled.

## Methods checklist outcomes (Section 3)

- Base rates and exposure: teardown intensity is reported per 1,000
  parcels in the neighborhood (parcel counts from the spine), never
  as raw counts alone; restricted supply is reported per 1,000 ACS
  housing units, the 2026-10-21 brief's basis.
- Direction of causality: the brief reports co-location of teardown
  activity, replacement prices, and restricted supply. It does not
  claim that any one causes another; the strongest alternative
  explanation (a common cause in land prices and in five decades of
  program siting) is stated in "What this might mean."
- Category and definition changes: the market-sale definition, the
  wreck classification, and the neighborhood geography are carried
  unchanged from the source packages; the one definition added by
  this package (the boundary-tie rule) is documented above.
- Time windows: demolitions 2020-01-01 to 2026-10-12 exactly (the
  source briefs' window); sales used through the 2026-11-01 snapshot;
  the HOST inventory is the 2026-10-21 pull; ACS units are the
  2020-2024 5-year estimates. The HOST housing needs assessment this
  brief is framed for is due December 2026 (per the tasking memo;
  see reviewer notes).
- Joins and match rates: neighborhood assignment covers 99.96
  percent of parcels and 100 percent of demolished parcels in the
  window. Paired cycles require both a pre-demolition market buy and
  a post-permit market sale on the same parcel: 616 of 2,326 rebuilt
  parcels (26.5 percent) qualify, so cycle medians describe
  completed, resold rebuilds, not all rebuilds. Of rebuilt parcels,
  1,424 (61.2 percent) have a buy side and 1,019 (43.8 percent) an
  exit side.
- Small numbers: the ranked index requires at least 30 demolitions
  and at least 10 paired cycles in the neighborhood. Percentages on
  counts under 30 are printed with their counts (Overland: 10 of 15
  observable buys; Villa Park: 8 of 10).
- Official definitions: neighborhoods are the city's statistical
  neighborhoods, as in every brief in this series; "income-restricted"
  is HOST's inventory definition as filed.
- Layering admission test: the sales layer is what lets the brief
  price the stock removed and the replacement (no other layer carries
  prices); the HOST layer is what lets the brief say whether a
  restricted backstop exists in the same neighborhood (no other layer
  records restricted supply); the permit layers contribute only the
  UNITS-coverage finding and the cross-basis control, and are labeled
  as such.

## Figures NOT verified or not computable

- Unit counts lost and gained: not computable. The UNITS field is
  present on 55.9 percent of new-building permits and 41.4 percent of
  demolition permits in the window (positive values on 55.6 and 40.5
  percent). No unit-loss figure appears anywhere in the brief.
- Construction cost, and therefore profit: not in any source. The
  spread printed throughout is the gross difference between two
  recorded sale prices, before construction, fees, financing, and
  time; the brief says so wherever the figure carries weight.
- Whether displaced occupants existed at any demolished address: no
  source records occupancy. The brief makes no occupancy claim.

## Chart and hero verification (visual package, 2026-11-17)

Charts are drawn by code/charts.py, which reads every plotted value
from stats.json and data/neighborhood_index.csv at build time (no
hand-typed figures). Each chart was rendered and viewed; the first
render round had footnote text running past the right edge on all
four charts, an annotation box overlapping the sale-price label on
chart_cycle_prices.png, and a panel title colliding with the figure
subhead on chart_zero_backstop.png. All were fixed (footnotes wrapped
to figure width, dollar axes formatted, annotation repositioned,
panel titles folded into labels) and the fixed renders were viewed
again. Plotted values, tied to source:

- charts/chart_index.png - all 16 qualifying neighborhoods from
  data/neighborhood_index.csv (fields: index, demolished,
  restricted_units), sorted by index descending: Washington Park
  89.6 / 268 / 0; Cory - Merrill 83.3 / 139 / 0; University Park
  77.1 / 129 / 23; Belcaro 75.0 / 100 / 0; Hilltop 72.9 / 104 / 0;
  Platt Park 66.7 / 139 / 4; Berkeley 41.7 / 218 / 129; Sloan Lake
  41.7 / 152 / 339; West Highland 39.6 / 98 / 45; Washington Park
  West 39.6 / 109 / 15; Montclair 37.5 / 44 / 5; North Park Hill
  37.5 / 66 / 0; University Hills 37.5 / 82 / 221; University
  33.3 / 105 / 98; Hale 22.9 / 50 / 118; Sunnyside 20.8 / 150 / 691.
  The same 16 rows, in the same order and with the same values, as
  Finding 3's table in brief.md. Structures-not-units caveat printed
  on the graphic.
- charts/chart_cycle_funnel.png - stats.json citywide:
  demolished_in_window 3,281; rebuilt 2,326 (rebuilt_share_pct 70.9);
  paired_cycles 616 (26.5 percent of rebuilt and 18.8 percent of
  demolished, derived at build time from the same three counts).
  Structures-not-units caveat and the right-censoring note (46.0
  percent vs 74.9 percent, stats.json censoring) printed on the
  graphic.
- charts/chart_cycle_prices.png - stats.json citywide:
  paired_median_buy $650,000; paired_median_sell $2,299,762.50;
  paired_median_spread $1,635,000; paired_median_ratio 3.45;
  paired_median_months 28.3. The gross-spread (not profit) caveat is
  printed on the graphic.
- charts/chart_zero_backstop.png - stats.json zero_backstop_
  neighborhoods: paired_median_spread_in_them $1,948,750 over
  paired_cycles_in_them 260; paired_median_spread_elsewhere
  $1,382,500 over 356 cycles (616 - 260, derived at build time);
  the 41 percent lift is the brief's derived figure, recomputed at
  build time (40.96 percent). Right panel: stats.json top6_combined
  demolished 879 and restricted_units_combined 27. The footnote
  states the two right-panel counts are different kinds of record,
  and the structures-not-units caveat is printed on the graphic.

Hero: hero.png (package root, the location prior packages use),
composited by code/hero_composite.py over the generated illustration
in hero_source/ (brand palette: dark charcoal, amber, teal; the
story the art tells is recorded in hero-headline.txt). All hero text
is read from stats.json at composite time: headline 42.2 percent
(stats.json paired_share_in_zero_backstop_pct) of 616 completed
cycles (citywide.paired_cycles). The alternate $1,635,000 headline
(paired_median_spread) was composited and viewed as well; the 42.2
percent headline was chosen because it matches the brief's title
and the recorded thesis and reads cleanly at catalog-card size.
Both variants were viewed at full size and at 480px wide; headline
and sub are fully legible at both.
