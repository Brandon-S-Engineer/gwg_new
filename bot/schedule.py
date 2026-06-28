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

# ============================================================
# TIMING: todos los tiempos de espera (time.sleep) del bot, en un
# solo lugar para calibrarlos. Van ANTES del import de rutinas
# (más abajo) para que cada módulo pueda hacer `from .. import
# schedule` y leer estas constantes sin import circular.
#
# Bajalos con cuidado: la mayoría es el mínimo para que el juego
# procese la acción anterior antes del siguiente click/screenshot.
# ============================================================

# --- phase1_salvage_greens (identificar + salvage con rune_crafter) ---
PHASE1_BEFORE_RIGHT_CLICK = 0.25     # asentar cursor sobre el green antes del right-click
PHASE1_AFTER_RIGHT_CLICK = 0.8       # que abra el menú contextual
PHASE1_HOVER_USE_ALL = 0.3           # asentar cursor sobre "Use All" antes de clickear
PHASE1_AFTER_SALVAGE_OPTION = 0.5    # tras clickear la opción "salvage green" del rune_crafter
PHASE1_AFTER_IDENTIFY = 8.0          # esperar a que procese el unidentified green gear
PHASE1_AFTER_SALVAGE = 20.0           # que termine el salvage con rune_crafter
PHASE1_AFTER_BANK_DOUBLECLICK = 0.5  # que la verde aparezca en inv antes de re-escanear
# --- phase2_consume_luck ---
PHASE2_BEFORE_RIGHT_CLICK = 0.08     # asentar cursor antes del right-click
PHASE2_AFTER_RIGHT_CLICK = 0.8       # que abra el menú (NO tocar: right-click + bajar quita el hover)
PHASE2_AFTER_DISMISS = 0.1           # tooltip ya se fue al bajar; clickear cuanto antes
PHASE2_AFTER_CONSUME = 0.2           # mínimo para que el stack desaparezca, y a la siguiente

# --- phase3_salvage_rares (silver_fed) ---
PHASE3_AFTER_RIGHT_CLICK = 0.8       # que abra el menú del kit
PHASE3_AFTER_OPTION = 0.5            # que aparezca el diálogo Accept
PHASE3_AFTER_SALVAGE = 6.0           # que termine el salvage

# --- ectos (salvage de stacks + venta de dust) ---
ECTOS_AFTER_RIGHT_CLICK = 0.8        # que abra el menú del kit
ECTOS_AFTER_OPTION = 0.5             # que aparezca el diálogo
ECTOS_AFTER_SALVAGE = 20.0           # que termine el salvage del stack

# --- sell (genérico TP: sell_materials/sell_seals/sell_all_clean) ---
SELL_AFTER_RIGHT_CLICK = 0.8         # que abra el menú
SELL_AFTER_DISMISS = 0.1             # tooltip ya se fue al bajar
SELL_AFTER_READY = 0.3               # asentar tras cargar el TP
SELL_STEP = 0.25                     # entre clicks del panel
SELL_AFTER_LIST = 1.5                # que se procese el listado

# --- store_luck (guardar luck al banco con doble-click) ---
STORE_LUCK_AFTER_COMPACT = 0.3
STORE_LUCK_AFTER_DOUBLECLICK = 0.2

from .routines import (
    ectos,
    phase1_salvage_greens,
    phase2_consume_luck,
    phase3_salvage_rares,
    sell_all_clean,
    sell_materials,
    sell_seals,
    store_luck,
)

MAX_ITERATIONS = 60  # -1 = infinito

STARTUP_DELAY = 5  # 

TASKS = [
    # (every, callable)
    (1, phase1_salvage_greens.run),
    (2, phase3_salvage_rares.run),
    # (5, phase2_consume_luck.run),
    # guardar esencia de suerte al banco (doble-click)
    (1,  lambda: store_luck.run(store_luck.BLUE)),
    (6,  lambda: store_luck.run(store_luck.GREEN)),
    (30, lambda: store_luck.run(store_luck.YELLOW)),
    # vender mats en TP, por ritmo de acumulación
    (2, lambda: sell_materials.run(sell_materials.LUCENT)),   # lucent motes
    (2, lambda: sell_materials.run(sell_materials.FAST)),     # silk, mithril, elder wood
    (6, lambda: sell_materials.run(sell_materials.SLOW)),    # el resto
    (30, sell_seals.run),                                    # vender sellos en TP (dan poquitos)
    (30, sell_all_clean.run),                                # limpieza: vender todos los mats restantes
    # (25, restart_or_not.run),                  # cada 25
]

# Corren 1 vez al terminar el loop (no por iteración). sell_all_clean va también
# acá para limpiar el inventario aunque el loop corte antes del múltiplo de 30.
FINAL_TASKS = [
    phase3_salvage_rares.run,  # limpiar rares que sueltan más ectos
    ectos.run,            # salvage de ectos + vender el crystalline dust
    sell_seals.run,       # vender los sellos que queden
    sell_all_clean.run,   # limpieza final del inventario (materiales)
]
