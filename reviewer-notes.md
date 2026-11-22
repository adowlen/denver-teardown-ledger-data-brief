# Reviewer notes - Denver: The Teardown Ledger (DRAFT, not published)

For Alex. This is a draft package: brief.md, stats.json,
data/neighborhood_index.csv (all 78 neighborhoods),
data/paired_cycles.csv (616 cycles), data/verification_ledger.csv,
sources.md, verification.md, code/analyze.py,
code/verify_independent.py. Nothing has been published or sent.

## Intended thesis (Section 13.1, recorded before the write-up)

Denver's completed teardown cycles replace a house with one that
sells for about 3.5 times the purchase price, and the neighborhoods
where that replacement is most intense are the ones with the least
income-restricted housing: four of the six highest-pressure
neighborhoods record none at all.

## Headline findings (all verified, 21 of 21 ledger rows reproduced)

1. 260 of 616 completed teardown cycles (42.2 percent) closed in the
   15 neighborhoods where HOST's inventory records zero
   income-restricted units. Those neighborhoods also hold 758 of
   3,281 demolished parcels (23.1 percent), and their median cycle
   spread is $1,948,750 against $1,382,500 elsewhere.
2. The index (teardown rate per 1,000 parcels x median paired spread
   x backstop absence, equal-weight percentile ranks, 16 qualifying
   neighborhoods) is led by Washington Park (89.6), Cory - Merrill
   (83.3), University Park (77.1), Belcaro (75.0), Hilltop (72.9),
   and Platt Park (66.7). The six together: 879 demolitions, 311
   paired cycles, 27 restricted units combined, four of them zero.
3. Of demolished parcels with an observable pre-demolition market
   buy (1,913 of 3,281), the median buy was $711,000 and 421
   (22.0 percent) were at or under $500,000. The cheapest removed
   stock is in Overland (median $459,000; 10 of 15 observable buys at
   or under $500,000) and Villa Park ($445,000; 8 of 10), where
   almost no cycle closes in the sales record (2 and 0 paired).
4. Citywide cycle, this snapshot: 3,281 demolished, 2,326 rebuilt
   (70.9 percent), 616 paired; median buy $650,000, median first
   post-rebuild sale $2,299,762.50, median gross spread $1,635,000,
   median sell-to-buy ratio 3.45, median 28.3 months deed to deed.

## Claims most likely to be challenged

- Snapshot change: the October briefs used the warehouse's
  2026-10-15 snapshot; this package uses the 2026-11-01 re-snapshot
  (the warehouse refreshed the layers on Nov 1; there was no way to
  run this join on the October layers because spine v6 and the
  refreshed sales layer are the current stack). Every shared figure
  is reconciled in verification.md; the largest move is demolished
  parcels 3,297 to 3,281 (records restated in the source). The
  brief discloses this in its data notes rather than quietly
  restating the October numbers.
- "No affordable backstop" means zero units in HOST's published
  inventory as filed. The 2026-10-21 brief documented that
  dispersed-site portfolios are booked to single neighborhoods, so a
  zero here is a statement about the inventory as filed; the brief
  repeats that limit.
- The paired-cycle medians describe the 26.5 percent of rebuilt
  parcels that sold on both sides of the cycle. They are not
  medians for all rebuilds, and the brief says so.
- The index is a constructed ranking (equal-weight percentile
  ranks). Its components print in data/neighborhood_index.csv so
  any reader can reweight; the brief prints the method in one
  paragraph and never treats the score as a measurement.

## Checks that could not be completed / caveats that must print

- UNITS: permit UNITS fields are present on 55.9 percent of
  new-building permits and 41.4 percent of demolition permits
  (positive values 55.6 / 40.5 percent). Unit loss is not
  computable; the brief is structures and prices only, and says so
  in the lede's second paragraph and again in data notes. (Tasking
  figures of 55.9 / 41.4 reproduced exactly.)
- Sun Valley is excluded from the ranked index for the reason the
  2026-10-21 brief printed (its ACS unit base, 502.9, is smaller
  than its recorded restricted count, 1,196, so its rate cannot be
  ranked). On the parcel basis it records 11 demolished parcels and
  0 rebuilt in the window.
- Right-censoring: final-12-month demolitions show a 46.0 percent
  rebuilt share vs 74.9 percent earlier; the index avoids raw
  rebuilt shares for this reason.
- Same-day deed clusters required a boundary-tie rule (56 parcels);
  the verifier caught a 2-parcel discrepancy first. Rule and counts
  are documented in verification.md.
