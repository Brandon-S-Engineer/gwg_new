"""Procesar Esencia de Suerte: subir tiers en la pestaña artificing y, durante
las esperas del craft, ir vendiendo seals + materiales para no gastar tiempo
extra después. Al final cambia a la pestaña banco, guarda las exotic, consume
el remanente y compacta.

La ventana tiene dos pestañas que se alternan: artificing_station (crafteo) y
banco (depositar). Se craftea en la primera y se deposita en la segunda.

Corre 1 vez en FINAL_TASKS, después de ectos.run.

La espera de cada craft SIEMPRE es por imagen (el "luck [0]" que aparece
al terminar, ver _wait_for_luck_zero/CRAFT_DONE_REGION), nunca un tiempo
fijo: craftear tarda variable y un tiempo fijo corto dejaba el juego
pegado en artificing (craft aún en curso) cuando la iteración seguía de
largo — eso hacía que phase1 después no encontrara greens en el inventario
y cortara el loop entero con un falso "no quedan greens".

Truco del overlap: mientras se espera el "luck [0]" de cada tier, se
intercala venta (seals/materiales) en cada vuelta del poll en vez de solo
dormir — el trabajo de venta es un generator compartido: se pausa y
retoma entre los 3 tiers sin repetir lo ya vendido, y si se agota antes
de que el craft termine, solo se sigue esperando la imagen sin más venta.

Flujo:
  1. pestaña artificing → buscar "luck"
  2. craftear masterwork, rare, exotic (craft_all + espera vendiendo)
  3. terminar la venta pendiente si quedó algo
  4. pestaña banco → filtrar "luck" (si no, no salen todas las exotic) →
     guardar (doble-click, tantos stacks como haya)
  5. consumir el remanente que no sea exotic (blue/green/yellow)
  6. compactar

Las 3 recetas se buscan por IMAGEN (no por coordenada fija): la lista de
resultados de la búsqueda no tiene un orden estable entre sesiones (varía
qué fila cae arriba/medio/abajo), así que un punto fijo se rompía cada
vez que el juego reordenaba. Con template matching no importa en qué
fila caiga cada receta.

Coordenadas necesarias (agregar con el picker):
    artificing_station - pestaña de crafteo (herramientas)
    banco             - pestaña del banco (depositar)
    search_production - campo de búsqueda de recetas
    craft_all         - botón Craft All

Regiones necesarias (agregar con el picker):
    RECIPE_LIST_AREA      - caja que cubre las 3 filas de resultados
    CRAFT_DONE_REGION     - zona del botón de craft donde aparece "luck [0]"
                            al terminar (para run_after_ectos)
    CRAFT_INGREDIENT_REGION - zona del panel de Ingredients donde aparece
                            "I have 0." en rojo al agotarse el ingrediente
                            base — señal INDEPENDIENTE de que terminó,
                            además del "luck [0]" del botón (ver
                            _wait_for_luck_zero: cualquiera de las dos
                            confirma, por si una queda tapada/oscurecida)
    CRAFT_ALL_REGION      - misma zona que la coordenada 'craft_all', para
                            buscar el botón por imagen en vez de clickear
                            a ciegas (ver _click_craft_all)

Items necesarios (capturar con el picker, pestaña de items):
    recipe_masterwork, recipe_rare, recipe_exotic - recorte de cada
    receta en la lista. Recortar el ÍCONO o el texto del NOMBRE, sin
    incluir el conteo entre paréntesis al final (ese número cambia).
    luck_zero - el "luck [0]" que aparece al terminar un craft (sirve
    para los 3 tiers).
    ingredient_zero - el "I have 0." en rojo del panel de Ingredients
    (recortar SOLO ese texto, no el nombre del ingrediente arriba, que
    cambia por tier).
    craft_all_button - recorte del botón "Craft All" en su estado normal
    (activo, con items para craftear) — NO el estado gris/deshabilitado.
"""

