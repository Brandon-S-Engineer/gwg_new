# Contexto mobs.py

Pega esto al inicio de una conversación nueva.

---

## Qué es

`mobs.py` es un bot visual de farmeo de mobs para Guild Wars 2. Un solo archivo, autocontenido. **Ignora la carpeta `bot/`**, es para un proyecto futuro distinto, no tocar.

## Setup físico

- Corre en **Mac** y controla GW2 que está en **Windows via Parsec**.
- Pantalla: **1440x900 lógico** (Retina 2880x1800).
- Multi-monitor: configurado para `MONITOR_IDX = 1`.
- Dependencias: `pyautogui`, `mss`, `opencv-python`, `numpy`.

## Cómo detecta mobs

- Captura el monitor con `mss`.
- Convierte a HSV, mascara rojo (rangos 0-12 y 170-180, S≥50, V≥30).
- Dilata para juntar letras del nombre en un blob.
- Filtra contornos: aspect ratio ≥2.2 (nameplates son anchos), tamaño dentro de rango.
- Descarta blobs por debajo de `PLAYER_Y - 50` (eso es cuerpo de minion, no nameplate).
- Personaje está fijo en el centro horizontal y al 60% vertical de pantalla.

## Cómo apunta y ataca

- `pick_target`: nameplate más grande = mob más cerca en 3D.
- Click izquierdo sobre el nameplate para seleccionar (GW2 click-to-select).
- Gira cámara con **Q/E** (binds in-game: Camera Rotate Left/Right). **Right-click drag no funciona** vía Parsec en Mac.
- Camina con W, hace `maybe_strafe` ocasional para no ir 100% recto.
- `1` = auto-attack (se repite solo).
- Skills 2-5 vacías por ahora (`SKILL_CDS = {}`).

## HP bar del target (lo último que se agregó)

Cuando seleccionas un mob, GW2 muestra una barra roja arriba al centro. Esa barra:
- **Verifica click**: después de `click_to_select`, esperamos 200ms y chequeamos si apareció.
- **Early exit**: durante engage, si la barra estuvo y desaparece 3 frames seguidos → mob muerto, sale antes de los 12s.
- Zona buscada: `HPBAR_TOP/BOTTOM/LEFT/RIGHT` (32%-68% horizontal, 2%-11% vertical).

## Damage detection

`has_damage_visible(img)`: busca texto blanco brillante (los damage numbers de GW2) en toda la zona de scan. Si lo ve, está pegando → para de caminar.

## Capturas y logs

Siempre activos en modo live.

```
captures/run_YYYY-MM-DD_HH-MM-SS/
  log.txt        timestamps + eventos
  summary.txt    stats al final
  XXX.XXX_HHMMSS_evento.jpg   capturas con overlay
```

Eventos que se capturan:
- `scan` — vagabundeo sin mobs (throttled cada 3s mínimo)
- `engage_start` — al iniciar combate
- `damage_first` — primera vez que aparece daño en ese engage
- `engage_end_hit` — cierre de engage con damage visto
- `engage_end_miss` — cierre sin damage (no le pegó a nada)

Cada captura tiene overlay: rectángulo de scan, círculos verdes en mobs, cyan en el target, cruz en el player.

## Kill switch

NO usa `pynput` (rompe `pyautogui` en Mac). Para parar:
```
touch /Users/bran/Documents/gwg/STOP
```
El bot revisa el archivo cada loop. También responde a Ctrl+C y al failsafe de `pyautogui` (mouse a esquina top-left).

## Flags de ejecución

```
python3 mobs.py                       # corre 60s
python3 mobs.py --duration 120        # corre 120s
python3 mobs.py --show                # ventana con overlay en vivo
python3 mobs.py debug imagen.png      # prueba detección en una imagen
```

## Cosas que NO funcionaron (no volver a intentar)

- **pynput Listener** para kill switch: rompe los eventos de teclado de pyautogui en Mac. File-based STOP es lo único que funciona.
- **Right-click drag para mouselook**: no pasa por Parsec en Mac. Usar Q/E.
- **`closest_to_center` como pick_target**: el target cambia cada scan → bot gira sin parar. Usar `pick_target` (nameplate más grande).
- **`find_mobs_confirmed` (temporal filter, mob debe aparecer en 2 scans)**: rompe detección cuando la cámara está rotando, porque los mobs se mueven cientos de px entre frames.
- **Damage detection cerca del target solamente**: el auto-attack pega a lo que GW2 elige, no siempre al target del bot. Chequear toda la zona de scan.
- **Apuntar a HP bars de mundo (Branded Devourer Nest)**: el filtro de aspect ratio + tamaño + posición arriba del player las descarta. No bajar esos filtros.

## Reglas de trabajo

- **Cambios de a uno**. Probar entre cambios.
- Si aparece un problema que antes no estaba → revertir el último cambio.
- **Español corto y plano**. Frases cortas. Sin em-dash, sin jerga de spec técnico, sin "primitiva/andamiaje/composición".
- Tono "te cuento" en vez de "te explico la arquitectura".
- No tocar `bot/` (proyecto futuro distinto).
- No mockear ni meter abstracciones por si acaso. Si tres líneas resuelven, tres líneas.

## Pendientes posibles

- Detectar si los minions están vivos antes de invocarlos (hoy `summon_minions` está desactivado).
- Ruta de farmeo: detectar POIs de TacO/Blish HUD visualmente (puntos brillantes).
- Cuando todo esté maduro, portar lógica a `bot/` package.
