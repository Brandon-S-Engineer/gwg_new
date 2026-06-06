"""Fase 4: vender materiales en el TP (venta instantánea).

Por ahora solo silk scraps. Para sumar más mats que se venden igual
(mithril, elder wood, etc.), agregalos a MATERIALS.

Ectos y lucent motes NO van acá (otro flujo).
"""

from . import sell

MATERIALS = [
    # mineral
    "mithril_ore",
    "orichalcum_ore",
    # madera
    "elder_wood_logs",
    "ancient_wood_logs",
    # tela
    "silk_scraps",
    "gossamer_Scraps",          # ojo: S mayúscula (nombre del archivo)
    # cuero
    "thick_leather_sections",
    "hardened_leather_sections",
    # otros
    "lucent_motes",
    # "reclaimed_metal_plates", # opcional, byproduct de salvage
]

# Suelen pasar de 250 (más de un stack): venderlos hasta 2 veces.
MULTI_STACK = {"lucent_motes", "mithril_ore", "silk_scraps"}
MAX_PASSES = 2


def run() -> bool:
    done = False
    for name in MATERIALS:
        passes = MAX_PASSES if name in MULTI_STACK else 1
        for _ in range(passes):
            if not sell.sell_item(name):
                break  # no hay (más) de este → siguiente material
            done = True
    return done
