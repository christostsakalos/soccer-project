# Step 1 verification — 9 November 2026

Implemented configuration, package metadata, collection, ordinary HTTP transport,
recursive inventory, provenance manifest, documentation and synthetic tests.
Dependencies were installed into the existing `env`; exact versions are in
`requirements-lock.txt`. No production files existed to move or hash-compare.

Commands executed from the repository root:

```powershell
.\env\Scripts\python.exe -m pip install pandas PyYAML soccerdata pytest
.\env\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e .
.\env\Scripts\python.exe -m football_similarity.download_data --limit 1
.\env\Scripts\python.exe -m football_similarity.inspect_data
.\env\Scripts\python.exe -m pytest -q
.\env\Scripts\python.exe -m pip check
```

- Tests: **14 passed**; tiny synthetic data only.
- Dependency consistency: **No broken requirements found**.
- Inspection: **0 CSVs, 0 fields, 0 inspection failures**. Both CSV reports have
  headers; collection manifest lists all 18 requested combinations.
- Collection: **exit code 1**, HTTP 403 Forbidden at the initial FBref competition
  page. One configured table attempted; remaining 17 unattempted. No retry or
  bypass followed the restriction. Timestamp and error are in the attempt log.
- Five requested categories are unsupported by the installed library, independently
  of the source-access failure. Support flags are in the manifest.

Implementation checks pass. Dataset acceptance remains incomplete: there are no
real exports, so real sizes, missingness, identifiers, transfer rows, goalkeeper
fields and field semantics cannot be validated. Empty reports are not evidence
of clean production data. Genuine existing exports can be inventoried without
network access; do not invent replacements or bypass source restrictions.

Stop at Step 1. Supervisor review is required before Step 2, particularly the
row definition (player-season or player-team-season), stable IDs, transfers,
goalkeeper policy, source availability and final league/season/category scope.
