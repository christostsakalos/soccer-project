import json
import sys
from types import SimpleNamespace
import pandas as pd
from football_similarity.download_data import collect
from football_similarity.inspect_data import sha256


def test_collect_skip_backup_and_unsupported(tmp_path, monkeypatch):
    cfg = {"data": {"leagues": ["ENG"], "seasons": ["2425"], "categories": ["standard"]}, "paths": {key: tmp_path / key for key in ("raw", "processed", "results")}}
    monkeypatch.setitem(sys.modules, "soccerdata", SimpleNamespace())
    monkeypatch.setattr("football_similarity.download_data.importlib.metadata.version", lambda _: "2026.43.0")
    calls = []
    class Reader:
        def __init__(self, **kwargs):
            calls.append(kwargs)
        def read_player_season_stats(self, stat_type):
            return pd.DataFrame({"player": ["A"], "minutes": [90]})
    monkeypatch.setattr("football_similarity.download_data.reader_class", lambda _: Reader)
    assert collect(cfg) == 0
    path = cfg["paths"]["raw"] / "2425/ENG/standard.csv"
    original = sha256(path)
    assert collect(cfg) == 0
    assert len(calls) == 1
    assert collect(cfg, overwrite=True) == 0
    assert sha256(path.with_name(f"standard.csv.{original}.bak")) == original
    cfg["data"]["categories"] = ["passing"]
    assert collect(cfg) == 1
    assert len(calls) == 2
    log = cfg["paths"]["results"] / "tables/download_attempts.jsonl"
    assert json.loads(log.read_text().splitlines()[-1])["status"] == "unsupported"