import datetime
import time

import cv2

from .. import config
from .. import input as inp
from .. import schedule
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_point, get_region
from . import phase2_consume_luck, sell, sell_all_clean, sell_materials, sell_seals, setup, store_luck

# Diagnóstico cuando el 'luck [0]' nunca se confirma a tiempo: guardar
# screenshot + una línea de log acá (mismo estilo que debug_green.py) para
# revisar después qué pasó, sin tener que reproducirlo en vivo.
CRAFT_TIMEOUT_DIR = config.PROJECT_ROOT / "tools" / "debug_output" / "craft_timeout"

RECIPE_MASTERWORK = ITEMS_DIR / "recipe_masterwork.png"
RECIPE_RARE = ITEMS_DIR / "recipe_rare.png"
RECIPE_EXOTIC = ITEMS_DIR / "recipe_exotic.png"

# "luck [0]" en la zona del botón de craft: señal de que el craft terminó.
# Capturar con el picker; sirve igual para los 3 tiers.
LUCK_ZERO = ITEMS_DIR / "luck_zero.png"
LUCK_ZERO_THRESHOLD = 0.85

# Segunda señal, independiente de la de arriba: "I have 0." del ingrediente
# base, en el panel de Ingredients (zona distinta a CRAFT_DONE_REGION). Con
# cualquiera de las dos alcanza para confirmar — si algo tapa/oscurece una
# (ej. un popup), la otra la respalda.
INGREDIENT_ZERO = ITEMS_DIR / "ingredient_zero.png"
INGREDIENT_ZERO_THRESHOLD = 0.85

# Botón "Craft All" por imagen (misma zona que el punto craft_all) en vez
# de coordenada fija — más confiable si el botón se corre un poco.
CRAFT_ALL_BUTTON = ITEMS_DIR / "craft_all_button.png"
CRAFT_ALL_THRESHOLD = 0.85

# Sacar el cursor hacia abajo tras clickear craft_all, para que no tape
# el "luck [0]" al reconocerlo por imagen.
CRAFT_MOUSE_PARK_OFFSET = (0, 150)

# Templates a capturar en el VM (recorte del nombre/ícono, sin el conteo).
RECIPE_THRESHOLD = 0.85
RECIPE_FIND_TIMEOUT = 2.0

# Cuántos stacks de exotic guardar como mucho (corta el loop si el find
# se queda pegado en un falso positivo).
MAX_STORE_PASSES = 6


def _sell_steps():
    """Un yield por venta hecha: primero sellos, luego materiales. Como es un
    generator, guarda su posición: el craft lo pausa cuando se acaba el tiempo
    y lo reanuda en la siguiente espera, sin repetir lo ya vendido.

    La limpieza de exotics NO va acá: el procesamiento de luck traba el TP,
    así que exotics corre aparte, al final de FINAL_TASKS (ver exotics.py)."""
    for name in sell_seals.SEALS:
        if sell.sell_item(name):
            yield
    for name in sell_all_clean.MATERIALS:
        for _ in range(sell_all_clean.MAX_PASSES):
            if not sell.sell_item(name):
                break  # no queda de este → siguiente material
            yield


def test_find_recipes():
    """Abre artificing, busca 'luck' y solo DETECTA las 3 recetas por
    imagen (sin clickear ni craftear nada). Para probar que los templates
    y RECIPE_LIST_AREA están bien calibrados antes de correr run().
    """
    open_and_search_luck()
    for template in (RECIPE_MASTERWORK, RECIPE_RARE, RECIPE_EXOTIC):
        spot = vision.find(template, region=get_region("RECIPE_LIST_AREA"),
                           threshold=RECIPE_THRESHOLD)
        if spot:
            print(f"[craft_essence] {template.name}: encontrada en {spot}")
        else:
            print(f"[craft_essence] {template.name}: NO encontrada")


