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
# ensure_bank_tab: confirmar que el click a 'banco' prendió de verdad (ver
# BANK_TAB/REFINEMENT ahí) en vez de asumirlo a ciegas.
BANK_TAB_CONFIRM_TIMEOUT = 15.0
BANK_TAB_RETRY_POLL = 1.0

# --- craft_essence (subir tiers de esencia en la artificing station) ---
CRAFT_AFTER_OPEN = 1.0           # tras abrir el banco / artificing station
CRAFT_AFTER_SEARCH = 0.5         # tras escribir "luck" en la búsqueda
CRAFT_AFTER_SELECT = 0.5         # tras seleccionar una receta

# Espera del craft SIEMPRE por imagen el "luck [0]" en CRAFT_DONE_REGION
# (nunca por tiempo fijo — ver docstring del módulo).
CRAFT_ZERO_GRACE = 2.0     # tras craft_all, antes de empezar a mirar
CRAFT_ZERO_TIMEOUT = 120   # respaldo por si el template no aparece nunca
CRAFT_ZERO_POLL_INTERVAL = 1.0  # cada cuánto revisar (un solo match aislado
                                 # puede ser un parpadeo a medio contar)
CRAFT_ZERO_CONFIRMATIONS = 3    # lecturas seguidas por encima del threshold
CRAFT_ZERO_STATIC_POLLS = 6     # candado extra: si la región no cambia nada
                                 # durante 6 lecturas seguidas (tras haber
                                 # cambiado al menos una vez), se asume
                                 # terminado aunque el template no confirme
CRAFT_ZERO_STATIC_DIFF = 1.5    # diferencia media (escala 0-255) para
                                 # considerar que la región "cambió"
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
EXOTICS_AFTER_DESTROY_RIGHT_CLICK = 0.8  # que abra el menú contextual de la inscripción
EXOTICS_AFTER_DESTROY_DISMISS = 0.1      # tooltip ya se fue al mover el cursor
EXOTICS_AFTER_DESTROY_CLICK = 0.3        # tras click en 'Destroy', que aparezca el confirm

# --- open_bags (abrir Lucky Red Bags del inventario, comando suelto) ---
# Igual que fase1 pero un poco más rápido: no hay que identificar ni
# salvage después, solo abrir. Calibrar a mano.
OPEN_BAGS_BEFORE_RIGHT_CLICK = 0.2   # asentar cursor sobre la bolsa antes del right-click
OPEN_BAGS_AFTER_RIGHT_CLICK = 0.6    # que abra el menú contextual
OPEN_BAGS_HOVER_USE_ALL = 0.25       # asentar cursor sobre "Use All" antes de clickear
OPEN_BAGS_AFTER_OPEN = 8.0          # espera larga tras abrir (que procese el loot), antes de re-escanear

# --- extract_yellow (Upgrade Extractor: yellow unidentified gear, comando
# suelto, independiente del pipeline de greens) ---
EXTRACT_BEFORE_RIGHT_CLICK = 0.25    # asentar cursor antes del right-click (identificar)
EXTRACT_AFTER_RIGHT_CLICK = 0.8      # que abra el menú contextual
EXTRACT_HOVER_USE_ALL = 0.3          # asentar cursor sobre "Use All" antes de clickear
EXTRACT_AFTER_IDENTIFY = 8.0         # esperar a que procese el unidentified yellow gear
# Salvage del gear con silver_fed en el camino SIN extractor (max_slots=0):
# son ~250 items, no los pocos de un fase3 normal (PHASE3_AFTER_SALVAGE=3.0)
# — arranca del mismo tiempo que PHASE1_AFTER_SALVAGE (fase1 también espera
# un stack entero salvageado con un kit) +2s: silver_fed tarda más que el
# rune_crafter que usa fase1.
EXTRACT_AFTER_SALVAGE = 21.0
EXTRACT_AFTER_BANK_DOUBLECLICK = 0.5 # que la yellow aparezca en inv antes de re-escanear
# El barrido de 250 slots amplifica cualquier segundo de sobra (~18min
# medidos). Recortado ~2.2x manteniendo el humanismo del movimiento
# (ver input.py: jitter + curva de aceleración variable), no el timing.
EXTRACT_DRAG_HOLD = 0.15             # hold_before del drag (default global es 0.5, pensado
                                      # para arrastrar ventanas, no para 250 items seguidos)