- Charts and hero: BUILT 2026-11-17 (Alex approved "charts et al").
  Hero: hero.png at package root, headline 42.2 percent (the
  $1,635,000 spread variant was composited and viewed; the
  percentage was chosen for card-size legibility and because it
  matches the title and thesis; record in hero-headline.txt, art in
  hero_source/, composite by code/hero_composite.py reading
  stats.json). Charts, all data-drawn by code/charts.py from
  stats.json and data/neighborhood_index.csv, all viewed after
  rendering, plotted values recorded in verification.md under
  "Chart and hero verification": charts/chart_index.png (index for
  the 16 qualifying neighborhoods with demolitions and restricted
  units alongside), charts/chart_cycle_funnel.png (3,281 to 2,326
  to 616), charts/chart_cycle_prices.png (median buy $650,000 vs
  median first sale $2,299,762.50, spread $1,635,000),
  charts/chart_zero_backstop.png ($1,948,750 vs $1,382,500 medians;
  top six 879 demolitions vs 27 restricted units). Hero and charts
  are inserted in brief.md at the findings they support. The
  Section 13.3 cold-reader gate is now the ONLY remaining
  pre-publication step; it runs as a separate pass. No social copy
  is drafted (distribution is a separate, selective decision per
  the standards).

## Exception flags (Section 11.3)

- Agencies named: HOST and Community Planning & Development are the
  brief's audience and appear in "Who can act." No official is
  named; no finding characterizes any agency's motives or competence.
- Surprises: (1) Sunnyside, with the fourth-most demolitions (150),
  ranks last on the index because its restricted rate is the highest
  among ranked neighborhoods and its median spread is the lowest;
  the index is not a demolition-count ranking. (2) The demolished
  count fell on the warehouse refresh. (3) University Park's median
  spread ($2,432,250) exceeds Washington Park's ($2,140,000); it
  ranks third only because its teardown rate and backstop scores are
  lower.
- First use of a joined dataset: this is the first package to join
  the HOST inventory to the parcel spine; the join is by statistical
  neighborhood name, verified against the raw pull (totals and the
  zero list reproduce exactly).

## Structure pass (2026-11-17, after the Section 13.3 cold-reader gate)

Cold-reader gate result: PASSED on the point. The fresh reader's
one-sentence takeaway matched the recorded thesis above (teardown
cycles reprice most aggressively where the HOST inventory records no
income-restricted homes). Most memorable number: 879 demolished
parcels against 27 restricted units across the top six. Alex approved
a light structure pass on the reader's friction points only; no new
analysis was added, and the reader's two scope gaps (who lived in the
houses; whether the wave is accelerating) were deliberately NOT
addressed. Changes made to brief.md:

1. Opening thinned: the Washington Park lede now carries only the
   demolition count and the zero-restricted record. The parcel
   denominator (3,572), the one-in-13 share, the 87 cycles, and the
   $1,000,000 / $3,100,000 medians moved to Finding 3, where the
   neighborhood machinery and table live.
2. Vocabulary defined at first body use: "completed cycle" and
   "parcel basis" in the citywide paragraph; "right-censored" in the
   funnel caption; "backstop" and "the inventory as filed" at the
   head of Finding 2, before the zero-backstop chart appears. Chart
   PNGs were not redrawn.
3. Gross-spread-is-not-profit caveat cut to two mentions in the brief
   text (intro and Data notes); the Finding 1 prices caption no
   longer repeats it. Caveats printed on the chart graphics are
   untouched.
4. Finding 1: the final-12-months censoring caveat (46.0 vs 74.9
   percent) moved out of the finding's flow into a marked
   "Censoring note" after the prices chart, wording otherwise intact.
5. Finding 3: index-construction prose compressed to the three
   components, the equal-weight percentile construction, the
   qualification thresholds, and the Sun Valley base mismatch; a
   sentence added after the index chart stating the chart carries
   the ranking and the table is the full record. Table and all data
   retained.
6. Finding 5: the percentage bases are now stated in prose (the 13
   neighborhoods' rebuilt parcels for 41.9 / 41.6; all rebuilt
   parcels citywide for 61.2 / 43.8). Numbers unchanged.
7. Cross-references glossed with a half-clause each: the keystone
   91.2 percent (purchase-timing measure), the keystone citywide
   price mix in Finding 4, the Sun Valley base mismatch, and the
   2026-10-11 permit-geography measure in "Who can act."
8. Section order swapped: "What this might mean" now precedes
   "Data notes and limits."

Verification after the pass: every numeric token in brief.md was
extracted before editing (368 tokens) and diffed after; the multiset
is identical (the only raw-token difference was a trailing comma the
extractor captured where a colon became a comma in the lede — no
figure changed). Package grep for the silent-truncation marker:
none. Brief tail read back intact (ends with the Methods paragraph).
