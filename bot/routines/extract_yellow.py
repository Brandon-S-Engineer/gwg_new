"""Procesar Unidentified Gear AMARILLO (rare) con el Upgrade Extractor.

Distinto de fase1 (greens): antes de hacer salvage se le extrae el
sigil/rune a CADA uno de los ~250 items del stack (sin destruirlo), lo que
sube mucho la ganancia por stack (~54.5 vs ~4.77 de un green). Este módulo
es independiente de phase1_salvage_greens: no lo importa, no lo llama, no
comparte constantes de timing/offsets con él — solo puede reusar imágenes
que son literalmente el mismo botón en el juego (use_all.png,
accept_salvage.png), tal como acordamos.

Pipeline completo:

  1. Identificar: igual idea que fase1 (inventario, con fallback a banco),
     pero buscando el ícono amarillo (yellow_gear.png).
  2. Barrer la grilla fija de inventario (slot_1..250) arrastrando
     cada slot a la ventana del Upgrade Extractor. Si sale el botón
     'Extract' (por imagen) se clickea; si no aparece en el timeout corto,
     ese slot no tenía upgrade (o estaba vacío) — se sigue al siguiente.
     OJO: acá NO se puede cortar en el primer miss como hace exotics.py,
     porque un miss es ambiguo (slot vacío O item sin upgrade) — se barren
     los 250 siempre. Esto deja sigils/runes sueltos mezclados con la
     armadura/arma ya sin upgrade.
  3. Separar: filtrar inventario por 'rune', guardar todo al banco con
     doble-click en las 2 'zonas' conocidas (cada bolsa compacta los
     matches filtrados en el mismo slot visual — doble-click ahí las veces
     que haga falta; clickear un slot vacío/filtrado-sin-match no hace nada
     en el juego, así que un tope de pasadas generoso es seguro). Repetir
     con 'sigil'.
  4. Salvage del resto (la armadura/arma ya pelada, ahora son rares
     comunes): reusa phase3_salvage_rares.run() TAL CUAL, sin tocarlo.
  5. Traer runes/sigils de vuelta: filtrar el BANCO por 'rune'/'sigil',
     doble-click en la zona del banco hasta vaciar cada uno.
  6. Salvage de runes/sigils con copper_fed (20x más barato que silver_fed;
     el resultado es idéntico para upgrades — investigado por el usuario).
     copper_fed tiene la misma opción bulk "salvage rares" que silver_fed/
     rune_crafter (copper_fed_salvage_rare): right-click al kit → click en
     la opción → Accept. Nada de armar cursor ni barrer slots acá.
  7. Reponer filtros normales (setup.restore_bank_filter) + compactar.

Coordenadas necesarias (agregar/calibrar con el picker, placeholders ya
puestos):
    upgrade_extractor_window - punto donde soltar el drag (la ventana del
        Upgrade Extractor)
    copper_fed, copper_fed_salvage_rare - kit barato, mismo patrón bulk que
        silver_fed/silver_fed_salvage_rare en phase3_salvage_rares.py
    rune_sigil_inv_zone_1, rune_sigil_inv_zone_2 - slot donde se compactan
        los matches filtrados en el INVENTARIO (2 bolsas — ~23 clicks en la
        1, ~12 en la 2, según lo medido; los topes son ajustables)
    rune_sigil_bank_zone_1 - igual pero del lado del BANCO, al traerlos de
        vuelta (si hace falta una 2da zona acá también, se agrega igual
        que se hizo con sell_top_confirm_2)
    slot_1..250 - grilla completa del inventario, COMPARTIDA con
        exotics.py (mismo menú, mismas posiciones — exotics solo usa
        slot_1..20 de esta misma lista). Solo se usa para el drag al
        extractor (paso 2); el salvage con copper_fed (paso 6) es bulk,
        no necesita slots.

Región necesaria:
    EXTRACT_WINDOW_REGION - caja donde aparece el botón 'Extract' cerca de
        upgrade_extractor_window

Items necesarios (capturar con el picker):
    yellow_gear - ícono del unidentified gear amarillo (igual idea que
        green.png pero para rare)
    extract_button - botón 'Extract' de la ventana del Upgrade Extractor

Reusa sin capturar de nuevo (mismo botón real en el juego):
    use_all.png (fase1) - identificar
    salvage.click_accept() (bot/salvage.py) - Accept del salvage bulk con
        copper_fed, mismo diálogo que usan fase1/fase3
"""

import time

from .. import config
from .. import dialogs
from .. import input as inp
from .. import salvage
from .. import schedule
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_point, get_region
from ..regions import Region
from . import phase3_salvage_rares, setup, store_luck
from .phase1_salvage_greens import USE_ALL, USE_ALL_THRESHOLD

YELLOW_GEAR = ITEMS_DIR / "yellow_gear.png"
YELLOW_THRESHOLD = 0.85

EXTRACT_BUTTON = ITEMS_DIR / "extract_button.png"
EXTRACT_BUTTON_THRESHOLD = 0.85