EXTRACT_BUTTON_TIMEOUT = 0.45        # esperar 'Extract' — la mayoría de slots no lo tienen,
                                      # así que este timeout se paga entero en casi cada uno
EXTRACT_AFTER_DRAG = 0.3             # tras soltar el drag en la ventana del extractor
EXTRACT_AFTER_EXTRACT_CLICK = 0.3    # tras clickear 'Extract', antes del siguiente slot
EXTRACT_AFTER_DIRECT_CLICK = 0.15    # igual, pero en modo directo (ver STATIC_AFTER_HITS)
EXTRACT_AFTER_KIT_RIGHT_CLICK = 0.8  # que abra el menú del kit (silver_fed/copper_fed)
EXTRACT_AFTER_KIT_OPTION = 0.5       # tras clickear 'salvage rares', que aparezca el Accept
# Interrumpir (i,m,i,m): la 1ra 'i' es la que realmente cancela el salvage
# en curso — le damos más tiempo para que registre antes de seguir. Las
# demás van con ritmo humano (jitter), no tecleo robótico parejo: muy
# rápido y el juego no llega a procesarlas (se vio con las 0.5s parejas,
# ni se alcanzaba a reabrir el inventario).
EXTRACT_AFTER_INTERRUPT_CANCEL = 1.0    # tras la 1ra 'i', antes de seguir con m,i,m
EXTRACT_AFTER_INTERRUPT_FIRST_M = 1.7   # tras la 1ra 'm': la que más tarda, no salía bien con menos
EXTRACT_AFTER_INTERRUPT_KEYPRESS = 0.6  # entre la 2da 'i' y la 2da 'm' (con jitter)
EXTRACT_BOUNDARY_POLL_INTERVAL = 0.2    # zona chica, revisar rápido — tiempo crítico
# Doble seguro: este tope es el respaldo si la detección por imagen falla
# del todo, así que tiene que alcanzar para llegar cerca del final (250)
# y no cortar el salvage a medias dejando gear sin tocar. Calibrado por
# regla de 3 con un dato real: a los 17s había llegado al item 182 →
# 17 * 250/182 ≈ 23.35s para llegar a 250, +1s extra de margen.
EXTRACT_SALVAGE_TIMEOUT = 24.3
# Tras disparar el copper_fed bulk (barato, sin interrumpir), darle tiempo
# de terminar solo antes de compactar — si no, compact() puede pisarle el
# salvage a medias.
EXTRACT_AFTER_COPPER_SALVAGE = 18.0
# Lecturas seguidas por encima del umbral antes de aceptar la frontera:
# un solo cambio aislado puede ser un parpadeo/efecto del salvage mismo,
# no el ícono desapareciendo de verdad. A 0.2s de poll, 3 seguidas cuestan
# ~0.6s — no afecta el "doble seguro" en la práctica.
EXTRACT_BOUNDARY_CONFIRMATIONS = 3

from .routines import (
    craft_essence,
    debug_green,
    deposit_metal_plates,
    ectos,
    exotics,
    extract_yellow,
    phase1_salvage_greens,
    phase2_consume_luck,
    phase3_salvage_rares,
    sell_all_clean,
    sell_materials,
    sell_seals,
    setup,
    store_luck,
)


# El corte real es config.NO_GREENS (phase1 avisa cuando ya no hay greens):
# poner un número acá es solo adivinar cuántas iteraciones va a necesitar
# ESTA corrida en particular (varía según cuánto se acumuló), y si se
# adivina bajo corta el loop con backlog sin procesar. -1 = infinito: deja
# que NO_GREENS sea el único corte real.
MAX_ITERATIONS_GREEN = -1
MAX_ITERATIONS_YELLOW = -1  # cada iteración procesa 1 stack completo (más
                             # pesado que una iteración de green); mismo
                             # criterio: corta por NO_GREENS, no por número

