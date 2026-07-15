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
PHASE1_AFTER_IDENTIFY = 8.0
PHASE1_AFTER_SALVAGE = 19.0
PHASE1_AFTER_BANK_DOUBLECLICK = 0.5  # que la verde aparezca en inv antes de re-escanear
# --- phase2_consume_luck ---
PHASE2_BEFORE_RIGHT_CLICK = 0.08     # asentar cursor antes del right-click
PHASE2_AFTER_RIGHT_CLICK = 0.8       # que abra el menú (NO tocar: right-click + bajar quita el hover)
PHASE2_AFTER_DISMISS = 0.1           # tooltip ya se fue al bajar; clickear cuanto antes
PHASE2_AFTER_CONSUME = 0.2           # mínimo para que el stack desaparezca, y a la siguiente

# --- deposit_metal_plates (depositar directo al depósito de materiales) ---
DEPOSIT_BEFORE_RIGHT_CLICK = 0.08    # asentar cursor antes del right-click
DEPOSIT_AFTER_RIGHT_CLICK = 0.8      # que abra el menú
DEPOSIT_AFTER_DISMISS = 0.1          # tooltip ya se fue al bajar
DEPOSIT_AFTER_DEPOSIT = 0.2          # mínimo para que el stack desaparezca, y al siguiente

# --- phase3_salvage_rares (silver_fed) ---
PHASE3_AFTER_RIGHT_CLICK = 0.8       # que abra el menú del kit
PHASE3_AFTER_OPTION = 0.5            # que aparezca el diálogo Accept
PHASE3_AFTER_SALVAGE = 3.0           # que termine el salvage

# --- ectos (salvage de stacks + venta de dust) ---
ECTOS_AFTER_RIGHT_CLICK = 0.8        # que abra el menú del kit
ECTOS_AFTER_OPTION = 0.5             # que aparezca el diálogo
ECTOS_AFTER_SALVAGE = 27.0           # que termine el salvage del stack

# --- sell (genérico TP: sell_materials/sell_seals/sell_all_clean) ---
SELL_AFTER_RIGHT_CLICK = 0.8         # que abra el menú
SELL_AFTER_DISMISS = 0.1             # tooltip ya se fue al bajar
SELL_AFTER_READY = 0.3               # asentar tras cargar el TP
SELL_STEP = 0.25                     # entre clicks del panel
SELL_AFTER_LIST = 1.5                # que se procese el listado

# --- setup (arrastrar banco + filtros de texto) ---
SETUP_AFTER_BANK_TAB = 0.5   # tras click en la pestaña banco (asegurar al iniciar)
SETUP_AFTER_DRAG = 0.5       # tras soltar el drag del banco
SETUP_AFTER_KEYPRESS = 0.5   # entre cada tecla de apertura de ventana (i / o / m)
SETUP_AFTER_FILTER = 0.3     # tras escribir en el campo de filtro

# --- craft_essence (subir tiers de esencia en la artificing station) ---
CRAFT_AFTER_OPEN = 1.0           # tras abrir el banco / artificing station
CRAFT_AFTER_SEARCH = 0.5         # tras escribir "luck" en la búsqueda
CRAFT_AFTER_SELECT = 0.5         # tras seleccionar una receta

CRAFT_WAIT_MASTERWORK = 360
CRAFT_WAIT_RARE = 360
CRAFT_WAIT_EXOTIC = 220

# quick(): craft incremental cada 2 iteraciones. Medido para 1 stack entero
# de greens: blue→green 11s, green→yellow 14s, yellow→exotic 9s. Cada 2
# iteraciones hay mucho menos acumulado, así que esto sobra; la espera se
# pasa vendiendo igual, no es tiempo perdido.
CRAFT_QUICK_WAIT_MASTERWORK = 24
CRAFT_QUICK_WAIT_RARE = 30
CRAFT_QUICK_WAIT_EXOTIC = 20

# run_after_ectos(): espera por imagen el "luck [0]" en CRAFT_DONE_REGION.
CRAFT_ZERO_GRACE = 2.0     # tras craft_all, antes de empezar a mirar
CRAFT_ZERO_TIMEOUT = 300   # respaldo por si el template no aparece nunca
CRAFT_ZERO_POLL_INTERVAL = 3.0  # cada cuánto revisar (un solo match aislado
                                 # puede ser un parpadeo a medio contar)
CRAFT_ZERO_CONFIRMATIONS = 2    # lecturas seguidas por encima del threshold
                                 # antes de dar el craft por terminado

# --- compact (compactar inventario) ---
COMPACT_AFTER_CLICK = 0.3

# --- store_luck (guardar luck al banco con doble-click) ---
STORE_LUCK_AFTER_DOUBLECLICK = 0.2

