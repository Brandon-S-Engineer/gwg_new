# Bot anterior — referencia meta

Resumen de TODA la lógica de `reference_old/main_old.py`. Sirve para escoger qué portar y en qué orden.

---

## 1. Setup inicial (una vez antes del loop)

| Paso | Función                         | Qué hace                                                                                                               |
| ---- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| 1    | `click_game()`                  | Click en `(78,700)` → activa ventana. Abre sell items (`(3450,125)`). Scroll baja 31 veces (alinear vista).            |
| 2    | `sell_item('lucent_motes.png')` | Vende motes (cero-shot, sin orden cada-N)                                                                              |
| 3    | `sell_all()`                    | Vende los 8 materiales base (madera, mithril, ori, sedas, cuero, etc.)                                                 |
| 4    | `consume_luck()`                | Si hay `blue_luck` → consume purple + click "consume all" + luego right-click sobre blue/green/yellow luck → "Consume" |

Cosas que están comentadas en `main()` pero existen: `open_menus()`, `take_all_and_storage(2)`, `salvage_restant_exotics()`, `place_10_orders(15, blue=False)`, `remove_oldest_orders(5)`, `calculate_ecto_profit(...)`.

---

## 2. Loop principal `for i in range(1, 20001)`

Lo que corre **siempre** cada iteración:

| Orden | Llamada                         | Notas                                                                                                                                                          |
| ----- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | `handle_errors()`               | Mira 4 imágenes: `ERR`, `ERR_2`, `select_character`, `windows_desktop`. Cualquier hit → `restart_game()` + `reset_position()` + `open_menus()` y luego reanuda |
| 2     | `manage_rare_gear()`            | Busca `yellow.png` en inventario → "Use All" sobre todos. Si no, busca en banco → doble-click stack → "Use All" inv                                            |
| 3     | `handle_errors()`               |                                                                                                                                                                |
| 4     | `manage_unidentified_gear()`    | Igual pero `green.png`. Si no encuentra → scroll y reintenta (step=3 hace -500\*10 hasta 10 veces)                                                             |
| 5     | `time.sleep(8.5)`               | Esperar identificación                                                                                                                                         |
| 6     | `handle_errors()`               |                                                                                                                                                                |
| 7     | `use_salvage_kits()`            | Salvage greens (Rune Crafter) + Salvage rares (Silver Fed). `sleep(20)` después de cada uno                                                                    |
| 8     | `handle_errors()`               |                                                                                                                                                                |
| 9     | `sell_item('lucent_motes.png')` |                                                                                                                                                                |
| 10    | `consume_luck()`                |                                                                                                                                                                |

Cadencias periódicas:

| `i %` | Llamadas                                                                                                                                                                                                                                                  |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2     | `sell_item(mithril_ore)`, `handle_errors()`, `sell_item(elder_wood_logs)`                                                                                                                                                                                 |
| 3     | `sell_item(silk_scraps)`, `sell_item(thick_leather_sections)`                                                                                                                                                                                             |
| 10    | `sell_ectos()`, `delete_dark_matter()`, `manage_cristallyne_dust()`, `handle_errors()`, `manage_charms()`×4, `sell_all()`×3, `handle_errors()`, `place_10_orders(11, blue=False)`, `remove_oldest_orders(1)`, `consume_luck()`, `take_all_and_storage(1)` |
| 25    | `manage_charms()`×4, `sell_all()`×3, `handle_errors()`, `sell_ectos()`, `sell_most_expensive_exotics(4)`, `salvage_restant_exotics()`, `manage_cristallyne_dust()`, `restart_or_not()`                                                                    |

---

## 3. Funciones por categoría

### Identificar gear (abrir unidentified)

| Función                      | Color  | Pasos                                                                                                                     |
| ---------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------- |
| `manage_unidentified_gear()` | green  | step=1 (inv) → step=2 (banco, doble-click stack y reintenta inv) → step=3 (scroll banco abajo y reintenta hasta 10 veces) |
| `manage_rare_gear()`         | yellow | step=1 → step=2                                                                                                           |
| `manage_common_gear()`       | blue   | step=1 → step=2 → step=3 (scroll)                                                                                         |
| `use_all_green_gear(x,y)`    | —      | right-click → `move(85,205)` → click ("Use All")                                                                          |
| `use_all_rare_gear(x,y)`     | —      | igual + `sleep(10)` + `use_silverfed()` (cadena salvage rares)                                                            |
| `use_all_common_gear(x,y)`   | —      | igual + `sleep(10)` + `use_copperfed()` (cadena salvage commons + greens)                                                 |

