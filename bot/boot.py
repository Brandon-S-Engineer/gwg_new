"""Pasos previos a cualquier rutina: dar foco al juego."""

import time

from . import config
from . import input as inp


def focus_game(wait_seconds: float = 0.5) -> None:
    """Click medio-izquierda para sacar el foco de CMD y devolverlo al juego."""
    point = (200, config.SCREEN_HEIGHT // 2)
    print(f"[boot] focus click {point}")
    inp.click(point)
    time.sleep(wait_seconds)
