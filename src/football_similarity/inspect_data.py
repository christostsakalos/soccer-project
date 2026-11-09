"""Inventory CSVs without rewriting raw data or flattening column labels."""
import argparse
import csv
import hashlib
import json
import logging
from pathlib import Path
import re
import pandas as pd
from .config import load_config

LOG = logging.getLogger(__name__)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_raw(path: Path) -> tuple[pd.DataFrame, str]:
    """Use export metadata for header depth; flag heuristics on external files."""
    sidecar = path.with_suffix(".metadata.json")
    if sidecar.exists():
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        depth = int(meta["header_rows"])
        index_levels = int(meta.get("index_levels", 0))
        frame = pd.read_csv(
            path, header=list(range(depth)) if depth > 1 else 0,
            index_col=list(range(index_levels)) or None,
            skiprows=[depth] if meta.get("index_name_row") and not index_levels else None,
        )
        return frame.reset_index() if index_levels else frame, "metadata"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        preview = list(__import__("itertools").islice(csv.reader(stream), 8))
    # pandas MultiIndex.to_csv emits an index-name row after column-level rows.
    for i, row in enumerate(preview[1:], 1):
        if any(x.lower() in {"player", "team", "league", "season"} for x in row) and row and row[-1] == "" and preview[0][-1] != "":
            return pd.read_csv(path, header=list(range(i)), index_col=list(range(len([x for x in row if x])))).reset_index(), "inferred_multiindex_review_required"
    return pd.read_csv(path), "single_header_assumed_review_required"


def label(column) -> str:
    return json.dumps(list(column) if isinstance(column, tuple) else column, ensure_ascii=False)


def inspect_file(path: Path, raw: Path) -> tuple[dict, list[dict]]:
    relative = path.relative_to(raw)
    scope = dict(zip(("season", "league", "category"), (*relative.parts[:2], path.stem))) if len(relative.parts) == 3 else {"season": "", "league": "", "category": ""}
    summary = {"path": relative.as_posix(), **scope, "sha256": sha256(path)}
    frame, header_status = read_raw(path)
    names = [str(next((x for x in reversed(c) if x and not str(x).startswith("Unnamed:")), "") if isinstance(c, tuple) else c).lower() for c in frame.columns]
    candidates = [i for i, name in enumerate(names) if name in {"player", "player_id", "team", "squad", "season", "league", "playerid"}]
    player = [i for i in candidates if names[i] in {"player", "player_id", "playerid"}]
    team = [i for i in candidates if names[i] in {"team", "squad"}]
    keys = candidates if player else []
    duplicates = int(frame.iloc[:, keys].duplicated().sum()) if keys else None
    aggregate = sum(bool(re.fullmatch(r"\d+\s+(?:squads?|clubs?|teams?)", str(x), re.I)) for i in team for x in frame.iloc[:, i].dropna())
    summary.update(rows=len(frame), columns=len(frame.columns), missing_cells=int(frame.isna().sum().sum()), exact_duplicate_rows=int(frame.duplicated().sum()), candidate_key_columns=json.dumps([label(frame.columns[i]) for i in keys]), candidate_key_duplicate_rows=duplicates, aggregate_team_rows=aggregate, header_status=header_status, status="ok")
    features = []
    for i, col in enumerate(frame.columns):
        series = frame.iloc[:, i]
        features.append({"path": relative.as_posix(), "column_position": i, "original_column_name": label(col), "inferred_dtype": str(series.dtype), "missing_count": int(series.isna().sum()), "missing_percent": 100 * float(series.isna().mean()) if len(series) else 0, "distinct_values": int(series.nunique(dropna=True))})
    return summary, features


SUMMARY_FIELDS = ["path", "season", "league", "category", "sha256", "rows", "columns", "missing_cells", "exact_duplicate_rows", "candidate_key_columns", "candidate_key_duplicate_rows", "aggregate_team_rows", "header_status", "status", "error"]
FEATURE_FIELDS = ["path", "column_position", "original_column_name", "inferred_dtype", "missing_count", "missing_percent", "distinct_values"]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run(cfg: dict) -> int:
    raw = cfg["paths"]["raw"]
    tables = cfg["paths"]["results"] / "tables"
    for folder in cfg["paths"].values():
        folder.mkdir(parents=True, exist_ok=True)
    summaries, features, manifest = [], [], []
    failed = 0
    for path in sorted(raw.rglob("*.csv")):
        try:
            summary, inventory = inspect_file(path, raw)
            features.extend(inventory)
        except Exception as exc:
            failed += 1
            summary = {"path": path.relative_to(raw).as_posix(), "status": "inspection_failed", "error": str(exc), "sha256": sha256(path)}
        summaries.append(summary)
        metadata = path.with_suffix(".metadata.json")
        try:
            meta = json.loads(metadata.read_text(encoding="utf-8")) if metadata.exists() else {}
            manifest.append({"path": summary["path"], "observed_sha256": summary["sha256"], "provenance": "recorded" if meta else "unknown_existing_file", "hash_matches_export": summary["sha256"] == meta.get("sha256") if meta else None, **{"export_metadata": meta}})
        except (ValueError, OSError) as exc:
            manifest.append({"path": summary["path"], "metadata_error": str(exc)})
            failed += 1
    log = tables / "download_attempts.jsonl"
    attempts = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    write_csv(tables / "dataset_summary.csv", summaries, SUMMARY_FIELDS)
    write_csv(tables / "feature_inventory.csv", features, FEATURE_FIELDS)
    tables.mkdir(parents=True, exist_ok=True)
    coverage = []
    from .transport import SUPPORTED_CATEGORIES
    for season in cfg["data"]["seasons"]:
        for league in cfg["data"]["leagues"]:
            for category in cfg["data"]["categories"]:
                relative = f"{season}/{league}/{category}.csv"
                latest = next((a for a in reversed(attempts) if a["path"] == relative), {})
                coverage.append({"path": relative, "file_present": (raw / relative).is_file(), "supported_by_verified_library": category in SUPPORTED_CATEGORIES, "latest_download_status": latest.get("status", "not_attempted")})
    (tables / "collection_manifest.json").write_text(json.dumps({"source": "FBref", "retrieval_library": "soccerdata", "configured_scope": cfg["data"], "coverage": coverage, "files": manifest, "download_attempts": attempts}, indent=2), encoding="utf-8")
    LOG.info("Inventoried %d CSVs, %d fields, %d failures", len(summaries), len(features), failed)
    return int(failed > 0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/settings.yaml")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    raise SystemExit(run(load_config(args.config)))


if __name__ == "__main__":
    main()
