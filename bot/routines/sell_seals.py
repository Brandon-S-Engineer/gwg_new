"""Vender sellos en el TP (venta instantánea).

Misma lógica que sell_materials: lista de items + sell.sell_item.
Grupos por ritmo de acumulación; la frecuencia (every) va en schedule.
"""

from . import sell

# Se acumulan rápido (vienen de gear común).
FAST = [
    "little_symbols_of_control",
    "little_symbols_of_enhancement",
    "little_symbols_of_pain",
    "little_charms_of_potence",
    "little_charms_of_briliance",   # ojo: 1 sola l (nombre del archivo)
    "little_charms_of_skill",
]
SLOW = [
    "symbols_of_control",
    "symbols_of_enhancement",
    "symbols_of_pain",
    "charms_of_potence",
    "charms_of_briliance",
    "charms_of_skill",
    "rune_crafter",
]

SEALS = FAST + SLOW

MULTI_STACK: set[str] = set()
MAX_PASSES = 2


def run(items=None) -> bool:
    done = False
    for name in items if items is not None else SEALS:
        passes = MAX_PASSES if name in MULTI_STACK else 1
        for _ in range(passes):
            if not sell.sell_item(name):
                break  # no hay (más) de este → siguiente
            done = True
    return done
