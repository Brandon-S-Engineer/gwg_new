"""Pasos previos a cualquier rutina: enfocar la ventana del juego."""

import time

from . import input as inp
from .coords_loader import get_point


def focus_game(wait_seconds: float = 3.0) -> None:
    """Click en `full_screen` para activar la ventana del juego, luego espera."""
    point = get_point("full_screen")
    print(f"[boot] click full_screen {point}")
    inp.click(point)
    time.sleep(wait_seconds)
