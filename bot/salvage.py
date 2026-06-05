"""Botón "Accept" del diálogo de salvage (rune_crafter y silver_fed).

El diálogo puede salir a distintas alturas, siempre en la misma columna
(coords confirm: x~1811, y 1219-1415). En vez de clickear todas las coords
posibles a ciegas, matcheamos el template del botón y clickeamos donde
realmente está, igual que el "Consume All" de la suerte.

Nota: accept.png se captura con el picker. Por ahora vive en items/.
"""

from . import input as inp
from . import vision
from .config import ITEMS_DIR
from .regions import Region

ACCEPT = ITEMS_DIR / "accept.png"
# Texto fijo en botón claro; gris alcanza. Afinar con el max_val de vision.
ACCEPT_THRESHOLD = 0.85

# Columna donde aparece el Accept del salvage. Cubre x~1811 (ancho generoso)
# y el rango y de las coords confirm (1219-1415). Deja fuera el de
# arriba-derecha (salvage_stack_accept), que es otro caso.
ACCEPT_REGION = Region(1361, 1180, 900, 280)


def click_accept(timeout: float = 2.0) -> bool:
    """Busca el botón Accept en la columna y lo clickea. True si lo encontró."""
    btn = vision.wait_for(ACCEPT, region=ACCEPT_REGION,
                          timeout=timeout, threshold=ACCEPT_THRESHOLD)
    if btn:
        inp.click(btn)
        return True
    print("[salvage] botón Accept no encontrado en la columna")
    return False
