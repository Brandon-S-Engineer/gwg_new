"""Limpieza: vender TODOS los materiales hasta acabarlos.

Igual que sell_materials pero sin grupos por frecuencia: barre cada material
hasta que no quede ninguno, para dejar el inventario limpio.

NO toca ectos/crystalline dust (tienen su propia lógica en ectos.py) ni
sellos (no hace falta, igual ni quedan). Solo materiales.

Va último en el schedule, cada 30 iteraciones.
"""

from . import sell
from . import sell_materials

# Mismos materiales que sell_materials, todos juntos.
MATERIALS = sell_materials.MATERIALS

MAX_PASSES = 4   # tope de seguridad por material, no loop infinito


def run() -> bool:
    """Vende cada material hasta que no quede. Re-escanea tras cada venta."""
    done = False
    for name in MATERIALS:
        for _ in range(MAX_PASSES):
            if not sell.sell_item(name):
                break  # no hay (más) de este → siguiente material
            done = True
    return done
