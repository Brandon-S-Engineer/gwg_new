"""Limpieza final: vender TODOS los materiales hasta acabarlos.

Igual que sell_materials pero sin frecuencias: barre cada material hasta que
no quede ninguno, para dejar el inventario limpio al terminar.

NO toca ectos/crystalline dust (tienen su propia lógica en ectos.py) ni
sellos (no hace falta). Solo materiales.

Corre 1 vez al terminar el loop (schedule.FINAL_TASKS).
"""

from . import sell
from . import sell_materials

# Mismos materiales que sell_materials, todos juntos.
MATERIALS = sell_materials.MATERIALS

MAX_PASSES = 12   # tope de seguridad por material, no loop infinito


def run() -> bool:
    """Vende cada material hasta que no quede. Re-escanea tras cada venta."""
    done = False
    for name in MATERIALS:
        for _ in range(MAX_PASSES):
            if not sell.sell_item(name):
                break  # no hay (más) de este → siguiente material
            done = True
    return done
