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
     Optimización: tras STATIC_AFTER_HITS (10) extracciones confirmadas
     por imagen, el botón 'Extract' deja de moverse (visto en la
     práctica) — de ahí en más se clickea directo en esa posición
     recordada, sin buscar por imagen ni esperar nada.
  3. Salvage de la armadura/arma con silver_fed (bulk, igual que fase3),
     pero CORTADO justo antes de que le toque a los sigils/runes: como no
     hay forma de saber el milisegundo exacto en que termina el gear y
     empieza el upgrade, se vigilan los últimos 9 slots (slot_242..250,
     donde sigils/runes suelen quedar clusterizados tras compactar)
     comparando screenshot antes/después. En cuanto cambian, se interrumpe
     el salvage cerrando y reabriendo inventario+mapa (cancela la acción
     en curso sin perder nada de lo ya salvageado).
  4. Salvage de lo que quedó (sigils/runes, y tal vez algún gear que no
     llegó a tocarse) con copper_fed — 20x más barato que silver_fed, el
     resultado es idéntico para upgrades (investigado por el usuario).
     Mismo patrón bulk que silver_fed/rune_crafter (copper_fed_salvage_rare):
     right-click al kit → click en la opción → Accept.
  5. Reponer filtros normales (setup.restore_bank_filter) + compactar.

Sin round-trip al banco: se probó separar runes/sigils al banco primero,
pero cortar el salvage caro a tiempo por imagen es más simple y más rápido
que todo ese ida y vuelta con filtros.

Coordenadas necesarias (agregar/calibrar con el picker, placeholders ya
puestos):
    upgrade_extractor_window - punto donde soltar el drag (la ventana del
        Upgrade Extractor)

Regiones necesarias:
    slot_1..250 - grilla completa del inventario, COMPARTIDA con
        exotics.py (mismo menú, mismas posiciones — exotics solo usa
        slot_1..20 de esta misma lista). Son REGIONES (cuadros chicos, no
        puntos): el centro se usa para el drag, y el cuadro completo para
        chequear si el item ahí está en la lista de ignorados.
    EXTRACT_WINDOW_REGION - caja donde aparece el botón 'Extract' cerca de
        upgrade_extractor_window

La frontera del paso 3 (BOUNDARY_REGIONS) reusa slot_242..250 directo del
grid — no hay una región aparte para eso, evita superponerse con el grid.

Items necesarios (capturar con el picker):
    yellow_gear - ícono del unidentified gear amarillo (igual idea que
        green.png pero para rare)
    extract_button - botón 'Extract' de la ventana del Upgrade Extractor
    ignore_1, ignore_2, ... - items que NUNCA tienen upgrade (anillos,
        amuletos, etc.): se detectan y se saltan sin arrastrarlos, sin
        límite de cuántos — extract_all() los descubre por nombre en el
        momento, agregar uno nuevo no toca código. _snapshot_inventory()
        guarda tools/calibration/<res>/main_view.png justo antes de
        arrancar el barrido (inventario ya identificado y abierto) para
        recortarlos de ahí con el picker, con calma, entre corridas.

Reusa sin capturar de nuevo (mismo botón/kit real en el juego):
    use_all.png (fase1) - identificar
    silver_fed, silver_fed_salvage_rare (fase3) - salvage bulk del gear
    copper_fed, copper_fed_salvage_rare - salvage bulk barato de upgrades
    salvage.click_accept() (bot/salvage.py) - Accept de ambos salvage bulk