# La búsqueda de la artificing station persiste dentro de la sesión: con
# escribir "luck" la primera vez alcanza. Las siguientes solo cambian de tab.
_luck_searched = False


def open_and_search_luck(force: bool = False):
    """Pestaña artificing + escribir 'luck' en la búsqueda de recetas
    (solo la primera vez de la corrida: el texto persiste en el juego).

    Separado de run() para poder probarlo solo (`py -m bot craft_essence
    search`) sin correr los ~7 min de craft completos.
    """
    global _luck_searched
    # Confirmado por imagen: si el paso anterior no soltó el control, este
    # click se perdía y todo el craft fallaba (recetas no encontradas, etc.).
    setup.ensure_artificing_tab()
    if _luck_searched and not force:
        return
    inp.click(get_point("search_production"))
    time.sleep(0.15)
    inp.clear_field()
    inp.type_text("luck")
    time.sleep(schedule.CRAFT_AFTER_SEARCH)
    _luck_searched = True


def _quick_sell_steps(materials):
    """Un yield por venta: los mismos materiales/pases que sell_materials.run,
    pero como generator para consumirlo durante las esperas del craft."""
    for name in materials:
        pre = sell_materials.PRE_DELAY.get(name, 0.0)
        passes = sell_materials.MAX_PASSES if name in sell_materials.MULTI_STACK else 1
        for _ in range(passes):
            if not sell.sell_item(name, pre_delay=pre):
                break
            yield


def quick(materials=None):
    """Craft incremental (cada 2 iteraciones): sube los 3 tiers con la luck
    acumulada en inventario, vendiendo LUCENT+FAST durante las esperas.
    Es la venta que igual tocaba esta iteración: el craft va gratis en sus
    tiempos muertos. Al final vuelve a la pestaña banco y repone filtros.
    """
    if materials is None:
        materials = sell_materials.LUCENT + sell_materials.FAST
    print("[craft_essence] quick: craft de tiers + venta en paralelo")
    open_and_search_luck()

    work = _quick_sell_steps(materials)
    _craft_wait_zero(RECIPE_MASTERWORK, work)
    _craft_wait_zero(RECIPE_RARE, work)
    _craft_wait_zero(RECIPE_EXOTIC, work)

    # Terminar la venta que no entró en las esperas (el craft ya corre solo).
    for _ in work:
        pass

    # Volver al banco. El filtro del inventario no persiste: reponerlo.
    # El "luck" del banco NO hace falta acá (solo al guardar exotic al final).
    setup.ensure_bank_tab()
    setup.filter_inventory()


def _click_craft_all():
    """Clickea 'Craft All' por imagen dentro de CRAFT_ALL_REGION en vez de
    la coordenada fija — si craft_all_button.png todavía es el placeholder
    (sin capturar de verdad con el picker), usa el punto de siempre."""
    if vision.is_calibrated(CRAFT_ALL_BUTTON):
        spot = vision.wait_for(CRAFT_ALL_BUTTON, region=get_region("CRAFT_ALL_REGION"),
                               timeout=RECIPE_FIND_TIMEOUT, threshold=CRAFT_ALL_THRESHOLD)
        if spot:
            inp.click(spot)
            return
        print("[craft_essence] no encontré 'Craft All' por imagen, uso coordenada")
    inp.click(get_point("craft_all"))


def _park_mouse():
    """Cursor abajo del botón de craft, fuera de CRAFT_DONE_REGION, para que
    no tape el "luck [0]" en el reconocimiento por imagen."""
    x, y = get_point("craft_all")
    dx, dy = CRAFT_MOUSE_PARK_OFFSET
    inp.move_to((x + dx, y + dy))


