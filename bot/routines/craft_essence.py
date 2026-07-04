"""Procesar Esencia de Suerte: subir tiers en la pestaña artificing y, durante
las esperas del craft, ir vendiendo seals + materiales para no gastar tiempo
extra después. Al final cambia a la pestaña banco, guarda las exotic, consume
el remanente y compacta.

La ventana tiene dos pestañas que se alternan: artificing_station (crafteo) y
banco (depositar). Se craftea en la primera y se deposita en la segunda.

Corre 1 vez en FINAL_TASKS, después de ectos.run.

Truco del overlap: las 3 esperas del craft (masterwork/rare/exotic) suman
~6 min. En vez de dormir, esos segundos se usan vendiendo. El trabajo de venta
es un generator compartido: cada espera consume lo que alcance y, cuando se
acaba el tiempo, se lanza el siguiente craft y la próxima espera RETOMA donde
quedó (el generator guarda su posición). Si la venta se acaba antes que la
espera, se duerme el resto para no cortar el craft.

Flujo:
  1. pestaña artificing → buscar "luck"
  2. craftear masterwork, rare, exotic (craft_all + espera vendiendo)
  3. terminar la venta pendiente si quedó algo
  4. pestaña banco → filtrar "luck" (si no, no salen todas las exotic) →
     guardar (doble-click, tantos stacks como haya)
  5. consumir el remanente que no sea exotic (blue/green/yellow)
  6. compactar

Coordenadas necesarias (agregar con el picker):
    artificing_station - pestaña de crafteo (herramientas)
    banco             - pestaña del banco (depositar)
    search_production - campo de búsqueda de recetas
    masterwork_essence, rare_essence, exotic_essence - recetas en la lista
    craft_all         - botón Craft All
"""

import time

from .. import input as inp
from .. import schedule
from ..coords_loader import get_point
from . import phase2_consume_luck, sell, sell_all_clean, sell_seals, setup, store_luck

# Cuántos stacks de exotic guardar como mucho (corta el loop si el find
# se queda pegado en un falso positivo).
MAX_STORE_PASSES = 6


def _sell_steps():
    """Un yield por venta hecha: primero sellos, luego materiales. Como es un
    generator, guarda su posición: el craft lo pausa cuando se acaba el tiempo
    y lo reanuda en la siguiente espera, sin repetir lo ya vendido."""
    for name in sell_seals.SEALS:
        if sell.sell_item(name):
            yield
    for name in sell_all_clean.MATERIALS:
        for _ in range(sell_all_clean.MAX_PASSES):
            if not sell.sell_item(name):
                break  # no queda de este → siguiente material
            yield


def _work_during(duration: float, work):
    """Consume pasos de `work` hasta que pasen `duration` seg. Chequea el
    tiempo ENTRE ventas (nunca corta una venta a medias). Si `work` se agota
    antes, duerme el resto para que el craft tenga su tiempo completo."""
    start = time.monotonic()
    for _ in work:
        if time.monotonic() - start >= duration:
            return  # tiempo cumplido; el generator queda donde iba
    rest = duration - (time.monotonic() - start)
    if rest > 0:
        time.sleep(rest)


def _craft(recipe: str, wait: float, work):
    inp.click(get_point(recipe))
    time.sleep(schedule.CRAFT_AFTER_SELECT)
    inp.click(get_point("craft_all"))
    print(f"[craft_essence] {recipe} → craft_all, {wait:.0f}s (vendiendo mientras)...")
    _work_during(wait, work)


def open_and_search_luck():
    """Pestaña artificing + escribir 'luck' en la búsqueda de recetas.

    Separado de run() para poder probarlo solo (`py -m bot craft_essence
    search`) sin correr los ~7 min de craft completos.
    """
    inp.click(get_point("artificing_station"))
    time.sleep(schedule.CRAFT_AFTER_OPEN)
    inp.click(get_point("search_production"))
    time.sleep(0.15)
    inp.clear_field()
    inp.type_text("luck")
    time.sleep(schedule.CRAFT_AFTER_SEARCH)


def run():
    open_and_search_luck()

    # Subir tiers vendiendo durante las esperas. `work` es el mismo generator
    # en los 3: se pausa y retoma entre esperas.
    work = _sell_steps()
    _craft("masterwork_essence", schedule.CRAFT_WAIT_MASTERWORK, work)
    _craft("rare_essence", schedule.CRAFT_WAIT_RARE, work)
    _craft("exotic_essence", schedule.CRAFT_WAIT_EXOTIC, work)

    # Si las esperas no alcanzaron, terminar la venta pendiente.
    for _ in work:
        pass

    # Cambiar a la pestaña banco, filtrar por "luck" (si no, no salen todas
    # las exotic) y guardar (doble-click).
    inp.click(get_point("banco"))
    time.sleep(schedule.CRAFT_AFTER_OPEN)
    setup.filter_bank()
    for _ in range(MAX_STORE_PASSES):
        if not store_luck.run(store_luck.EXOTIC):
            break

    # Consumir el remanente que no sea exotic y compactar.
    phase2_consume_luck.run(phase2_consume_luck.NON_EXOTIC)
    store_luck.compact()