MAX_SLOTS = 250
# slot_1..250: grilla compartida con exotics.py (mismo menú de inventario,
# exotics solo calibró/usa las primeras 20 posiciones de esta misma lista).
SLOT_NAMES = [f"slot_{i}" for i in range(1, MAX_SLOTS + 1)]

# Sacar el cursor del item hacia el menú: quita el tooltip de hover. Mismo
# truco que fase1/exotics, valores propios (independientes) por si hace
# falta ajustar uno sin tocar el otro.
IDENTIFY_MENU_DISMISS_OFFSET = (16, 88)
IDENTIFY_MENU_REGION_DX = -10
IDENTIFY_MENU_REGION_DY = 0
IDENTIFY_MENU_REGION_W = 500
IDENTIFY_MENU_REGION_H = 360

SEPARATE_INV_ZONES = ["rune_sigil_inv_zone_1", "rune_sigil_inv_zone_2"]
RETRIEVE_BANK_ZONES = ["rune_sigil_bank_zone_1"]

# Tiempos centralizados en schedule.py para calibrarlos en un solo lugar.
SLEEP_BEFORE_RIGHT_CLICK = schedule.EXTRACT_BEFORE_RIGHT_CLICK
SLEEP_AFTER_RIGHT_CLICK = schedule.EXTRACT_AFTER_RIGHT_CLICK
SLEEP_HOVER_USE_ALL = schedule.EXTRACT_HOVER_USE_ALL
SLEEP_AFTER_IDENTIFY = schedule.EXTRACT_AFTER_IDENTIFY
SLEEP_AFTER_BANK_DOUBLECLICK = schedule.EXTRACT_AFTER_BANK_DOUBLECLICK
SLEEP_AFTER_DRAG = schedule.EXTRACT_AFTER_DRAG
SLEEP_AFTER_EXTRACT_CLICK = schedule.EXTRACT_AFTER_EXTRACT_CLICK
SLEEP_AFTER_ZONE_DOUBLECLICK = schedule.EXTRACT_AFTER_ZONE_DOUBLECLICK
SLEEP_AFTER_KIT_RIGHT_CLICK = schedule.EXTRACT_AFTER_KIT_RIGHT_CLICK
SLEEP_AFTER_KIT_OPTION = schedule.EXTRACT_AFTER_KIT_OPTION


# ============================================================
# 1. Identificar
# ============================================================

def _identify_menu_region(point: tuple[int, int]) -> Region:
    x = max(0, point[0] + IDENTIFY_MENU_REGION_DX)
    y = max(0, point[1] + IDENTIFY_MENU_REGION_DY)
    w = min(IDENTIFY_MENU_REGION_W, config.SCREEN_WIDTH - x)
    h = min(IDENTIFY_MENU_REGION_H, config.SCREEN_HEIGHT - y)
    return Region(x, y, w, h)


def find_yellow_in_inventory() -> tuple[int, int] | None:
    return vision.find(YELLOW_GEAR, region=get_region("INVENTORY_AREA"),
                       threshold=YELLOW_THRESHOLD)


def find_yellow_in_bank() -> tuple[int, int] | None:
    return vision.find(YELLOW_GEAR, region=get_region("BANK_AREA"),
                       threshold=YELLOW_THRESHOLD)


def use_all_at(point: tuple[int, int]) -> bool:
    inp.move_to(point)
    time.sleep(SLEEP_BEFORE_RIGHT_CLICK)
    inp.right_click(point)
    time.sleep(SLEEP_AFTER_RIGHT_CLICK)
    inp.move_rel(*IDENTIFY_MENU_DISMISS_OFFSET)
    time.sleep(SLEEP_HOVER_USE_ALL)

    btn = vision.wait_for(USE_ALL, region=_identify_menu_region(point),
                          timeout=1.5, threshold=USE_ALL_THRESHOLD)
    if not btn:
        print("[extract_yellow] no apareció 'Use All', abortando (no clickeo a ciegas)")
        return False
    inp.click(btn)
    return True


def identify_one() -> bool:
    """Identifica UN stack de yellow gear (inventario, o banco→inventario
    si no hay). True si identificó algo."""
    print("[extract_yellow] buscando yellow gear en inventario...")
    spot = find_yellow_in_inventory()

    if not spot:
        print("[extract_yellow] no hay en inv, buscando en banco...")
        bank_spot = find_yellow_in_bank()
        if not bank_spot:
            print("[extract_yellow] no hay yellow gear ni en inv ni en banco.")
            return False
        print(f"[extract_yellow] yellow en banco {bank_spot}, doble-click...")
        inp.double_click(bank_spot)
        time.sleep(SLEEP_AFTER_BANK_DOUBLECLICK)
        spot = find_yellow_in_inventory()
        if not spot:
            print("[extract_yellow] tras mover, no apareció en inv. Aborto.")
            return False

    print(f"[extract_yellow] yellow gear en inv {spot}, Use All...")
    if not use_all_at(spot):
        return False
    dialogs.sleep_safe(SLEEP_AFTER_IDENTIFY)
    return True