STARTUP_DELAY = 5  #

# ============================================================
# GREEN: pipeline de siempre, iteración por iteración (green unidentified
# gear, luck, exotics, etc.). `py -m bot loop g`
# ============================================================

TASKS_GREEN = [
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
    (30, lambda: sell_materials.run(sell_materials.SLOW)),    # el resto, ya de vuelta en banco

    (30, sell_seals.run),                                    # vender sellos en TP (dan poquitos)
    (30, sell_all_clean.run),                                # limpieza: vender todos los mats restantes
    # (25, restart_or_not.run),                  # cada 25

    (30, ectos.run),
    # (30, craft_essence.run),
    (30, craft_essence.run_after_ectos),  # procesar la luck de los ectos (espera por imagen)
                                          # + guardar exotic + consumir + compact
    (30, deposit_metal_plates.run),
    (30, exotics.run),
    (30, setup.restore_bank_filter),  # craft_essence/exotics dejan los filtros en otra cosa
]

FINAL_TASKS_GREEN = [
    # phase1_salvage_greens.drain: NO va acá — corre hasta que no quede
    # ningún green (hasta 100 pasadas), sin límite de tiempo, así que si hay
    # backlog el loop se pasa de MAX_ITERATIONS_GREEN sin avisar. El backlog
    # que quede se procesa solo en la siguiente corrida (TASKS_GREEN ya
    # llama a phase1_salvage_greens.run cada iteración).

    # phase3_salvage_rares.run,  # limpiar rares que sueltan más ectos
    # ectos.run,            # salvage de ectos + vender el crystalline dust
    # craft_essence.run,    # craftea esencia y, durante las esperas, vende seals + materiales
    #                       # (luego guarda exotic, consume el resto y compacta)
    # deposit_metal_plates.run,  # reclaimed_metal_plates al depósito, al final de todo
    # exotics.run,           # reset vista TP + vender los más caros + salvage del resto

                           # (va después de todo el procesamiento de luck: ese traba el TP)
    # debug_green.run,      # captura + scores de lo que quedó sin tomar (tools/debug_output/)
]

#? ============================================================ #

YELLOW_MAX_SLOTS = 0  # __main__.py lo pisa con el N de 'loop y<N>' antes de correr

TASKS_YELLOW = [
    # (every, callable)
    (1, lambda: extract_yellow.run(max_slots=YELLOW_MAX_SLOTS)),

    # Pasos internos de extract_yellow.run(), documentados acá por si algún
    # día hace falta separarlos en tasks propias (hoy van bundleados en la
    # llamada de arriba, no hace falta tocar nada para que corran):
    #   extract_yellow.identify_one          - identificar 1 stack
    #   extract_yellow.extract_all            - drag al Upgrade Extractor (solo si max_slots>0)
    #   extract_yellow.salvage_gear_then_upgrades  - silver_fed cortado + copper_fed (solo si max_slots>0)
    #   phase3_salvage_rares.run              - salvage directo, sin extractor (solo si max_slots==0)
    #   setup.restore_bank_filter             - reponer filtros
    #   store_luck.compact                    - compactar

    (1, lambda: ectos.run(undercut=False)),  # cada iteración, ~222 ectos/stack:
                                              # sin undercut, no me tapo a mí mismo
    (1, craft_essence.quick),
    (10, lambda: sell_materials.run(sell_materials.SLOW)),    # el resto, ya de vuelta en banco
    (10, sell_seals.run),                                    # vender sellos en TP (dan poquitos)
    (10, sell_all_clean.run),                                # limpieza: vender todos los mats restantes
    (10, deposit_metal_plates.run),
    (10, exotics.run),
]

FINAL_TASKS_YELLOW = []
