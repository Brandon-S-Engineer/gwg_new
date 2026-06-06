"""Estado del Trading Post.

El TP tarda un tiempo VARIABLE en cargar tras abrirlo (a veces bastante).
`tp_ready.png` es un icono que solo aparece cuando el panel ya está listo.
`wait_ready()` espera por él antes de tocar botones del TP.

Reusar en TODO flujo de TP: vender, comprar, órdenes. Nunca clickear botones
del TP sin antes pasar por wait_ready().
"""

from . import vision
from .config import ITEMS_DIR
from .coords_loader import get_region

TP_READY = ITEMS_DIR / "tp_ready.png"
TP_READY_THRESHOLD = 0.85
TP_READY_TIMEOUT = 15.0  # a veces tarda bastante en cargar


def wait_ready(timeout: float = TP_READY_TIMEOUT) -> bool:
    """True cuando el TP terminó de cargar; False si no apareció en `timeout`."""
    spot = vision.wait_for(TP_READY, region=get_region("TP_AREA"),
                           timeout=timeout, threshold=TP_READY_THRESHOLD)
    if spot is None:
        print(f"[tp] no cargó en {timeout}s")
        return False
    return True
