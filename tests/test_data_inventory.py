import json
from pathlib import Path
import pandas as pd
import pytest
from football_similarity.config import component, load_config
from football_similarity.inspect_data import inspect_file, read_raw, run, sha256


@pytest.mark.parametrize("name", ["../escape", "a/b", "a\\b", "CON", "a:", "..", "trailing."])
def test_unsafe_components(name):
    with pytest.raises(ValueError):
        component(name)


def test_inventory_missing_duplicates_transfer_and_immutability(tmp_path):
    path = tmp_path / "2024-2025" / "ENG-Premier League" / "standard.csv"
    path.parent.mkdir(parents=True)
    path.write_text("player,team,minutes\nA,2 squads,90\nA,Club,\nA,Club,\n", encoding="utf-8")
    before = sha256(path)
    summary, features = inspect_file(path, tmp_path)
    assert summary["rows"] == 3
    assert summary["missing_cells"] == 2
    assert summary["exact_duplicate_rows"] == 1
    assert summary["candidate_key_duplicate_rows"] == 1
    assert summary["aggregate_team_rows"] == 1
    assert features[2]["missing_count"] == 2
    assert sha256(path) == before


def test_multiindex_roundtrip(tmp_path):
    path = tmp_path / "keeper.csv"
    frame = pd.DataFrame([[1, 2]], columns=pd.MultiIndex.from_tuples([("Playing Time", "Min"), ("Performance", "GA")]), index=pd.MultiIndex.from_tuples([("ENG", "2425", "Club", "Player")], names=["league", "season", "team", "player"]))
    frame.to_csv(path)
    path.with_suffix(".metadata.json").write_text(json.dumps({"header_rows": 2, "index_name_row": True, "index_levels": 4}))
    loaded, status = read_raw(path)
    assert len(loaded) == 1
    assert loaded.columns[-1] == ("Performance", "GA")
    assert status == "metadata"
    summary, _ = inspect_file(path, tmp_path)
    assert "player" in summary["candidate_key_columns"]


def test_empty_inventory_and_corrupt_csv(tmp_path):
    cfg = {"data": {"leagues": ["ENG"], "seasons": ["2425"], "categories": ["standard"]}, "paths": {key: tmp_path / key for key in ("raw", "processed", "results")}}
    assert run(cfg) == 0
    report = cfg["paths"]["results"] / "tables" / "dataset_summary.csv"
    assert len(pd.read_csv(report)) == 0
    (cfg["paths"]["raw"] / "broken.csv").write_text('a,b\n"unterminated')
    assert run(cfg) == 1
    assert pd.read_csv(report).iloc[0]["status"] == "inspection_failed"


def test_config_rejects_outside_paths(tmp_path):
    folder = tmp_path / "config"
    folder.mkdir()
    file = folder / "settings.yaml"
    file.write_text('data: {leagues: [ENG], seasons: ["2425"], categories: [standard]}\npaths: {raw: ../outside, processed: data/processed, results: results}')
    with pytest.raises(ValueError, match="inside"):
        load_config(file)
