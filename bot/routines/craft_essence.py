"""Procesar Esencia de Suerte: subir tiers en la artificing station (banco
incluido) y, durante las esperas del craft, ir vendiendo seals + materiales
para no gastar tiempo extra después. Al final guarda las exotic al banco,
consume el remanente y compacta.

Corre 1 vez en FINAL_TASKS, después de ectos.run.

Truco del overlap: las 3 esperas del craft (masterwork/rare/exotic) suman
~6 min. En vez de dormir, esos segundos se usan vendiendo. El trabajo de venta
es un generator compartido: cada espera consume lo que alcance y, cuando se
acaba el tiempo, se lanza el siguiente craft y la próxima espera RETOMA donde
quedó (el generator guarda su posición). Si la venta se acaba antes que la
espera, se duerme el resto para no cortar el craft.

Flujo:
  1. abrir banco → Production → buscar "luck"
  2. craftear masterwork, rare, exotic (craft_all + espera vendiendo)
  3. terminar la venta pendiente si quedó algo
  4. abrir banco, guardar las exotic (doble-click, tantos stacks como haya)
  5. consumir el remanente que no sea exotic (blue/green/yellow)
  6. compactar

Coordenadas necesarias (agregar con el picker):
    banco             - abre la artificing station (incluye banco)
    production        - pestaña Production
    search_production - campo de búsqueda de recetas
    masterwork_essence, rare_essence, exotic_essence - recetas en la lista
    craft_all         - botón Craft All
"""

import time

from .. import input as inp
from .. import schedule
from ..coords_loader import get_point
from . import phase2_consume_luck, sell, sell_all_clean, sell_seals, store_luck

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


def run():
    import keyboard as _kb

    # Abrir artificing station (banco incluido) y buscar recetas de luck.
    inp.click(get_point("banco"))
    time.sleep(schedule.CRAFT_AFTER_OPEN)
    inp.click(get_point("production"))
    time.sleep(schedule.CRAFT_AFTER_PRODUCTION)
    inp.click(get_point("search_production"))
    time.sleep(0.15)
    _kb.send("ctrl+a")
    time.sleep(0.05)
    _kb.send("delete")
    _kb.write("luck")
    time.sleep(schedule.CRAFT_AFTER_SEARCH)

    # Subir tiers vendiendo durante las esperas. `work` es el mismo generator
    # en los 3: se pausa y retoma entre esperas.
    work = _sell_steps()
    _craft("masterwork_essence", schedule.CRAFT_WAIT_MASTERWORK, work)
    _craft("rare_essence", schedule.CRAFT_WAIT_RARE, work)
    _craft("exotic_essence", schedule.CRAFT_WAIT_EXOTIC, work)

    # Si las esperas no alcanzaron, terminar la venta pendiente.
    for _ in work:
        pass

    # Guardar las exotic al banco (doble-click), tantos stacks como haya.
    inp.click(get_point("banco"))
    time.sleep(schedule.CRAFT_AFTER_OPEN)
    for _ in range(MAX_STORE_PASSES):
        if not store_luck.run(store_luck.EXOTIC):
            break

    # Consumir el remanente que no sea exotic y compactar.
    phase2_consume_luck.run(phase2_consume_luck.NON_EXOTIC)
    store_luck.compact()