def _wait_for_luck_zero(timeout: float, work=None) -> bool:
    """Poll cada CRAFT_ZERO_POLL_INTERVAL seg; exige CRAFT_ZERO_CONFIRMATIONS
    lecturas seguidas por encima del threshold antes de dar el craft por
    terminado. Un solo match aislado puede ser el número a medio contar
    (ej. terminando en 0 de casualidad) y no el final real.

    Si se pasa `work` (generator de ventas), intercala un paso de venta en
    cada vuelta que no confirma nada: aprovecha la espera real del craft
    (nunca se adivina de antemano) en vez de solo dormir sin hacer nada.

    En cuanto aparece la PRIMERA lectura positiva (streak >= 1) se corta la
    venta: de ahí en más solo se re-chequea la imagen hasta juntar las
    confirmaciones, sin meter otra venta de por medio. Vender durante las
    confirmaciones era lo que hacía que, al terminar el craft, todavía se
    vendieran 1-2 items más antes de pasar al siguiente tier.

    Segunda señal (INGREDIENT_ZERO): además del "luck [0]" del botón, se
    chequea el "I have 0." del ingrediente base en el panel de Ingredients
    (otra zona de la pantalla) — cualquiera de las dos cuenta como lectura
    positiva. Si una queda tapada/oscurecida por algo (ej. un popup), la
    otra la respalda.

    Candado extra (CRAFT_ZERO_STATIC_POLLS): un craft en curso va cambiando
    la región (contador bajando, animación); si deja de moverse del todo
    durante varias lecturas seguidas es porque ya terminó, aunque el
    template no lo confirme (ej. un popup tapando/oscureciendo la región
    justo en ese momento). Solo cuenta después de haber visto cambiar la
    región al menos una vez, para no disparar en falso apenas arranca."""
    deadline = time.time() + timeout
    streak = 0
    work_done = work is None
    region = get_region("CRAFT_DONE_REGION")
    ingredient_region = get_region("CRAFT_INGREDIENT_REGION")
    # ingredient_zero.png es placeholder hasta que se capture de verdad con
    # el picker: sin eso, un match de casualidad contra 10x10 de ruido
    # daría un falso "terminado" — mejor no chequear esta señal todavía.
    check_ingredient = vision.is_calibrated(INGREDIENT_ZERO)
    prev_frame = None
    static_streak = 0
    ever_changed = False
    while time.time() < deadline:
        found = vision.is_present(LUCK_ZERO, region=region, threshold=LUCK_ZERO_THRESHOLD)
        if not found and check_ingredient:
            found = vision.is_present(INGREDIENT_ZERO, region=ingredient_region,
                                      threshold=INGREDIENT_ZERO_THRESHOLD)
        streak = streak + 1 if found else 0
        if streak >= schedule.CRAFT_ZERO_CONFIRMATIONS:
            return True

        frame = vision.capture_screen(region)
        if prev_frame is not None:
            if cv2.absdiff(frame, prev_frame).mean() > schedule.CRAFT_ZERO_STATIC_DIFF:
                ever_changed = True
                static_streak = 0
            else:
                static_streak += 1
        prev_frame = frame
        if ever_changed and static_streak >= schedule.CRAFT_ZERO_STATIC_POLLS:
            print("[craft_essence] región estática varias lecturas seguidas, asumo terminado")
            return True

        if streak == 0 and not work_done:
            try:
                next(work)
                continue  # ya gastó tiempo real vendiendo, re-chequear ya
            except StopIteration:
                work_done = True
        time.sleep(schedule.CRAFT_ZERO_POLL_INTERVAL)
    return False