# --- exotics (vender los N más caros + salvage por posición del resto) ---
EXOTICS_AFTER_CLOSE = 1.5        # tras cerrar el último panel de venta
EXOTICS_AFTER_TAB = 1.5          # tras abrir la pestaña "Sell" del TP
EXOTICS_AFTER_SORT = 0.5         # entre los 2 clicks de ordenar por precio
EXOTICS_AFTER_SORT_FINAL = 1.5   # tras el 2do click de ordenar, ya ordenado
EXOTICS_AFTER_SELECT = 2.0       # tras clickear el slot top (más caro)
EXOTICS_AFTER_SUCCESS = 1.5      # tras confirmar la venta, antes de cerrar
EXOTICS_AFTER_ARM_KIT = 0.5      # tras armar el silver_fed en modo "Use"
EXOTICS_AFTER_SALVAGE_CLICK = 0.25  # tras clickear un slot armado, antes del Accept
EXOTICS_AFTER_TP_SECTION = 1.5   # tras el reset de vista (m,o,o,m), click a la sección TP

# --- open_bags (abrir Lucky Red Bags del inventario, comando suelto) ---
# Igual que fase1 pero un poco más rápido: no hay que identificar ni
# salvage después, solo abrir. Calibrar a mano.
OPEN_BAGS_BEFORE_RIGHT_CLICK = 0.2   # asentar cursor sobre la bolsa antes del right-click
OPEN_BAGS_AFTER_RIGHT_CLICK = 0.6    # que abra el menú contextual
OPEN_BAGS_HOVER_USE_ALL = 0.25       # asentar cursor sobre "Use All" antes de clickear
OPEN_BAGS_AFTER_OPEN = 8.0          # espera larga tras abrir (que procese el loot), antes de re-escanear

from .routines import (
    craft_essence,
    debug_green,
    deposit_metal_plates,
    ectos,
    exotics,
    phase1_salvage_greens,
    phase2_consume_luck,
    phase3_salvage_rares,
    sell_all_clean,
    sell_materials,
    sell_seals,
    setup,
    store_luck,
)

MAX_ITERATIONS = 30  # -1 = infinito

STARTUP_DELAY = 5  # 

TASKS = [
    # (every, callable)
    (1, phase1_salvage_greens.run),
    (2, phase3_salvage_rares.run),
    # (5, phase2_consume_luck.run),

    # guardar esencia de suerte al banco (doble-click)
    # (1,  lambda: store_luck.run(store_luck.BLUE)),
    # (1,  lambda: store_luck.run(store_luck.BLUE)),
    # (6,  lambda: store_luck.run(store_luck.GREEN)),
    # (30, lambda: store_luck.run(store_luck.YELLOW)),

    # craft de luck (3 tiers) + venta LUCENT/FAST en paralelo: es la misma
    # venta de siempre cada 2 iteraciones, pero mientras el craft espera.
    # En iter 1 no corre (todavía no hay luck). Reemplaza a store_luck y
    # al craft_essence.run gigante del final.
    (2, craft_essence.quick),
    (10, lambda: sell_materials.run(sell_materials.SLOW)),    # el resto, ya de vuelta en banco

    (30, sell_seals.run),                                    # vender sellos en TP (dan poquitos)
    (30, sell_all_clean.run),                                # limpieza: vender todos los mats restantes
    # (25, restart_or_not.run),                  # cada 25

    # corridas largas (MAX_ITERATIONS grande/-1): estos también van en
    # FINAL_TASKS, pero ahí solo corren 1 vez al terminar el loop entero.
    # Acá se repiten cada 30 iteraciones para que no esperen horas.
    (30, ectos.run),
    # (30, craft_essence.run),
    (30, craft_essence.run_after_ectos),  # procesar la luck de los ectos (espera por imagen)
                                          # + guardar exotic + consumir + compact
    (30, deposit_metal_plates.run),
    (30, exotics.run),
    (30, setup.restore_bank_filter),  # craft_essence/exotics dejan los filtros en otra cosa
]

# Corren 1 vez al terminar el loop (no por iteración). sell_all_clean va también
# acá para limpiar el inventario aunque el loop corte antes del múltiplo de 30.
FINAL_TASKS = [
    # phase1_salvage_greens.drain: NO va acá — corre hasta que no quede
    # ningún green (hasta 100 pasadas), sin límite de tiempo, así que si hay
    # backlog el loop se pasa de MAX_ITERATIONS sin avisar. El backlog que
    # quede se procesa solo en la siguiente corrida (TASKS ya llama a
    # phase1_salvage_greens.run cada iteración).

    # phase3_salvage_rares.run,  # limpiar rares que sueltan más ectos
    # ectos.run,            # salvage de ectos + vender el crystalline dust
    # craft_essence.run,    # craftea esencia y, durante las esperas, vende seals + materiales
    #                       # (luego guarda exotic, consume el resto y compacta)
    # deposit_metal_plates.run,  # reclaimed_metal_plates al depósito, al final de todo
    # exotics.run,           # reset vista TP + vender los más caros + salvage del resto
  
                           # (va después de todo el procesamiento de luck: ese traba el TP)
    # debug_green.run,      # captura + scores de lo que quedó sin tomar (tools/debug_output/)
]
