"""Pasos previos a cualquier rutina: dar foco al juego."""

import time

from . import input as inp
from .coords_loader import get_point


def focus_game(wait_seconds: float = 0.5) -> None:
    """Un click en `full_screen` para sacar el foco de CMD y devolverlo al juego.

    El punto `full_screen` ahora debe apuntar a una zona segura DENTRO de la
    ventana del juego (no a la barra de título de VMware, eso ya no aplica
    porque el bot corre dentro de la VM).
    """
    point = get_point("full_screen")
    print(f"[boot] focus click {point}")
    inp.click(point)
    time.sleep(wait_seconds)
