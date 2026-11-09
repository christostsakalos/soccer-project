"""Conservative, explicit collection of FBref aggregated player tables."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import platform
import time
from .config import load_config
from .inspect_data import sha256, run as inspect
from .transport import reader_class, SUPPORTED_CATEGORIES

LOG = logging.getLogger(__name__)


def collect(cfg: dict, overwrite: bool = False, limit: int | None = None) -> int:
    os.environ.setdefault("SOCCERDATA_DIR", str(cfg["paths"]["raw"].parent / "cache" / "soccerdata"))
    import soccerdata as sd
    if importlib.metadata.version("soccerdata") != "2026.43.0":
        raise RuntimeError("Plain HTTP adapter verified with soccerdata 2026.43.0; install pinned dependencies")
    reader_type = reader_class(sd)
    tables = cfg["paths"]["results"] / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    failed, count = 0, 0
    # Library validates stat_type before retrieval. Unsupported tables are recorded.
    for season in cfg["data"]["seasons"]:
        for league in cfg["data"]["leagues"]:
            for category in cfg["data"]["categories"]:
                if limit is not None and count >= limit:
                    return failed
                count += 1
                path = cfg["paths"]["raw"] / season / league / f"{category}.csv"
                event = {"source": "FBref", "retrieval_library": "soccerdata", "library_version": importlib.metadata.version("soccerdata"), "python_version": platform.python_version(), "season": season, "league": league, "category": category, "path": path.relative_to(cfg["paths"]["raw"]).as_posix(), "attempted_at_utc": datetime.now(timezone.utc).isoformat()}
                if path.exists() and not overwrite:
                    event.update(status="skipped_existing", sha256=sha256(path))
                elif category not in SUPPORTED_CATEGORIES:
                    event.update(status="unsupported", error="Not supported by installed soccerdata read_player_season_stats")
                    failed += 1
                else:
                    retries = int(cfg.get("collection", {}).get("retries", 1))
                    delay = max(10, float(cfg.get("collection", {}).get("retry_delay_seconds", 30)))
                    for attempt in range(retries + 1):
                        try:
                            reader = reader_type(leagues=[league], seasons=[season], data_dir=cfg["paths"]["raw"].parent / "cache" / "FBref")
                            frame = reader.read_player_season_stats(stat_type=category)
                            if frame.empty:
                                raise ValueError("Source returned an empty table; no CSV written")
                            path.parent.mkdir(parents=True, exist_ok=True)
                            # Original DataFrame index, column levels and values are exported unchanged.
                            temporary = path.with_suffix(".csv.tmp")
                            frame.to_csv(temporary)
                            if path.exists():
                                backup = path.with_name(f"{path.name}.{sha256(path)}.bak")
                                if not backup.exists():
                                    import shutil
                                    shutil.copy2(path, backup)
                                if sha256(backup) != sha256(path):
                                    raise OSError("Backup hash verification failed")
                                old_metadata = path.with_suffix(".metadata.json")
                                if old_metadata.exists():
                                    metadata_backup = backup.with_name(backup.name + ".metadata.json")
                                    if not metadata_backup.exists():
                                        shutil.copy2(old_metadata, metadata_backup)
                            temporary.replace(path)
                            event.pop("error", None)
                            event.update(status="downloaded", transport="plain_http_no_challenge_bypass", retrieved_at_utc=datetime.now(timezone.utc).isoformat(), sha256=sha256(path), header_rows=frame.columns.nlevels, index_levels=frame.index.nlevels, index_names=frame.index.names, rows=len(frame), columns=len(frame.columns), previous_file_preserved=overwrite)
                            # pandas exports an index-name row for MultiIndex columns.
                            event["index_name_row"] = bool(frame.columns.nlevels > 1 and any(x is not None for x in frame.index.names))
                            path.with_suffix(".metadata.json").write_text(json.dumps(event, indent=2, default=str), encoding="utf-8")
                            break
                        except Exception as exc:
                            message = str(exc)
                            event.update(status="failed", error=f"{type(exc).__name__}: {message}", attempts=attempt + 1)
                            blocked = any(token in message.lower() for token in ("403", "429", "forbidden", "captcha", "cloudflare", "blocked"))
                            # Only retry transient transport errors, never access restrictions or schema errors.
                            transient = any(token in type(exc).__name__.lower() for token in ("timeout", "connection"))
                            if blocked or not transient or attempt == retries:
                                failed += 1
                                break
                            time.sleep(delay * (attempt + 1))
                with (tables / "download_attempts.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(event, default=str) + "\n")
                LOG.info("%s: %s", event["path"], event["status"])
                if event["status"] == "failed":
                    LOG.error("%s", event["error"])
                    if any(token in event["error"].lower() for token in ("403", "429", "forbidden", "captcha", "cloudflare", "blocked")):
                        LOG.error("Stopping collection after access restriction; no bypass attempted")
                        return failed
    return failed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/settings.yaml")
    parser.add_argument("--overwrite", action="store_true", help="Replace exports, retaining hash-verified backups")
    parser.add_argument("--limit", type=int, help="Maximum number of configured tables to attempt")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    cfg = load_config(args.config)
    failed = collect(cfg, args.overwrite, args.limit)
    inspection_failed = inspect(cfg)
    raise SystemExit(int(bool(failed or inspection_failed)))


if __name__ == "__main__":
    main()
