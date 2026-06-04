"""Schedule del loop principal: qué corre y cada cuántas iteraciones.

Editá `TASKS` para agregar/quitar rutinas. `every=N` = corre cuando `i % N == 0`
(con i empezando en 1). every=1 = cada iteración.

`MAX_ITERATIONS = -1` corre infinito.
"""

from .routines import phase1_salvage_greens, phase2_consume_luck

MAX_ITERATIONS = 1  # -1 = infinito


TASKS = [
    # (every, callable)
    # (1, phase1_salvage_greens.run),
    (1, phase2_consume_luck.run),
    # (2,  lambda: sell_item("mithril_ore")),
    # (3,  lambda: sell_item("silk_scraps")),
    # (10, sell_ectos.run),
    # (25, restart_or_not.run),
]
