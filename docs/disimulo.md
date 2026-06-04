# Disimulo — comportamiento humano del bot

Guía viva de reglas para que el bot no se vea como bot. Cada vez que detectemos un patrón delator, lo apuntamos aquí.

## Principios

1. **Nada exacto.** Ningún número que sea siempre el mismo: ni coords, ni delays, ni tiempos de hold, ni rutas.
2. **Llegar bien, llegar variado.** El destino del click debe caer dentro del target, pero nunca al mismo pixel dos veces.
3. **Velocidad humana.** Ni teleport ni lento de sobra. Movimientos cortos rápidos, largos más lentos (la mano humana acelera y frena).
4. **Pausas naturales.** Entre acciones, mini-pausas variables. Cada N ciclos, una pausa más larga (mirar mapa, leer chat).
5. **Romper el patrón temporal.** No hacer la misma rutina exactamente cada X segundos. Variar duración total de sesión y horario del día.

## Implementado

### Movimiento del mouse ([bot/input.py](../bot/input.py))

- **Jitter de posición**: `POS_JITTER = 3` → cada click cae en `(x±3, y±3)`. Suficiente para no ser detectable, no tanto que falle templates de ~24px o más.
- **Duración escalada con distancia**: la duración del move depende de cuán lejos esté el cursor del target. Mano humana: movimientos cortos ~0.12s, largos hasta ~0.6s.
- **Easing `easeInOutQuad`**: arranque y final suaves, pico de velocidad en medio. No es lineal (eso sí grita "bot").
- **Hold del click**: tiempo entre press y release randomizado 0.05-0.12s.
- **Pre/post click sleep**: pausa antes y después del click, randomizada.

### Sleeps ([bot/input.py](../bot/input.py))

- `inp.sleep(seconds, jitter=0.15)` aplica ±15% al delay por defecto.

## Pendiente / por agregar

- **Pausas largas aleatorias**: cada cierto número de ciclos, un sleep de 5-30s (simular AFK corto).
- **Variación de orden**: cuando hay 2+ acciones independientes, alternarlas aleatoriamente en lugar de siempre el mismo orden.
- **Overshoot ocasional**: 1 de cada N moves, pasarse un poco del target y regresar (humano se pasa a veces).
- **Movimientos parásitos**: mover el cursor a posiciones random del juego entre acciones (como cuando uno "piensa").
- **Cerrar el picker antes de farmear**: dejar el `region_picker.html` abierto deja una ventana sospechosa.
- **Variar duración de sesión**: no farmear siempre 4 horas exactas.
- **No farmear en una sola zona**: rotar maps/instancias si la rutina lo permite.

## Cosas que NO hacer

- Hooks globales de teclado innecesarios (`keyboard` package los registra a nivel del SO; si no los uso, no los importo).
- Dejar ventanas con el código del bot abiertas mientras juego (VS Code con el `.py` visible en screenshots).
- Procesos con nombres delatores. `python.exe` está bien (común). `gw2_bot.exe` no.
- Inyección de memoria / DLL / kernel drivers. Nuestro bot es 100% visual + clicks normales; mantenerlo así.

## Referencias

- [reference_old.md](reference_old.md) — el bot viejo no era baneable por esto, fue por otra razón.
