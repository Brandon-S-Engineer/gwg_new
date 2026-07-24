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

Región e items necesarios (agregar con el picker) para confirmar que el
click en 'banco' realmente prendió (ver ensure_bank_tab):
    BANK_TAB_REGION - caja que cubre la zona donde se puede leer tanto
                      'Bank Tab' (ya en el banco) como 'Refinement' (el
                      dropdown de categoría de artificing, si todavía
                      estamos ahí) — misma región, sirve para las dos.
    bank_tab   - recorte del texto/ícono que solo aparece con el banco
                 realmente abierto.
    refinement - recorte de 'Refinement' (dropdown de artificing). Si
                 esto sigue viéndose después de clickear 'banco', el
                 click no prendió (el craft todavía no soltó el control).
"""

import time

from .. import input as inp
from .. import schedule
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_point, get_region

BANK_TAB = ITEMS_DIR / "bank_tab.png"
REFINEMENT = ITEMS_DIR / "refinement.png"
BANK_TAB_THRESHOLD = 0.85
REFINEMENT_THRESHOLD = 0.85


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


def filter_inventory(text: str = "unid"):
    """text por defecto alcanza con 'unid', no hay items con nombre parecido.
    extract_yellow.py pasa 'rune'/'sigil' para separar upgrades."""
    inp.click(get_point("inventory_filter"))
    time.sleep(0.15)
    inp.clear_field()
    inp.type_text(text)
    time.sleep(schedule.SETUP_AFTER_FILTER)


def filter_bank(text: str = "luck"):
    """extract_yellow.py pasa 'rune'/'sigil' para traerlos de vuelta."""
    inp.click(get_point("bank_filter"))
    time.sleep(0.15)
    inp.clear_field()
    inp.type_text(text)
    time.sleep(schedule.SETUP_AFTER_FILTER)


def ensure_bank_tab():
    """Click banco + CONFIRMAR por imagen que realmente abrió. El click a
    veces no prende: si el craft de luck todavía no soltó el control (una
    confirmación temprana falsa en _wait_for_luck_zero), seguimos parados
    en artificing y el click se pierde — reintenta hasta ver 'bank_tab' o
    agotar el timeout, en vez de asumir a ciegas que ya estamos en banco."""
    inp.click(get_point("banco"))
    time.sleep(schedule.SETUP_AFTER_BANK_TAB)

    if not (vision.is_calibrated(BANK_TAB) and vision.is_calibrated(REFINEMENT)):
        return  # bank_tab.png/refinement.png todavía son el placeholder:
                # sin capturas reales no hay nada que confirmar

    deadline = time.time() + schedule.BANK_TAB_CONFIRM_TIMEOUT
    while time.time() < deadline:
        region = get_region("BANK_TAB_REGION")
        if vision.is_present(BANK_TAB, region=region, threshold=BANK_TAB_THRESHOLD):
            return
        if vision.is_present(REFINEMENT, region=region, threshold=REFINEMENT_THRESHOLD):
            print("[setup] 'banco' no prendió (todavía en artificing), reintento click...")
            inp.click(get_point("banco"))
            time.sleep(schedule.SETUP_AFTER_BANK_TAB)
            continue
        time.sleep(schedule.BANK_TAB_RETRY_POLL)
    print("[setup] no pude confirmar que 'banco' abrió, sigo igual")


def restore_bank_filter():
    """craft_essence y exotics (cada 30 iteraciones) cambian de pestaña
    banco/artificing y navegan el TP, dejando los filtros en otra cosa.
    Repite los mismos pasos que el final de run() para dejarlos como al
    principio."""
    ensure_bank_tab()
    filter_inventory()
    filter_bank()


def position_bank_for_calibration():
    """El banco no retoma su posición solo al abrirse: hace falta este drag
    para dejarlo siempre en el mismo lugar. Útil para calibrar a mano
    coordenadas que dependen de esa posición (ej. rune_sigil_bank_zone_1 en
    extract_yellow.py) — abrí el banco en el juego primero, después corré
    esto. `py -m bot setup position`"""
    drag_bank()
    ensure_bank_tab()


def run():
    drag_bank()        # primero acomodar: el punto 'banco' asume la ventana ya al costado
    ensure_bank_tab()
    open_windows()
    filter_inventory()
    filter_bank()