### Salvage

| Función                         | Resumen                                                                                                                                                                                                                                                                                                                                            |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `use_salvage_kits()`            | Busca `rune_crafter.png` en inv → right-click → `move(20,90)` → click → `handle_errors` → 7 clicks confirm + `sleep(20)`. Luego busca `silver.png` → right-click → `move(20,125)` → click → 7 clicks confirm + click `compact`                                                                                                                     |
| `use_copperfed()`               | Cadena fija para commons: right-click coords copper_fed → click salvage_common (×2) → 7 clicks confirm → `sleep(15)` → right-click rune_crafter → salvage_green (×2) → 7 confirm → `sleep(8)` → right-click silver_fed → salvage_rare (×2) → confirms → `sleep(1.5)` → `compact`                                                                   |
| `use_silverfed()`               | Similar a `use_salvage_kits` pero solo silver_fed + después: `sell_ectos`×2, `sell_item(motes)`×2, `sell_item(mithril)`×2, `sell_item(elder_wood)`×2, `sell_item(silk)`×2, `sell_item(thick_leather)`×2, `manage_charms`×2, `sell_most_expensive_exotics(3)`, `salvage_restant_exotics_few()`, `manage_cristallyne_dust()`, `delete_dark_matter()` |
| `salvage_ectos()`               | Busca `globs_of_ectoplasm.png` en inv → right-click silver_fed → `salvage_stack` → click sobre ecto → click accept → `sleep(9)` → `consume_luck()`                                                                                                                                                                                                 |
| `salvage_restant_exotics()`     | Compact → busca silver → right-click → `move(20,16)` → click "use" → loop 20 coords fijas `(126..1806, 385)` cada uno: click + click accept_button → `manage_cristallyne_dust()`                                                                                                                                                                   |
| `salvage_restant_exotics_few()` | Mismo pero solo 10 coords                                                                                                                                                                                                                                                                                                                          |

### Vender (Trading Post)