"""

import time
from pathlib import Path

import numpy as np

from .. import config
from .. import dialogs
from .. import input as inp
from .. import salvage
from .. import schedule
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_point, get_region
from ..regions import Region
from . import setup, store_luck
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

# Los últimos 9 slots (242..250) del grid, reusados como zona frontera:
# sigils/runes suelen quedar clusterizados justo ahí tras compactar. Antes
# había regiones EXTRACT_BOUNDARY_1..5 aparte, pero se superponían con los
# slots reales del grid — se sacaron, esto usa directo slot_242..250 (más
# margen de reacción que las 5 de antes).
BOUNDARY_REGIONS = [f"slot_{i}" for i in range(242, 251)]

# Diferencia promedio de intensidad (0-255) entre screenshot antes/después
# de una zona para contarla como "cambió". El ícono salvageado desaparece
# del todo (queda vacío/otro fondo), así que el salto real es grande;
# valor conservador para no gatillar con ruido de compresión/animación.
BOUNDARY_CHANGE_THRESHOLD = 12.0

# Tiempos centralizados en schedule.py para calibrarlos en un solo lugar.
SLEEP_BEFORE_RIGHT_CLICK = schedule.EXTRACT_BEFORE_RIGHT_CLICK
SLEEP_AFTER_RIGHT_CLICK = schedule.EXTRACT_AFTER_RIGHT_CLICK
SLEEP_HOVER_USE_ALL = schedule.EXTRACT_HOVER_USE_ALL
SLEEP_AFTER_IDENTIFY = schedule.EXTRACT_AFTER_IDENTIFY
SLEEP_AFTER_BANK_DOUBLECLICK = schedule.EXTRACT_AFTER_BANK_DOUBLECLICK
SLEEP_AFTER_DRAG = schedule.EXTRACT_AFTER_DRAG
SLEEP_AFTER_EXTRACT_CLICK = schedule.EXTRACT_AFTER_EXTRACT_CLICK
SLEEP_AFTER_DIRECT_CLICK = schedule.EXTRACT_AFTER_DIRECT_CLICK
DRAG_HOLD = schedule.EXTRACT_DRAG_HOLD
BUTTON_TIMEOUT = schedule.EXTRACT_BUTTON_TIMEOUT
SLEEP_AFTER_KIT_RIGHT_CLICK = schedule.EXTRACT_AFTER_KIT_RIGHT_CLICK
SLEEP_AFTER_KIT_OPTION = schedule.EXTRACT_AFTER_KIT_OPTION
SLEEP_AFTER_INTERRUPT_CANCEL = schedule.EXTRACT_AFTER_INTERRUPT_CANCEL
SLEEP_AFTER_INTERRUPT_FIRST_M = schedule.EXTRACT_AFTER_INTERRUPT_FIRST_M
SLEEP_AFTER_INTERRUPT_KEYPRESS = schedule.EXTRACT_AFTER_INTERRUPT_KEYPRESS
BOUNDARY_POLL_INTERVAL = schedule.EXTRACT_BOUNDARY_POLL_INTERVAL
SALVAGE_TIMEOUT = schedule.EXTRACT_SALVAGE_TIMEOUT
BOUNDARY_CONFIRMATIONS = schedule.EXTRACT_BOUNDARY_CONFIRMATIONS
SLEEP_AFTER_COPPER_SALVAGE = schedule.EXTRACT_AFTER_COPPER_SALVAGE


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

# Tras esta cantidad de extracciones CONFIRMADAS por imagen, el botón
# 'Extract' deja de moverse (visto en la práctica): de ahí en más se
# clickea directo en esa posición, sin buscarlo por imagen ni esperar.
STATIC_AFTER_HITS = 10

# Items que NUNCA tienen upgrade (anillos, amuletos, etc.): se saltan sin
# arrastrarlos. Se descubren por NOMBRE en el momento (ignore_1.png,
# ignore_2.png, ...) — agregar uno nuevo con el picker no toca código.
IGNORE_THRESHOLD = 0.85

# Los templates capturados (~68x68) son MÁS GRANDES que el cuadro del slot
# (60x60): sin margen ni entran completos en la zona de búsqueda, así que
# el match no tiene dónde deslizarse para encontrar la mejor posición. Se
# busca en un cuadro más grande, centrado en el mismo punto — no hace
# falta que el slot esté pixel-perfect, con que el ítem quede adentro de
# esta zona alcanza. 80px = el espaciado real de la grilla, así da margen
# sin llegar a pisar el slot vecino.
IGNORE_CHECK_SIZE = 80


def _ignore_templates() -> list[Path]:
    return sorted(ITEMS_DIR.glob("ignore_*.png"))


def _ignore_search_region(slot_region: Region) -> Region:
    cx, cy = slot_region.center
    half = IGNORE_CHECK_SIZE // 2
    x = max(0, cx - half)
    y = max(0, cy - half)
    w = min(IGNORE_CHECK_SIZE, config.SCREEN_WIDTH - x)
    h = min(IGNORE_CHECK_SIZE, config.SCREEN_HEIGHT - y)
    return Region(x, y, w, h)


def _is_ignored(slot_region: Region, templates: list[Path]) -> bool:
    search = _ignore_search_region(slot_region)
    return any(vision.is_present(tpl, region=search, threshold=IGNORE_THRESHOLD)
               for tpl in templates)


def _snapshot_inventory() -> None:
    """Guarda un screenshot completo en el mismo archivo que usa el picker
    para 'main_view' (tools/calibration/<res>/main_view.png) — como si se
    apretara Ctrl+P ahí mismo. Se toma UNA vez, justo antes de arrancar el
    barrido (inventario ya identificado y abierto), para poder ir
    recortando ignore_N de esa captura real con calma, entre corridas."""
    from PIL import ImageGrab
    out_dir = config.PROJECT_ROOT / "tools" / "calibration" / config.RES_KEY
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "main_view.png"
    ImageGrab.grab().save(out_path, "PNG")
    print(f"[extract_yellow] snapshot guardado en {out_path}")


def _slot_center(slot_name: str) -> tuple[int, int]:
    return get_region(slot_name).center


def _extract_at(slot_name: str) -> tuple[int, int] | None:
    """Arrastra el item del slot a la ventana del extractor. Devuelve la
    posición del botón 'Extract' si salió y se clickeó; None si no apareció
    (slot vacío o item sin upgrade — ambos casos válidos, no es error).

    Este paso se repite hasta 250 veces por stack: cualquier segundo de
    sobra acá se multiplica mucho, así que va con timings propios más
    ajustados (DRAG_HOLD, BUTTON_TIMEOUT) en vez de los defaults genéricos
    de input.py."""
    slot_point = _slot_center(slot_name)
    window_point = get_point("upgrade_extractor_window")
    inp.drag(slot_point, window_point, hold_before=DRAG_HOLD)
    time.sleep(SLEEP_AFTER_DRAG)

    btn = vision.wait_for(EXTRACT_BUTTON, region=get_region("EXTRACT_WINDOW_REGION"),
                          timeout=BUTTON_TIMEOUT, threshold=EXTRACT_BUTTON_THRESHOLD)
    if not btn:
        return None
    inp.click(btn)
    time.sleep(SLEEP_AFTER_EXTRACT_CLICK)
    return btn


def _extract_at_direct(slot_name: str, button_point: tuple[int, int]) -> None:
    """Modo directo (botón ya estático): drag + click en la posición
    recordada, sin buscar por imagen — máxima velocidad. Si el slot no
    tenía upgrade, clickear ahí no hace nada (no hay botón real debajo)."""
    slot_point = _slot_center(slot_name)
    window_point = get_point("upgrade_extractor_window")
    inp.drag(slot_point, window_point, hold_before=DRAG_HOLD)
    inp.click(button_point)
    time.sleep(SLEEP_AFTER_DIRECT_CLICK)


def extract_all() -> int:
    """Barre TODA la grilla (250 slots), siempre completa: acá un miss es
    ambiguo (vacío vs. sin upgrade) así que no se puede cortar temprano
    como en exotics.py. Antes de dragear cada slot, chequea contra la
    lista de ignore_N (items que nunca tienen upgrade) y lo salta directo
    si matchea. Tras STATIC_AFTER_HITS confirmaciones por imagen cambia a
    modo directo (ver _extract_at_direct) para el resto del barrido.
    Devuelve cuántos upgrades extrajo (los de modo directo se cuentan como
    intento, ya no se verifican por imagen)."""
    store_luck.compact()
    _snapshot_inventory()
    templates = _ignore_templates()
    if templates:
        print(f"[extract_yellow] {len(templates)} template(s) de items a ignorar")

    count = 0
    skipped = 0
    hits = 0
    button_pos = None
    for name in SLOT_NAMES:
        if templates and _is_ignored(get_region(name), templates):
            skipped += 1
            continue
        if button_pos is not None:
            _extract_at_direct(name, button_pos)
            count += 1
            continue
        btn = _extract_at(name)
        if not btn:
            continue
        count += 1
        hits += 1
        if hits >= STATIC_AFTER_HITS:
            print(f"[extract_yellow] botón estático tras {hits} usos, "
                  f"modo directo desde acá (sin imagen, sin espera)")
            button_pos = btn
    print(f"[extract_yellow] {count} upgrade(s) extraído(s)/intentado(s), "
          f"{skipped} ignorado(s) por template, de {MAX_SLOTS} slots")
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
# 3. Salvage del gear con silver_fed, cortado antes de llegar a upgrades
# ============================================================

def _capture_boundary() -> list[np.ndarray]:
    return [vision.capture_screen(get_region(name)) for name in BOUNDARY_REGIONS]


def _boundary_changed(baseline: list[np.ndarray]) -> bool:
    current = _capture_boundary()
    for before, after in zip(baseline, current):
        if before.shape != after.shape:
            return True
        diff = float(np.abs(after.astype(int) - before.astype(int)).mean())
        if diff > BOUNDARY_CHANGE_THRESHOLD:
            return True
    return False


def _fire_silver_fed_salvage() -> None:
    """Dispara el salvage bulk (no espera a que termine — eso lo maneja
    salvage_gear_then_upgrades vigilando la frontera)."""
    inp.right_click(get_point("silver_fed"))
    time.sleep(SLEEP_AFTER_KIT_RIGHT_CLICK)
    inp.click(get_point("silver_fed_salvage_rare"))
    time.sleep(SLEEP_AFTER_KIT_OPTION)
    salvage.click_accept()


def _interrupt_inventory() -> None:
    """Cierra inventario a media-salvage (cancela la acción en curso sin
    perder lo ya salvageado) y lo reabre junto con el mapa, que se deja
    abierto para que el juego corra más fluido.

    La 1ra 'i' es la que realmente cancela — le damos más tiempo para que
    registre antes de seguir. La 1ra 'm' es la que más tarda en procesar
    (probado: con menos de ~1.7s no siempre salía la secuencia completa).
    El resto va con ritmo humano (jitter), no tecleo robótico parejo."""
    import keyboard as _kb
    _kb.press_and_release("i")
    time.sleep(SLEEP_AFTER_INTERRUPT_CANCEL)
    _kb.press_and_release("m")
    time.sleep(SLEEP_AFTER_INTERRUPT_FIRST_M)
    for key in ("i", "m"):
        _kb.press_and_release(key)
        inp.sleep(SLEEP_AFTER_INTERRUPT_KEYPRESS, jitter=0.3)


def salvage_gear_then_upgrades() -> None:
    """Arranca el salvage bulk de silver_fed y corta ANTES de que le toque
    a sigils/runes por DOS seguros independientes, lo que dispare primero:
      (a) las 5 zonas frontera cambian por imagen, confirmado
          BOUNDARY_CONFIRMATIONS veces seguidas (un cambio aislado puede
          ser un parpadeo del efecto de salvage, no el ícono desapareciendo
          de verdad), o
      (b) pasan EXTRACT_SALVAGE_TIMEOUT segundos — respaldo si la imagen
          falla del todo; calibrado para alcanzar casi hasta el final del
          batch (250), no para cortar temprano (eso lo hace (a)).
    Termina lo que quedó (upgrades, y tal vez algo de gear sin tocar) con
    el copper_fed barato."""
    store_luck.compact()
    baseline = _capture_boundary()
    _fire_silver_fed_salvage()

    deadline = time.time() + SALVAGE_TIMEOUT
    streak = 0
    while time.time() < deadline:
        if _boundary_changed(baseline):
            streak += 1
            if streak >= BOUNDARY_CONFIRMATIONS:
                print(f"[extract_yellow] frontera confirmada ({BOUNDARY_CONFIRMATIONS}x), "
                      f"interrumpiendo...")
                break
        else:
            streak = 0
        time.sleep(BOUNDARY_POLL_INTERVAL)
    else:
        print(f"[extract_yellow] tope de {SALVAGE_TIMEOUT:.0f}s alcanzado (2do seguro), "
              f"interrumpiendo...")

    _interrupt_inventory()

    print("[extract_yellow] salvage del resto con copper_fed...")
    inp.right_click(get_point("copper_fed"))
    time.sleep(SLEEP_AFTER_KIT_RIGHT_CLICK)
    inp.click(get_point("copper_fed_salvage_rare"))
    time.sleep(SLEEP_AFTER_KIT_OPTION)
    salvage.click_accept()
    # Barato, no hace falta interrumpirlo — pero sí darle tiempo de
    # terminar solo antes de que el caller compacte (si no, se lo pisa).
    time.sleep(SLEEP_AFTER_COPPER_SALVAGE)


# ============================================================
# Orquestador
# ============================================================

def run() -> bool:
    print("[extract_yellow] procesando stack de yellow unidentified gear...")
    if not identify_one():
        return False
    extract_all()
    salvage_gear_then_upgrades()
    setup.restore_bank_filter()
    store_luck.compact()
    print("[extract_yellow] OK")
    return True
