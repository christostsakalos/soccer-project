"""Configuration and safe output paths."""
from pathlib import Path
import re
import yaml


def component(value: str) -> str:
    """Reject traversal and Windows-unsafe names instead of silently renaming."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _.-]*", value) or value.endswith((".", " ")) or value.upper().split(".")[0] in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        raise ValueError(f"Unsafe path component: {value!r}")
    return value


def load_config(path: str | Path) -> dict:
    path = Path(path).resolve()
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    for field in ("leagues", "seasons", "categories"):
        values = cfg["data"][field]
        if not isinstance(values, list) or not values:
            raise ValueError(f"data.{field} must be a nonempty list")
        for value in values:
            component(value)
    root = path.parent.parent
    for key in ("raw", "processed", "results"):
        target = (root / cfg["paths"][key]).resolve()
        if not target.is_relative_to(root) or target == root:
            raise ValueError(f"paths.{key} must be inside the project")
        cfg["paths"][key] = target
    return cfg