# ============================================================
# 2. Drag al Upgrade Extractor
# ============================================================

def _extract_at(slot_name: str) -> bool:
    """Arrastra el item del slot a la ventana del extractor. True si salió
    'Extract' y se clickeó; False si no apareció (slot vacío o item sin
    upgrade — ambos casos válidos, no es error)."""
    slot_point = get_point(slot_name)
    window_point = get_point("upgrade_extractor_window")
    inp.drag(slot_point, window_point)
    time.sleep(SLEEP_AFTER_DRAG)

    btn = vision.wait_for(EXTRACT_BUTTON, region=get_region("EXTRACT_WINDOW_REGION"),
                          timeout=1.0, threshold=EXTRACT_BUTTON_THRESHOLD)
    if not btn:
        return False
    inp.click(btn)
    time.sleep(SLEEP_AFTER_EXTRACT_CLICK)
    return True


def extract_all() -> int:
    """Barre TODA la grilla (250 slots), siempre completa: acá un miss es
    ambiguo (vacío vs. sin upgrade) así que no se puede cortar temprano
    como en exotics.py. Devuelve cuántos upgrades extrajo."""
    store_luck.compact()
    count = 0
    for name in SLOT_NAMES:
        if _extract_at(name):
            count += 1
    print(f"[extract_yellow] {count} upgrade(s) extraído(s) de {MAX_SLOTS} slots")
    return count


def identify_and_extract() -> int:
    """Identifica UN stack (inventario, o banco→inventario si no hay —
    misma lógica que fase1 con los greens) y barre los 250 slots al
    Upgrade Extractor. Para ahí: no separa runes/sigils ni hace salvage.
    Para probar el pipeline hasta el extractor antes de calibrar el resto.
    `py -m bot extract_yellow identify_extract`"""
    if not identify_one():
        return 0
    return extract_all()


# ============================================================
# 3. Separar runes/sigils al banco
# ============================================================

def _store_zone(zone_point_name: str, max_passes: int) -> None:
    """Doble-click repetido en la misma posición: cada guardado hace que el
    siguiente match (mismo filtro) se acomode ahí mismo. Clickear una
    posición sin match no hace nada en el juego, así que un tope generoso
    es seguro (como mucho pierde un par de segundos de más)."""
    point = get_point(zone_point_name)
    for _ in range(max_passes):
        inp.double_click(point)
        time.sleep(SLEEP_AFTER_ZONE_DOUBLECLICK)


def store_filtered(filter_text: str) -> None:
    """Filtra el inventario por `filter_text` ('rune' o 'sigil') y guarda
    todo al banco, doble-click en las 2 zonas conocidas."""
    setup.filter_inventory(filter_text)
    zones = [
        (SEPARATE_INV_ZONES[0], schedule.EXTRACT_ZONE1_MAX_PASSES),
        (SEPARATE_INV_ZONES[1], schedule.EXTRACT_ZONE2_MAX_PASSES),
    ]
    for zone_name, max_passes in zones:
        print(f"[extract_yellow] guardando '{filter_text}' en {zone_name}...")
        _store_zone(zone_name, max_passes)


def separate_runes_and_sigils() -> None:
    store_filtered("rune")
    store_filtered("sigil")


# ============================================================
# 5. Traer runes/sigils de vuelta del banco
# ============================================================

def retrieve_filtered(filter_text: str) -> None:
    setup.filter_bank(filter_text)
    for zone_name in RETRIEVE_BANK_ZONES:
        print(f"[extract_yellow] trayendo '{filter_text}' de {zone_name}...")
        _store_zone(zone_name, schedule.EXTRACT_BANK_ZONE1_MAX_PASSES)


def retrieve_runes_and_sigils() -> None:
    retrieve_filtered("rune")
    retrieve_filtered("sigil")


# ============================================================
# 6. Salvage de runes/sigils con copper_fed
# ============================================================
# copper_fed_salvage_rare (renombrado de un copper_fed_salvage_common ya
# calibrado) es la MISMA clase de opción bulk que silver_fed_salvage_rare
# (fase3) y rune_crafter_salvage_green (fase1): right-click al kit → click
# en la opción → Accept. Nada de armar cursor ni barrer slots.

def salvage_runes_and_sigils() -> bool:
    inp.right_click(get_point("copper_fed"))
    time.sleep(SLEEP_AFTER_KIT_RIGHT_CLICK)
    inp.click(get_point("copper_fed_salvage_rare"))
    time.sleep(SLEEP_AFTER_KIT_OPTION)
    return salvage.click_accept()


# ============================================================
# Orquestador
# ============================================================

def run() -> bool:
    print("[extract_yellow] procesando stack de yellow unidentified gear...")
    if not identify_one():
        return False
    extract_all()
    separate_runes_and_sigils()
    phase3_salvage_rares.run()
    retrieve_runes_and_sigils()
    salvage_runes_and_sigils()
    setup.restore_bank_filter()
    store_luck.compact()
    print("[extract_yellow] OK")
    return True
