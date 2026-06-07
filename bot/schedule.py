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
    sell_seals,
)

MAX_ITERATIONS = 14  # -1 = infinito

STARTUP_DELAY = 5  # 

TASKS = [
    # (every, callable)
    (1, phase1_salvage_greens.run),
    (4, phase3_salvage_rares.run),
    # (5, phase2_consume_luck.run),
    # vender mats en TP, por ritmo de acumulación
    (5, lambda: sell_materials.run(sell_materials.LUCENT)),   # lucent motes
    (7, lambda: sell_materials.run(sell_materials.FAST)),     # silk, mithril, elder wood
    (14, lambda: sell_materials.run(sell_materials.SLOW)),    # el resto
    # vender sellos en TP, por ritmo de acumulación
    (7, lambda: sell_seals.run(sell_seals.FAST)),            # little symbols/charms
    (14, lambda: sell_seals.run(sell_seals.SLOW)),           # symbols/charms enteros + rune
    # (10, sell_ectos.run),                      # cada 10
    # (25, restart_or_not.run),                  # cada 25
]
