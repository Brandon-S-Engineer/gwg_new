"""Setup inicial: arrastrar banco al costado y activar filtros de texto.

Correr antes del loop principal (una vez por sesión):

    from bot.routines import setup
    setup.drag_bank()
    setup.filter_inventory()
    setup.filter_bank()

Coordenadas necesarias (agregar con el picker):
    bank_title      - barra de título del banco (donde aparece siempre, centro)
    bank_target     - destino del drag (costado derecho)
    inventory_filter - campo de texto del filtro del inventario
    bank_filter      - campo de texto del filtro del banco
"""

import time

from .. import input as inp
from .. import schedule
from ..coords_loader import get_point


def drag_bank():
    """Arrastrar la ventana del banco desde donde aparece (centro) al costado."""
    inp.drag(get_point("bank_title"), get_point("bank_target"))
    time.sleep(schedule.SETUP_AFTER_DRAG)


def filter_inventory():
    """Escribir 'luck' en el filtro del inventario."""
    import keyboard as _kb
    inp.click(get_point("inventory_filter"))
    time.sleep(0.15)
    _kb.send("ctrl+a")
    time.sleep(0.05)
    _kb.send("delete")
    _kb.write("luck")
    time.sleep(schedule.SETUP_AFTER_FILTER)


def filter_bank():
    """Escribir 'unidentified' en el filtro del banco."""
    import keyboard as _kb
    inp.click(get_point("bank_filter"))
    time.sleep(0.15)
    _kb.send("ctrl+a")
    time.sleep(0.05)
    _kb.send("delete")
    _kb.write("unidentified")
    time.sleep(schedule.SETUP_AFTER_FILTER)
