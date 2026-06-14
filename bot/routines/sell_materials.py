"""Fase 4: vender materiales en el TP (venta instantánea).

Por ahora solo silk scraps. Para sumar más mats que se venden igual
(mithril, elder wood, etc.), agregalos a MATERIALS.

Ectos y lucent motes NO van acá (otro flujo).
"""

from . import sell

# Espera antes del right-click (por item). Lucent motes: el salvage aún suelta
# y la ventana del TP no abre si clickeamos enseguida.
PRE_DELAY = {"lucent_motes": 2.0}

# Grupos por ritmo de acumulación. La frecuencia (every) va en schedule.
LUCENT = ["lucent_motes"]            # te dan muchísimas
FAST = [                             # se acumulan rápido
    "mithril_ore",
    "elder_wood_logs",
    "silk_scraps",
    "thick_leather_sections",
]
SLOW = [                            # te dan menos
    "orichalcum_ore",
    "ancient_wood_logs",
    "gossamer_Scraps",              # ojo: S mayúscula (nombre del archivo)
    "hardened_leather_sections",
    # "reclaimed_metal_plates",    # opcional, byproduct de salvage
]

MATERIALS = LUCENT + FAST + SLOW

# Suelen pasar de 250 (más de un stack): venderlos hasta 2 veces.
MULTI_STACK = {"lucent_motes", "mithril_ore", "silk_scraps"}
MAX_PASSES = 2


def run(materials=None) -> bool:
    done = False
    for name in materials if materials is not None else MATERIALS:
        pre = PRE_DELAY.get(name, 0.0)
        passes = MAX_PASSES if name in MULTI_STACK else 1
        for _ in range(passes):
            if not sell.sell_item(name, pre_delay=pre):
                break  # no hay (más) de este → siguiente material
            done = True
    return done
