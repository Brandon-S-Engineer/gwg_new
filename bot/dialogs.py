"""Detección y descarte de diálogos inesperados del juego."""

import time

from . import input as inp
from . import vision
from .config import ITEMS_DIR

CONN_ERROR = ITEMS_DIR / "conn_error.png"
CONN_ERROR_OK = ITEMS_DIR / "conn_error_ok.png"
CONN_ERROR_THRESHOLD = 0.85


class ConnErrorDetected(Exception):
    pass


def check_conn_error() -> bool:
    """Si aparece el diálogo de error de conexión, clickea OK. True si lo hubo."""
    if not vision.is_present(CONN_ERROR, threshold=CONN_ERROR_THRESHOLD):
        return False
    print("[dialogs] error de conexión detectado, clickeando OK...")
    ok = vision.find(CONN_ERROR_OK, threshold=CONN_ERROR_THRESHOLD)
    if ok:
        inp.click(ok)
    else:
        print("[dialogs] botón OK no encontrado, ignorando")
        return False
    time.sleep(0.5)
    return True


def sleep_safe(duration: float, interval: float = 2.0) -> None:
    """Sleep que revisa conn_error cada `interval` segundos.

    Si detecta el error lo descarta y lanza ConnErrorDetected para que el loop
    pueda reiniciar la iteración limpiamente.
    """
    elapsed = 0.0
    while elapsed < duration:
        chunk = min(interval, duration - elapsed)
        time.sleep(chunk)
        elapsed += chunk
        if check_conn_error():
            raise ConnErrorDetected()