def _craft_wait_zero(template, work=None) -> bool:
    """Craftea y espera el fin SIEMPRE por imagen (nunca por tiempo fijo):
    si el craft tarda más de lo esperado, sigue esperando en vez de cortar
    antes de tiempo. Cortar antes dejaba el juego pegado en artificing (el
    craft seguía en curso) y phase1 después no encontraba greens, cortando
    el loop entero con un falso "no quedan greens".

    Si se pasa `work` (generator de ventas), lo intercala durante la
    espera (ver _wait_for_luck_zero) — no se pierde el tiempo muerto."""
    spot = vision.wait_for(template, region=get_region("RECIPE_LIST_AREA"),
                           timeout=RECIPE_FIND_TIMEOUT, threshold=RECIPE_THRESHOLD)
    if not spot:
        print(f"[craft_essence] no encontré {template.name} en la lista, salto este craft")
        return False

    inp.click(spot)
    time.sleep(schedule.CRAFT_AFTER_SELECT)
    _click_craft_all()
    _park_mouse()
    time.sleep(schedule.CRAFT_ZERO_GRACE)

    vendiendo = " (vendiendo mientras)" if work is not None else ""
    print(f"[craft_essence] {template.name} → craft_all, esperando 'luck [0]'{vendiendo}...")
    done = _wait_for_luck_zero(schedule.CRAFT_ZERO_TIMEOUT, work=work)
    if not done:
        print(f"[craft_essence] no vi 'luck [0]' en {schedule.CRAFT_ZERO_TIMEOUT:.0f}s, sigo igual")
        _log_craft_zero_timeout(template)
    return True


def _log_craft_zero_timeout(template) -> None:
    """No es infinito (CRAFT_ZERO_TIMEOUT tiene tope), pero si pasa seguido
    conviene verlo con datos reales en vez de adivinar: guarda un
    screenshot completo + una línea en tools/debug_output/craft_timeout/
    (git-tracked, llega a la otra sesión/PC para revisarlo)."""
    from PIL import ImageGrab
    CRAFT_TIMEOUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = CRAFT_TIMEOUT_DIR / f"{ts}_{template.stem}.png"
    ImageGrab.grab().save(img_path, "PNG")
    with open(CRAFT_TIMEOUT_DIR / "log.txt", "a", encoding="utf-8") as f:
        f.write(f"{ts} | receta={template.name} | timeout={schedule.CRAFT_ZERO_TIMEOUT:.0f}s "
                f"| confirmations={schedule.CRAFT_ZERO_CONFIRMATIONS} "
                f"| poll={schedule.CRAFT_ZERO_POLL_INTERVAL}s | screenshot={img_path.name}\n")
    print(f"[craft_essence] diagnóstico guardado en {CRAFT_TIMEOUT_DIR}")


def _store_exotic_and_finish():
    """Pestaña banco + filtro 'luck' (si no, no salen todas las exotic) +
    guardar exotic (doble-click) + consumir remanente + compactar."""
    setup.ensure_bank_tab()   # confirmado por imagen, no click a ciegas
    setup.filter_bank()
    for _ in range(MAX_STORE_PASSES):
        if not store_luck.run(store_luck.EXOTIC):
            break
    phase2_consume_luck.run(phase2_consume_luck.NON_EXOTIC)
    store_luck.compact()


def run_after_ectos():
    """Iter 30, después de ectos: procesar la luck que soltaron. Sin venta
    en paralelo (ya se vendió antes en la iteración); cada tier espera por
    imagen a que diga "luck [0]". Al final, el cierre de siempre: guardar
    exotic al banco, consumir el remanente y compactar."""
    print("[craft_essence] luck de los ectos: craft de tiers (espera por imagen)")
    open_and_search_luck()
    _craft_wait_zero(RECIPE_MASTERWORK)
    _craft_wait_zero(RECIPE_RARE)
    _craft_wait_zero(RECIPE_EXOTIC)
    _store_exotic_and_finish()


def run():
    open_and_search_luck()

    # Subir tiers vendiendo durante las esperas. `work` es el mismo generator
    # en los 3: se pausa y retoma entre esperas.
    work = _sell_steps()
    _craft_wait_zero(RECIPE_MASTERWORK, work)
    _craft_wait_zero(RECIPE_RARE, work)
    _craft_wait_zero(RECIPE_EXOTIC, work)

    # Si las esperas no alcanzaron, terminar la venta pendiente.
    for _ in work:
        pass

    # Guardar exotic al banco, consumir el remanente y compactar.
    _store_exotic_and_finish()
