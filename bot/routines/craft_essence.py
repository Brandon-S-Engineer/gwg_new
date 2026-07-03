"""Procesar Esencia de Suerte: subir tiers en la artificing station (banco
incluido), guardar las exotic al banco, consumir el remanente y compactar.

Corre 1 vez en FINAL_TASKS, después de ectos.run. Tarda ~7 min por los
craft_all (masterwork → rare → exotic), cada uno espera minutos.

Flujo:
  1. abrir banco → Production → buscar "luck"
  2. craftear masterwork, rare, exotic (cada uno craft_all + espera)
  3. abrir banco de nuevo, guardar las exotic (doble-click, tantos stacks
     como haya)
  4. consumir el remanente que no sea exotic (blue/green/yellow)
  5. compactar

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
from . import phase2_consume_luck, store_luck

# Cuántos stacks de exotic guardar como mucho (corta el loop si el find
# se queda pegado en un falso positivo).
MAX_STORE_PASSES = 6


def _craft(recipe: str, wait: float):
    inp.click(get_point(recipe))
    time.sleep(schedule.CRAFT_AFTER_SELECT)
    inp.click(get_point("craft_all"))
    print(f"[craft_essence] {recipe} → craft_all, esperando {wait:.0f}s...")
    time.sleep(wait)


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

    # Subir tiers. Cada tier tiene menos items, por eso espera menos.
    _craft("masterwork_essence", schedule.CRAFT_WAIT_MASTERWORK)
    _craft("rare_essence", schedule.CRAFT_WAIT_RARE)
    _craft("exotic_essence", schedule.CRAFT_WAIT_EXOTIC)

    # Guardar las exotic al banco (doble-click), tantos stacks como haya.
    inp.click(get_point("banco"))
    time.sleep(schedule.CRAFT_AFTER_OPEN)
    for _ in range(MAX_STORE_PASSES):
        if not store_luck.run(store_luck.EXOTIC):
            break

    # Consumir el remanente que no sea exotic.
    phase2_consume_luck.run(phase2_consume_luck.NON_EXOTIC)

    # Compactar al fin.
    store_luck.compact()
