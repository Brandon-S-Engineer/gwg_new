"""Setup inicial: se ejecuta una vez cuando arranca el loop.

Orden:
  1. drag_bank()       - arrastra el banco al costado (primero: 'banco' asume esa posición)
  2. click en la pestaña banco (por si quedó en artificing; así aseguramos)
  3. open_windows()    - presiona i / o / m para abrir inventario, TP y mapa
  4. filter_inventory() - escribe 'unidentified' en el filtro del inventario
  5. filter_bank()      - escribe 'luck' en el filtro del banco

Coordenadas necesarias (agregar con el picker):
    banco            - pestaña del banco (asegurar al iniciar)
    bank_title       - barra de título del banco (donde aparece, centro)
    bank_target      - destino del drag (costado derecho)
    inventory_filter - campo de texto del filtro del inventario
    bank_filter      - campo de texto del filtro del banco
    inventory_close  - botón X del inventario (cerrar antes de abrir con 'i',
                        que es un toggle: si ya estaba abierto de una corrida
                        anterior, 'i' lo cerraría en vez de abrirlo)
"""

import time

from .. import input as inp
from .. import schedule
from ..coords_loader import get_point


def drag_bank():
    inp.drag(get_point("bank_title"), get_point("bank_target"))
    time.sleep(schedule.SETUP_AFTER_DRAG)


def open_windows():
    """'i' es un toggle: si el inventario ya estaba abierto de una corrida
    anterior (el loop se reinicia sin cerrar el juego), presionarlo lo
    CIERRA en vez de abrirlo, y filter_inventory() clickea sobre nada.
    Por eso primero se cierra a la fuerza con inventory_close (botón X, no
    toggle) para arrancar siempre desde "cerrado" — mismo truco que usaba
    el bot viejo en open_menus()."""
    import keyboard as _kb
    inp.click(get_point("inventory_close"))
    time.sleep(schedule.SETUP_AFTER_KEYPRESS)
    _kb.press_and_release("i")
    time.sleep(schedule.SETUP_AFTER_KEYPRESS)
    _kb.press_and_release("o")
    time.sleep(schedule.SETUP_AFTER_KEYPRESS)
    _kb.press_and_release("m")
    time.sleep(schedule.SETUP_AFTER_KEYPRESS)


def filter_inventory():
    inp.click(get_point("inventory_filter"))
    time.sleep(0.15)
    inp.clear_field()
    inp.type_text("unidentified")
    time.sleep(schedule.SETUP_AFTER_FILTER)


def filter_bank():
    inp.click(get_point("bank_filter"))
    time.sleep(0.15)
    inp.clear_field()
    inp.type_text("luck")
    time.sleep(schedule.SETUP_AFTER_FILTER)


def ensure_bank_tab():
    # Puede haber quedado en la pestaña artificing: click banco para asegurar.
    inp.click(get_point("banco"))
    time.sleep(schedule.SETUP_AFTER_BANK_TAB)


def run():
    drag_bank()        # primero acomodar: el punto 'banco' asume la ventana ya al costado
    ensure_bank_tab()
    open_windows()
    filter_inventory()
    filter_bank()