| Función                          | Resumen                                                                                                                                                                                                  |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sell_item(image_path)`          | Encuentra item → right-click → `move(16,88)` → click "Sell" → espera `menus_setup.png` → clicks: `sellers_list (3163,746)` → `maximum_amount (3280,358)` → `list_item (3002,556)` → espera `Success.png` |
| `sell_all()`                     | Llama `sell_item` para 8 materiales: ancient_wood, elder_wood, gossamer, hardened_leather, mithril, orichalcum, silk, thick_leather                                                                      |
| `sell_ectos()`                   | Como `sell_item` pero con `minus_one_copper` antes de listar (vender 1cu bajo el precio)                                                                                                                 |
| `manage_cristallyne_dust()`      | Igual `sell_ectos` (también `minus_one_copper`)                                                                                                                                                          |
| `manage_charms()`                | Sobre 6 imágenes (skill, control, potence, brilliance, pain, enhancement): right-click → "Sell" → `sellers_list` → `maximum_amount` → `minus_one_copper` → `list_item` → `Success`                       |
| `sell_most_expensive_exotics(N)` | Click cerrar venta (3517,186) → click sell tab (3450,125) → click price col (×2) para ordenar → loop N: click primer item (2871,304) → click sell (3007,555 + ,595) → `Success` → cerrar                 |

### TP — órdenes

| Función                             | Resumen                                                                                                                                                                                                                                         |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `place_10_orders(N=15, blue=False)` | Cerrar/abrir sell → Home → search → escribir "piece of unidentified gear" → click Green (2873,356) o Blue (2873,545) → click "order" (2733,746) → click 250 (3284,356) → loop N: click `(3007,555)` + esperar `Success_green.png` + click again |
| `place_orders_rare(N=1)`            | Similar pero clica gear (2873,449), `plus_one_copper`, si NO ve `correct_order.png` revierte con `minus_one_copper`                                                                                                                             |
| `remove_oldest_orders(N=5)`         | Cerrar venta → My Transactions (3700,128) → Buying (2487,358) → ordenar por Price (3558,290) → loop N: click cancel (3732,359)×2 → abrir Sell                                                                                                   |

### Banco / Storage

| Función                     | Resumen                                                                                                                                                                                                 |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `take_all_and_storage(N=1)` | Loop N: cerrar venta → "Take All" (2619,1025) → click scroll-down (2817,1991)×3 → click scroll-up (2816,1725)×2 → loop sobre **32 coords de greens** (grid 4×8) → doble-click cada uno → scroll-down ×2 |

Las 32 coords son una grid: x ∈ {2491, 2575, 2669, 2756}, y ∈ {1340, 1430, 1520, 1610, 1700, 1790, 1880, 1970}.

### Luck

| Función                              | Resumen                                                                                                                                                       |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `consume_purple_luck()`              | Busca `purple_luck.png` → right-click sobre él                                                                                                                |
| `consume_purple_luck_click_button()` | Busca `consume_all.png` → click ×2                                                                                                                            |
| `consume_luck()`                     | Si hay `blue_luck` → corre los 2 anteriores + `handle_errors` + loop sobre [blue, green, yellow, blue]: right-click luck → `move(20,125)` → click ("Consume") |

### Errores / recuperación

| Función             | Trigger                | Acción                                                                                                                                                                                 |
| ------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `handle_errors()`   | `ERR.png`              | click (2367,885)×2 → `restart_game` + `reset_position` + `open_menus` + `use_salvage_kits` + `handle_errors_2` + `manage_rare_gear` + `consume_luck` + `sell_item(motes)` + `sell_all` |
|                     | `ERR_2.png`            | bucle `handle_errors_2()` hasta despejar + ídem cola                                                                                                                                   |
|                     | `select_character.png` | `restart_game` + ... + cola                                                                                                                                                            |
|                     | `windows_desktop.png`  | igual                                                                                                                                                                                  |
| `handle_errors_2()` | —                      | 12 clicks fijos en `(2119,1156)` y `(2129,1181)` (cancelar errores apilados)                                                                                                           |
| `restart_or_not()`  | —                      | Click (2,1176) → si ve `volunteer.png` → click volunteer → `sleep(10)` + `reset_position` + `walk_and_center_npc` + `open_menus`                                                       |

### Boot / menús / posicionamiento

| Función                 | Resumen                                                                                                                                                                                                                                                           |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `open_game()`           | Click icono GW2 (180,2122) → espera client → login (1203,1327)×varias → espera select_character → doble-click character (1600,2015) → espera playing_mode                                                                                                         |
| `restart_game()`        | Alt+F4 → cierra → relanza con `open_game` flow                                                                                                                                                                                                                    |
| `reset_position()`      | Spam ESC hasta `esc_menu.png` → `ctrl+z` → doble-click `portal_scroll` (837,1535) → espera playing_mode → doble-click `mistlock` (744,1535)                                                                                                                       |
| `walk_and_center_npc()` | Loop: matchea 4 imágenes direccionales (Top/Right/Left/Bot-1.png) → llama `handle_direction(dir)` con teclas hold                                                                                                                                                 |
| `handle_direction(dir)` | Combinaciones de teclas hold: top = `3` 4.5s; right = `w` 1s + `k` .78s + `3` 4.5s; left = `w 1s + l .75s + 3 4.5s + q .15s`; bot = `w 1.1s + o + 3 4.5s`                                                                                                         |
| `open_menus()`          | Click (1800,1050) → click cerrar inv (2288,109) → ctrl+z → Tab → caminar `e` 1s → Tab → caminar `q` 1s → drag bank tab (1960,544)→(3141,1086) → shift+z (map blanco) → scroll -500 × ~30 → valida `correct_tpbank.png` y `correct_inventory.png` (sino re-centra) |

### Utilidades

| Función                        | Resumen                                                   |
| ------------------------------ | --------------------------------------------------------- |
| `capture_game_screen()`        | `pyautogui.screenshot((0,0,3840,2160))` → grayscale numpy |
| `search_for_item(img, th)`     | template match con `TM_CCOEFF_NORMED` → loc, w, h         |
| `is_item_present(img, th)`     | bool de lo anterior                                       |
| `does_it_match(img, th=0.7)`   | igual pero devuelve max_val ≥ th                          |
| `can_continue(img, timeout=9)` | poll cada 0.4s hasta encontrar el img con th=0.8          |
| `press_and_hold(key, t)`       | keyboard press + sleep + release                          |
| `drag_window(a,b)`             | mouseDown en a → mover a b con duration=1 → mouseUp       |

---

## 4. Coordenadas clave (4K, viejas, validar contra `bot/coords/3840x2160.json`)

| Nombre             | (x, y)                |
| ------------------ | --------------------- |
| `inventory_area`   | (0,0,2350,2160)       |
| `bank_area`        | (2840,1125,3840,2160) |
| `tp_area`          | (2430,60,3840,1090)   |
| `compact`          | (2240,180)            |
| `take_all`         | (2615,1025)           |
| `rune_crafter`     | (937,1540)            |
| `silver_fed`       | (1017,1540)           |
| `copper_fed`       | (132,1540)            |
| `mistlock`         | (744,1535)            |
| `portal_scroll`    | (837,1535)            |
| `volunteer`        | (78,1176)             |
| `sellers_list`     | (3163,746)            |
| `maximum_amount`   | (3280,358)            |
| `minus_one`        | (2986,362)            |
| `minus_one_copper` | (3240,423)            |
| `plus_one_copper`  | (3240,406)            |
| `list_item`        | (3002,556)            |
| `inventory_close`  | (2288,109)            |

---

## 5. Asunciones y "gotchas"

- Los `time.sleep` están medidos para inventario grande (más items = más tiempo de identify/salvage). En la cuenta nueva con pocos slots **deberían bajar**.
- La cadena `use_silverfed` repite `sell_item(...)`×2 porque a veces el primer click "falla" en la UI (defensa). Si los `can_continue` funcionan bien, con uno basta.
- `handle_errors` puede recursar pesado (corre todo el ciclo de venta/salvage en cada hit). En cuenta nueva probablemente lo simplificas a "loggear y abortar iteración".
- Los confirm buttons del salvage tienen 7 coords distintas por si el popup aparece en distintas posiciones (por items distintos en el stack que abrieron sub-popup). Probablemente con 1-2 alcanza.
- `open_menus()` espera dos NPCs cercanos (Bank + TP) en una posición fija. Es la parte más frágil.

---

## 6. Fases sugeridas para portar (de menos a más)

| Fase  | Objetivo                                            | Funciones a portar                                                                                                                 | Necesita                                                               |
| ----- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **0** | Calibrar coords + templates a 4K en este repo       | (sin código bot)                                                                                                                   | Picker + capturas                                                      |
| **1** | **Sacar greens del banco y procesar 1 stack**       | `take_all_and_storage(1)` simplificado (1 stack), `manage_unidentified_gear()` solo step=1, `use_salvage_kits()` solo rune_crafter | Sólo necesita Bank visible, inv visible, rune_crafter en slot conocido |
| 2     | Vender 1 material                                   | `sell_item(motes.png)`                                                                                                             | TP sell tab visible                                                    |
| 3     | Vender todos los materiales                         | `sell_all()`                                                                                                                       | igual                                                                  |
| 4     | Loop simple: identify → salvage greens → sell motes | Combinar fase 1 + 2 en `for i in range(N)`                                                                                         | igual                                                                  |
| 5     | Rares + Silver Fed                                  | `manage_rare_gear()`, salvage rare con silver_fed                                                                                  |                                                                        |
| 6     | Charms + dust                                       | `manage_charms`, `manage_cristallyne_dust`, `sell_ectos`, `delete_dark_matter`                                                     |                                                                        |
| 7     | Errores                                             | `handle_errors` minimal (solo loggear primero)                                                                                     |                                                                        |
| 8     | Periódicos (`i%10`, `i%25`)                         | `take_all_and_storage`, `place_10_orders`, `remove_oldest_orders`, `sell_most_expensive_exotics`, `salvage_restant_exotics`        |                                                                        |
| 9     | Recuperación dura                                   | `restart_game`, `open_menus`, `reset_position`, `walk_and_center_npc`                                                              | center_character templates                                             |
| 10    | Boot del cliente                                    | `open_game`                                                                                                                        |                                                                        |

---

## 7. Fase 1 mínima — propuesta concreta

Pseudo-código de la primera iteración portable:

```
1. Asumir: GW2 abierto, personaje frente a NPC, banco + inv + TP abiertos.
2. Click banco scroll-up (1 vez) para garantizar verde arriba.
3. Para cada coord en grid greens (32):
     doble-click coord → mueve stack a inv
4. Buscar green.png en inventory_area → si hit → right-click → move(85,205) → click ("Use All")
5. sleep(N) — N a calibrar (antes era 8.5 con 50 slots, probar 3-5)
6. Buscar rune_crafter.png en inv → right-click → "Salvage" → click confirm
7. sleep(N) — antes 20, probar 5
8. Log: "iteración OK"
```

Si esto corre 1 vez sin errores, tienes la espina dorsal. El resto se inserta en orden.
