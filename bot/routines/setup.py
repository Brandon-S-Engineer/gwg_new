"""Setup inicial: se ejecuta una vez cuando arranca el loop.

Orden:
  1. drag_bank()       - arrastra el banco al costado
  2. open_windows()    - presiona i / o / m para abrir inventario, TP y mapa
  3. filter_inventory() - escribe 'luck' en el filtro del inventario
  4. filter_bank()      - escribe 'unidentified' en el filtro del banco

Coordenadas necesarias (agregar con el picker):
    bank_title       - barra de título del banco (donde aparece, centro)
    bank_target      - destino del drag (costado derecho)
    inventory_filter - campo de texto del filtro del inventario
    bank_filter      - campo de texto del filtro del banco
"""

import time

from .. import input as inp
from .. import schedule
from ..coords_loader import get_point


def drag_bank():
    inp.drag(get_point("bank_title"), get_point("bank_target"))
    time.sleep(schedule.SETUP_AFTER_DRAG)


def open_windows():
    import keyboard as _kb
    _kb.press_and_release("i")
    time.sleep(schedule.SETUP_AFTER_KEYPRESS)
    _kb.press_and_release("o")
    time.sleep(schedule.SETUP_AFTER_KEYPRESS)
    _kb.press_and_release("m")
    time.sleep(schedule.SETUP_AFTER_KEYPRESS)


def filter_inventory():
    import keyboard as _kb
    inp.click(get_point("inventory_filter"))
    time.sleep(0.15)
    _kb.send("ctrl+a")
    time.sleep(0.05)
    _kb.send("delete")
    _kb.write("luck")
    time.sleep(schedule.SETUP_AFTER_FILTER)


def filter_bank():
    import keyboard as _kb
    inp.click(get_point("bank_filter"))
    time.sleep(0.15)
    _kb.send("ctrl+a")
    time.sleep(0.05)
    _kb.send("delete")
    _kb.write("unidentified")
    time.sleep(schedule.SETUP_AFTER_FILTER)


def run():
    drag_bank()
    open_windows()
    filter_inventory()
    filter_bank()
