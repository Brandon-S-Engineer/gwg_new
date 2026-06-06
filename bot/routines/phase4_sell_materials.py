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
    # "lucent_motes",           # flujo aparte
    # "reclaimed_metal_plates", # opcional, byproduct de salvage
]


def run() -> bool:
    done = False
    for name in MATERIALS:
        if sell.sell_item(name):
            done = True
    return done
