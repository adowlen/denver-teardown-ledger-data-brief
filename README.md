# Denver: The Teardown Ledger - package README

Topic (Machine Readable meta-analysis, built 2026-11-17): join the four earlier Denver analyses (the assessor sales keystone, permits and demolitions, housing permits, and the HOST affordable housing inventory) on the parcel and neighborhood keys they share, and measure the completed teardown cycle end to end: what was bought, what was demolished, what replaced it, what it sold for, and where the income-restricted backstop is absent.

Status: PUBLISHED 2026-11-21. The package passed its Section 13.3 cold-reader gate and a light structure pass on 2026-11-17; the pass changed no figure (368 numeric tokens diffed identical before and after).

## Contents
- brief.md - the brief (publishable text)
- stats.json - every figure used in the brief, produced by code/analyze.py
- verification.md - independent verification record and the reconciliation against the October briefs' snapshot
- reviewer-notes.md - claims most likely challenged, Section 11.3 exception flags, chart and hero verification, structure-pass record
- sources.md - dataset citations, snapshot note, and access notes
- hero.png - hero graphic (generated illustration + composited verified figure; code/hero_composite.py)
- hero-headline.txt - hero headline choice record (42.2 percent chosen over the $1,635,000 variant)
- charts/ - chart_index.png, chart_cycle_funnel.png, chart_cycle_prices.png, chart_zero_backstop.png (drawn by code/charts.py from stats.json and data/neighborhood_index.csv)
- data/ - neighborhood_index.csv (all 78 neighborhoods), paired_cycles.csv (616 completed cycles), verification_ledger.csv, audit_output.txt
- code/ - analyze.py, verify_independent.py, charts.py, hero_composite.py
- hero_source/ - the raw generated illustration before compositing

## Dependencies (match code imports)
python 3.12; pandas, numpy, matplotlib, Pillow (hero composite)

## Rebuild order
1. code/analyze.py (writes stats.json, data/neighborhood_index.csv, data/paired_cycles.csv)
2. code/verify_independent.py (writes data/verification_ledger.csv; its ledger reproduced the analysis on 21 of 21 rows)
3. code/charts.py, code/hero_composite.py

## Data provenance
City and County of Denver open data (host: services1.arcgis.com/zdB7qR0BtYrg0Xpl) via the Machine Readable Denver warehouse, 2026-11-01 snapshot: assessor sales and parcels, demolition and new-building permit registers, the HOST Affordable Housing Inventory as filed (pulled in full 2026-10-21), and ACS 2020-2024 5-year B25001 denominators. The analysis window matches the source briefs (demolitions from 2020-01-01 to 2026-10-12). Full citations are in sources.md; the reconciliation against the 2026-10-15 snapshot the October briefs used is in verification.md.
