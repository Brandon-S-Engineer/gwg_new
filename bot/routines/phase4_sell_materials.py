"""Fase 4: vender materiales en el TP (venta instantánea).

Por ahora solo silk scraps. Para sumar más mats que se venden igual
(mithril, elder wood, etc.), agregalos a MATERIALS.

Ectos y lucent motes NO van acá (otro flujo).
"""

from . import sell

MATERIALS = [
    "silk_scraps",
    "mithril_ore",
    # "elder_wood_logs",
    # "thick_leather_sections",
]


def run() -> bool:
    done = False
    for name in MATERIALS:
        if sell.sell_item(name):
            done = True
    return done
