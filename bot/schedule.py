"""Control del loop principal (`py -m bot loop`).

Misma lógica que el bot viejo (`if i % X == 0`), pero en tabla en vez de
hardcodear cada caso. Cada tarea declara cada cuántas iteraciones corre.

  (every, callable)
    every=1  -> cada iteración
    every=5  -> cada 5 iteraciones (corre en i = 5, 10, 15, ...)
    every=25 -> cada 25 (i = 25, 50, ...)

El loop (bot/__main__.py), por iteración i (desde 1), hace:

    for every, task in TASKS:
        if i % every == 0:
            task()

Las tareas corren en el orden de la lista dentro de cada iteración.

MAX_ITERATIONS = -1 corre infinito (como el `for i in range(1, 20001)` viejo).
Poné un número chico para probar.
"""

from .routines import (
    phase1_salvage_greens,
    phase2_consume_luck,
    phase3_salvage_rares,
    sell_materials,
)

MAX_ITERATIONS = 5  # -1 = infinito

STARTUP_DELAY = 5  # 

TASKS = [
    # (every, callable)
    (1, phase1_salvage_greens.run),
    (5, phase3_salvage_rares.run),
    # (5, phase2_consume_luck.run),   
    (5, sell_materials.run),          # vender materiales en TP
    # (10, sell_ectos.run),                      # cada 10
    # (25, restart_or_not.run),                  # cada 25
]
