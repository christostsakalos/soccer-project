# Football player similarity — Step 1

Python research project for auditing aggregated player statistics. FBref is the
data source; `soccerdata` is the retrieval library. This stage collects and
inventories data only. No merged player matrix, preprocessing, or models exist.

## Run from the repository root

The existing Windows virtual environment is `env` (Python 3.14). Explicit paths
also work when a terminal has not activated it.

```powershell
.\env\Scripts\python.exe -m pip install -e ".[test]"
.\env\Scripts\python.exe -m football_similarity.inspect_data
.\env\Scripts\python.exe -m pytest -q
```

Edit `config/settings.yaml` to choose competitions, seasons and categories.
The two leagues and 2024–2025 season are illustrative starting scope, pending
supervisor confirmation. Relative paths resolve against the configuration's
project root, not the shell's working directory.

```powershell
# First perform a single-table collection check.
.\env\Scripts\python.exe -m football_similarity.download_data --limit 1
# Collect the configured scope after checking source availability.
.\env\Scripts\python.exe -m football_similarity.download_data
# Recreate reports without network access.
.\env\Scripts\python.exe -m football_similarity.inspect_data
```

Collection skips existing CSVs. Inspect them before trusting them: a skipped file
is not proof of validity. Explicit `--overwrite` retains a hash-verified `.bak`
copy before replacing a CSV. Do not run collectors concurrently. Raw exports
retain the DataFrame index, headers, values and library-provided metadata; these
are library exports, not the original FBref HTML. Inspection never modifies them.
Store externally supplied original exports under
`data/raw/<season>/<league>/<category>.csv`; keep their original bytes. Their
retrieval date and library version remain unknown unless documented separately.

## Reports and provenance

`results/tables/dataset_summary.csv` contains sizes, missing cells, exact duplicate
rows, candidate key duplicates, transfer aggregate markers and schema warnings.
`feature_inventory.csv` identifies each column by its position and JSON-encoded
original label (a list for a multi-level label), inferred dtype, missingness and
distinct non-null values. Numeric-looking identifiers can receive numeric dtypes
during inspection; raw bytes remain authoritative. Blank/default pandas NA
markers count as missing; missingness semantics require later review.

`collection_manifest.json` records configured coverage, hashes, export metadata
and collection history from the append-only `download_attempts.jsonl`. New
exports have sidecars recording soccerdata/Python versions, UTC retrieval time,
scope and header layout. Unknown provenance is explicitly labelled. Hash
mismatches are reported, never repaired silently. Empty inventories have headers
and an explicit absent-file coverage list; they are not research results.

Collection makes at most one delayed retry of transient connection failures;
unsupported categories and other errors are recorded without repeated attempts.
Access restriction errors stop the run. No proxy rotation or restriction bypass
is configured. The pinned library's default Selenium transport attempts CAPTCHA
handling, so this project replaces it with ordinary HTTP requests spaced at least
seven seconds apart, with a 30-second timeout. It retains soccerdata parsing and
caching, stops on access restrictions and never launches a browser. The adapter
uses internal APIs verified against version 2026.43.0; retest before upgrading.
Respect FBref terms.
The current [soccerdata FBref reference](https://soccerdata.readthedocs.io/en/latest/reference/fbref.html)
lists only standard, shooting, playing_time, keeper and misc for player-season
tables. This does not guarantee that any historical table remains accessible.

See [data dictionary](docs/data_dictionary.md) and [decisions](docs/decisions.md).
Tests use synthetic fixtures only. `requirements-lock.txt`, when present, records
the verified environment; install it before the editable package to reproduce
exact versions. Source caches and raw exports are ignored by Git by default;
retain them separately with the manifest for reproducibility.

Step 2 requires supervisor review, including the unit of analysis, transfer
aggregation and goalkeeper inclusion. Do not merge on player names alone.

## Verified initial run

On 9 November 2026, the first configured table was attempted. FBref returned
HTTP 403 at `https://fbref.com/en/comps/`; collection stopped immediately.
There are **0 actual datasets and 0 observed fields**. Missingness and football
results cannot be reported. The remaining 17 combinations were not attempted.
Five requested category names are unsupported by the pinned library (ten
league/category combinations). The manifest records support separately from
attempt status. Source availability must be resolved or genuine existing exports
provided before Step 1's dataset acceptance criteria can be satisfied.
