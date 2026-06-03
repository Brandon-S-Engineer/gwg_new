"""Pasos previos a cualquier rutina: enfocar la ventana del juego."""

import time

from . import input as inp
from .coords_loader import get_point


def focus_game(wait_seconds: float = 3.0) -> None:
    """Click en `full_screen` para activar la ventana del juego, luego espera.

    Hacemos 2 clicks: el primero a veces solo le da foco a la ventana,
    el segundo activa el botón.
    """
    point = get_point("full_screen")
    print(f"[boot] click full_screen {point} (x2)")
    inp.click(point)
    time.sleep(0.4)
    inp.click(point)
    time.sleep(wait_seconds)
