"""Carga coords/<wxh>.json y expone puntos y regiones por nombre."""

import json
from functools import lru_cache

from .config import COORDS_PATH
from .regions import Region


@lru_cache(maxsize=1)
def _load() -> dict:
    return json.loads(COORDS_PATH.read_text(encoding="utf-8"))


def _main_view() -> dict:
    return _load()["types"]["main_view"]


def get_point(name: str) -> tuple[int, int]:
    for p in _main_view()["points"]:
        if p["name"] == name:
            return (int(p["x"]), int(p["y"]))
    raise KeyError(f"punto no encontrado: {name}")


def get_region(name: str) -> Region:
    for r in _main_view()["regions"]:
        if r["name"] == name:
            return Region(int(r["x"]), int(r["y"]), int(r["w"]), int(r["h"]))
    raise KeyError(f"región no encontrada: {name}")
