"""
mobs.py — farmeo visual de mobs en GW2.

Diseñado para correr en Mac y controlar GW2 a través de Parsec.

Controles asumidos (GW2 default + tu remap de E):
  W/A/S/D   moverse
  Tab       target nearest enemy
  1-5       skills (1 = auto-attack)
  6         heal
  F         interact
  E         lock camera (tu remap — el bot no la toca)

PARA DETENER:
  1) Ctrl+C en la terminal (lo más confiable)
  2) Mueve el mouse a la esquina superior izquierda de la pantalla (failsafe)

REQUISITOS en Mac:
  - Permisos de Accesibilidad para Terminal/iTerm (pyautogui)
  - Permisos de Grabación de pantalla para Terminal/iTerm (mss)
  - pip install pyautogui mss opencv-python numpy

Modo debug (sin tocar el juego):
  python3 mobs.py debug ruta/al/screenshot.png
"""

import sys
import time
import random
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

try:
    import mss
    import pyautogui
    pyautogui.FAILSAFE = True
except ImportError:
    mss = None
    pyautogui = None



# ============================================================================
# Monitor — captura del monitor 1
# ============================================================================
if mss is not None:
    _sct = mss.mss()
    MONITOR_IDX = 1                       # 1 = primer monitor, 2 = segundo
    MONITOR = _sct.monitors[MONITOR_IDX]
    SCREEN_W = MONITOR['width']
    SCREEN_H = MONITOR['height']
    OFFSET_X = MONITOR['left']            # offset global cuando hay 2 monitores
    OFFSET_Y = MONITOR['top']
else:
    # Fallback para modo debug sin mss instalado
    SCREEN_W, SCREEN_H = 1920, 1080
    OFFSET_X = OFFSET_Y = 0


# ============================================================================
# Config — tamaños proporcionales a la resolución, así sirve para cualquier res
# ============================================================================
# Zona donde buscar mobs: excluye UI de arriba (objetivos), abajo (skill bar),
# izquierda (íconos de menú) y derecha (panel de quests / dailies — gran fuente
# de falsos positivos por sus textos rojos/naranjas).
SCAN_TOP = int(SCREEN_H * 0.20)
SCAN_BOTTOM = int(SCREEN_H * 0.77)
SCAN_LEFT = int(SCREEN_W * 0.12)
SCAN_RIGHT = int(SCREEN_W * 0.74)

# Posición fija del personaje en pantalla. La cámara está siempre detrás,
# así que tu personaje se renderiza en el mismo punto relativo.
PLAYER_X = SCREEN_W // 2
PLAYER_Y = int(SCREEN_H * 0.60)

# Color de nameplates hostiles en GW2: rojo brillante saturado.
# Rojo en HSV está al inicio (0-10) y al final (170-180) del hue — dos rangos.
# S>=90 V>=50: el texto del nameplate es saturado (S~119) y medio brillante
# (V~76). El terreno rojizo del Brand es oscuro y poco saturado (S~72 V~29),
# así que estos mínimos lo descartan y evitan que inunde la máscara.
RED_HSV_RANGES = [
    (np.array([0, 90, 50]), np.array([12, 255, 255])),
    (np.array([170, 90, 50]), np.array([180, 255, 255])),
]

# Los nameplates de texto son mucho más anchos que altos. Esto descarta
# blobs cuadrados como cuerpos rojos de minions/monstruos.
MIN_NAMEPLATE_ASPECT = 2.2

# Los nameplates SIEMPRE aparecen arriba del personaje (flotan sobre el mob).
# Si la detección queda al nivel del char o más abajo, es un falso positivo
# (cuerpo de minion, efecto de spell, etc).
MAX_NAMEPLATE_Y = PLAYER_Y - 50

# Si la diferencia Y entre tu posición fija y el del mob es menor que esto,
# estás "en rango" para atacar y no hace falta seguir caminando.
# Proporcional al alto de pantalla. Para melee (greatsword) habrá que bajarlo.
CLOSE_ENOUGH_Y = int(SCREEN_H * 0.30)

# En --single: qué tan cerca (dY en px) debe estar el mob para dejar de caminar
# y atacarlo PARADO. Mucho más chico que CLOSE_ENOUGH_Y a propósito. Bajar/subir
# para que pare más cerca o más lejos.
APPROACH_CLOSE_Y = int(SCREEN_H * 0.12)   # ~108 px

# Tamaño esperado de un nameplate, proporcional al ancho de pantalla
MIN_NAME_W = max(20, int(SCREEN_W * 0.015))
MAX_NAME_W = int(SCREEN_W * 0.20)
MIN_NAME_H = max(6, int(SCREEN_H * 0.008))
MAX_NAME_H = int(SCREEN_H * 0.032)

# Cuánto bajar del nameplate al cuerpo del mob
NAMEPLATE_TO_BODY_Y = int(SCREEN_H * 0.04)

# HP bar del target: cuando seleccionas un mob, GW2 muestra arriba al centro
# una barra roja con su nombre. Mientras esté ahí = mob vivo y seleccionado.
# Zona medida sobre captura real (1440x900): barra en x=599 y=117, 174x9 px.
# Fracciones para que aguante otras resoluciones. +3px vertical de margen.
HPBAR_TOP = int(SCREEN_H * 0.1267)     # ~114 px
HPBAR_BOTTOM = int(SCREEN_H * 0.1433)  # ~129 px
HPBAR_LEFT = int(SCREEN_W * 0.4160)    # ~599 px
HPBAR_RIGHT = int(SCREEN_W * 0.5368)   # ~773 px
# Mínimo ancho/alto del blob rojo dentro de la zona para considerarlo "barra"
HPBAR_MIN_WIDTH = int(SCREEN_W * 0.04)
HPBAR_MIN_HEIGHT = max(4, int(SCREEN_H * 0.005))

# Comportamiento
ATTACK_SECONDS = 12.0      # tope máximo de un combate (sale antes si pierde al mob)
WANDER_SECONDS = 1.5       # cuánto vaga si no ve mobs
SCAN_INTERVAL = 0.14       # pausa entre escaneos del loop principal (~7/s)
STARTUP_DELAY = 5          # segundos para que cliques Parsec
SHOW_OVERLAY = False       # se enciende con --show
DURATION = 60              # duración del run en segundos (cambiar con --duration N)
SINGLE_KILL = False        # --single: mata el primer mob confirmado y para el bot

# Estado de la sesión
RECORD = False
RUN_DIR: Path | None = None
RUN_START = 0.0
END_TIME = 0.0

# Cooldowns de skills 2-5 (en segundos). La 1 es auto-attack, no tracking.
# Por ahora vacío — usa solo auto-attack y minions. Re-llenar cuando cambies
# el arma a greatsword (o lo que sea) con los CDs reales.
SKILL_CDS = {}
SKILL_CAST_TIME = 1.0      # tiempo de casteo, durante esto no se puede otra

# Estado de cooldowns (persiste entre engages, los CDs siguen corriendo entre mobs)
_skill_ready_at = {k: 0.0 for k in SKILL_CDS}   # tiempo absoluto en que cada skill está lista
_busy_until = 0.0                                # tiempo absoluto en que termina el casteo actual


# ============================================================================
# Detección
# ============================================================================
@dataclass
class Mob:
    x: int          # coord local del monitor (no global)
    y: int
    name_w: int
    name_h: int


def capture_screen_bgr():
    """Captura el monitor configurado como array BGR."""
    img = np.array(_sct.grab(MONITOR))
    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


# Para temporal filtering: guardamos los mobs del scan anterior.
# Un mob se considera "real" solo si aparece también en el scan anterior.
_PREV_SCAN_MOBS: list = []
CONFIRM_TOLERANCE_PX = 50    # cuánto se puede mover un mob entre scans


def find_mobs_confirmed(image_bgr):
    """
    Encuentra mobs que aparecen en ESTE scan Y en el anterior.
    Filtra falsos positivos transitorios (1-frame flickers en textura, etc).
    """
    global _PREV_SCAN_MOBS
    current = find_mobs(image_bgr)
    confirmed = []
    for mob in current:
        for prev in _PREV_SCAN_MOBS:
            if (abs(mob.x - prev.x) < CONFIRM_TOLERANCE_PX
                    and abs(mob.y - prev.y) < CONFIRM_TOLERANCE_PX):
                confirmed.append(mob)
                break
    _PREV_SCAN_MOBS = current
    return confirmed


def find_mobs(image_bgr):
    """Devuelve lista de Mob encontrados en la zona de búsqueda."""
    roi = image_bgr[SCAN_TOP:SCAN_BOTTOM, SCAN_LEFT:SCAN_RIGHT]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Mascara de rojo (dos rangos combinados)
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lo, hi in RED_HSV_RANGES:
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lo, hi))

    # Dilatar para conectar las letras del nombre en un solo blob
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 3))
    mask = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mobs = []
    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        if not (MIN_NAME_W <= cw <= MAX_NAME_W and MIN_NAME_H <= ch <= MAX_NAME_H):
            continue
        # Aspect ratio: nameplate de texto es mucho más ancho que alto
        if cw / max(ch, 1) < MIN_NAMEPLATE_ASPECT:
            continue
        # Posición del nameplate (sin offset de body)
        plate_y = y + ch + SCAN_TOP
        if plate_y > MAX_NAMEPLATE_Y:
            continue
        mob_x = x + cw // 2 + SCAN_LEFT
        mob_y = plate_y + NAMEPLATE_TO_BODY_Y
        mobs.append(Mob(x=mob_x, y=mob_y, name_w=cw, name_h=ch))
    return mobs


def closest_to_center(mobs):
    cx, cy = SCREEN_W // 2, SCREEN_H // 2
    return min(mobs, key=lambda m: (m.x - cx) ** 2 + (m.y - cy) ** 2)


def pick_target(mobs):
    """
    Elige el mob más cercano físicamente. El nameplate más grande = mob más
    cerca en 3D (por perspectiva). En empates, prefiere el más al centro.
    """
    cx = SCREEN_W // 2
    return max(mobs, key=lambda m: (m.name_w * m.name_h, -abs(m.x - cx)))


def draw_overlay(image_bgr, mobs, current_target=None):
    """Dibuja todo el debugging visual sobre una copia de la imagen."""
    img = image_bgr.copy()

    # Caja del área de escaneo (gris)
    cv2.rectangle(img, (SCAN_LEFT, SCAN_TOP), (SCAN_RIGHT, SCAN_BOTTOM),
                  (80, 80, 80), 2)

    # HP bar del target: zona + estado. Verde si está agarrado el mob, rojo si no.
    # Así en la captura se ve si el click realmente seleccionó algo.
    hp_on = has_target_hp_bar(image_bgr)
    hp_color = (0, 255, 0) if hp_on else (0, 0, 255)
    cv2.rectangle(img, (HPBAR_LEFT, HPBAR_TOP), (HPBAR_RIGHT, HPBAR_BOTTOM),
                  hp_color, 2)
    cv2.putText(img, f"HP bar: {'SI' if hp_on else 'no'}",
                (HPBAR_LEFT, HPBAR_BOTTOM + 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, hp_color, 2)

    # Todos los mobs detectados
    for m in mobs:
        is_target = current_target is not None and m is current_target
        color = (0, 255, 255) if is_target else (0, 0, 255)
        thickness = 3 if is_target else 2
        cv2.rectangle(
            img,
            (m.x - m.name_w // 2, m.y - m.name_h - NAMEPLATE_TO_BODY_Y),
            (m.x + m.name_w // 2, m.y - NAMEPLATE_TO_BODY_Y),
            color, thickness,
        )
        cv2.circle(img, (m.x, m.y), 8, (0, 255, 0), 2)

    # Posición fija del personaje (cruz cyan)
    cv2.drawMarker(img, (PLAYER_X, PLAYER_Y), (255, 200, 0),
                   markerType=cv2.MARKER_CROSS, markerSize=40, thickness=3)

    # Línea de distancia al target activo
    if current_target is not None:
        y_dist = abs(current_target.y - PLAYER_Y)
        in_range = y_dist < CLOSE_ENOUGH_Y
        line_color = (0, 255, 0) if in_range else (0, 165, 255)
        cv2.line(img, (PLAYER_X, PLAYER_Y),
                 (current_target.x, current_target.y), line_color, 2)
        label = f"dY={y_dist} {'en rango' if in_range else 'lejos'}"
        cv2.putText(img, label,
                    (current_target.x + 12, current_target.y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, line_color, 2)

    return img


def show_debug_window(image_bgr, mobs, current_target=None):
    """Si --show está activado, muestra la imagen con overlays en una ventana."""
    if not SHOW_OVERLAY:
        return
    overlay = draw_overlay(image_bgr, mobs, current_target)
    # Mitad de tamaño para que entre cómodo al lado de Parsec
    h, w = overlay.shape[:2]
    small = cv2.resize(overlay, (w // 2, h // 2))
    cv2.imshow('mobs.py - live', small)
    cv2.waitKey(1)


# ============================================================================
# Captures + log + stats (debugging persistente)
# ============================================================================
class RunStats:
    def __init__(self):
        self.scans = 0
        self.mobs_seen_total = 0       # sumatoria de mobs en todos los scans
        self.max_mobs_in_scan = 0
        self.engagements = 0
        self.kills = 0                  # mobs con muerte confirmada (HP bar apareció y desapareció)
        self.damage_frames = 0          # frames donde se detectó damage
        self.lost_targets = 0           # veces que perdió al target durante engage
        self.wanders = 0

    def summary(self, elapsed):
        return [
            f"=== RESUMEN ===",
            f"Duración real:           {elapsed:.1f}s",
            f"Escaneos:                {self.scans}",
            f"Mobs detectados (total): {self.mobs_seen_total}",
            f"Mobs por scan (máx):     {self.max_mobs_in_scan}",
            f"Combates iniciados:      {self.engagements}",
            f"Kills confirmados:       {self.kills}",
            f"Frames con damage:       {self.damage_frames}",
            f"Targets perdidos:        {self.lost_targets}",
            f"Vagabundeos:             {self.wanders}",
        ]

STATS = RunStats()

# Throttling de capturas tipo "scan" (vagabundeo)
_LAST_SCAN_CAPTURE_AT = 0.0
SCAN_CAPTURE_MIN_GAP = 3.0   # segundos mínimos entre dos scan caps

# Cuántas capturas conservar dentro de un run. Al pasarse, se borra la más vieja.
MAX_CAPTURES = 3
# Cuántas carpetas de run conservar. Al arrancar una nueva, se borra la más vieja.
MAX_RUNS = 3

# Kill switch por archivo: el bot revisa si existe `STOP` y se detiene.
# Para parar: en otra terminal, `touch /Users/bran/Documents/gwg/STOP`
STOP_FILE = Path("/Users/bran/Documents/gwg/STOP")


def is_kill_requested():
    """True si el usuario pidió parar el bot (vía archivo STOP)."""
    return STOP_FILE.exists()


def clear_stop_file():
    """Elimina el STOP file por si quedó de un run anterior."""
    if STOP_FILE.exists():
        STOP_FILE.unlink()


def init_run_dir():
    """Crea la carpeta de capturas para esta sesión."""
    global RUN_DIR
    if not RECORD:
        return
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    RUN_DIR = Path("captures") / f"run_{ts}"
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Grabando capturas en: {RUN_DIR}")

    # Dejar solo las MAX_RUNS carpetas de run más nuevas: borrar las más viejas.
    # El nombre lleva la fecha-hora, así que ordenar por nombre = cronológico.
    runs = sorted(RUN_DIR.parent.glob("run_*"))
    for old in runs[:-MAX_RUNS]:
        shutil.rmtree(old, ignore_errors=True)


def log(msg):
    """Imprime y guarda en log.txt con timestamp relativo al run."""
    elapsed = time.time() - RUN_START if RUN_START else 0
    line = f"{elapsed:6.2f}s  {msg}"
    print(line)
    if RECORD and RUN_DIR is not None:
        with open(RUN_DIR / "log.txt", "a") as f:
            f.write(line + "\n")


def save_capture(image_bgr, mobs, current_target, event):
    """Guarda una captura con overlay. event = etiqueta corta (scan, engage, etc.)"""
    if not RECORD or RUN_DIR is None:
        return
    overlay = draw_overlay(image_bgr, mobs, current_target)
    elapsed = time.time() - RUN_START if RUN_START else 0
    # Prefijo con el segundo relativo al inicio + timestamp absoluto
    ts = f"{elapsed:07.3f}_{datetime.now().strftime('%H%M%S')}"
    path = RUN_DIR / f"{ts}_{event}.jpg"
    cv2.imwrite(str(path), overlay, [cv2.IMWRITE_JPEG_QUALITY, 80])

    # Dejar solo las MAX_CAPTURES más nuevas: borrar las más viejas.
    # El nombre arranca con el segundo (con padding) así que ordenar por nombre
    # = orden cronológico.
    caps = sorted(RUN_DIR.glob("*.jpg"))
    for old in caps[:-MAX_CAPTURES]:
        old.unlink()


def save_summary(elapsed):
    """Imprime y guarda summary.txt al final del run."""
    lines = STATS.summary(elapsed)
    text = "\n".join(lines)
    print("\n" + text)
    if RECORD and RUN_DIR is not None:
        (RUN_DIR / "summary.txt").write_text(text + "\n")


# ============================================================================
# Detección de damage (señal de que estamos pegando al mob)
# ============================================================================
def has_damage_visible(image_bgr):
    """
    Busca números de daño en TODO el campo de visión principal.
    No nos importa cerca de qué mob esté — si hay damage visible en pantalla,
    estamos en combate y conectando.

    Los damage numbers son texto blanco brillante grande. Después de dilatar
    los dígitos se conectan en un blob de ~30-120px ancho x 12-50px alto.
    """
    roi = image_bgr[SCAN_TOP:SCAN_BOTTOM, SCAN_LEFT:SCAN_RIGHT]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    # Texto blanco: saturación baja, valor muy alto
    white_mask = ((hsv[:, :, 1] < 50) & (hsv[:, :, 2] > 200)).astype(np.uint8) * 255
    # Dilatar para conectar dígitos del mismo número
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    dilated = cv2.dilate(white_mask, kernel, iterations=1)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        # Damage number ya dilatado: tamaño típico de un número de 2-5 dígitos
        if 25 <= cw <= 130 and 12 <= ch <= 50:
            return True
    return False


def has_target_hp_bar(image_bgr):
    """
    Detecta la HP bar del target en top-center.
    Cuando seleccionas un mob, GW2 muestra arriba al centro una barra roja
    horizontal con su nombre y vida. Si está visible → mob seleccionado y vivo.
    Si desaparece → mob muerto o target perdido.
    """
    roi = image_bgr[HPBAR_TOP:HPBAR_BOTTOM, HPBAR_LEFT:HPBAR_RIGHT]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lo, hi in RED_HSV_RANGES:
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lo, hi))

    # Dilatar horizontal para conectar pixeles de la barra
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (12, 2))
    mask = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        # Barra horizontal: muy ancha, poco alta
        if cw >= HPBAR_MIN_WIDTH and ch >= HPBAR_MIN_HEIGHT and cw / max(ch, 1) >= 4.0:
            return True
    return False


# ============================================================================
# Acciones (input)
# ============================================================================
TURN_LEFT_KEY = 'q'                # bind en GW2: Camera Rotate Left
TURN_RIGHT_KEY = 'e'               # bind en GW2: Camera Rotate Right
TURN_SECONDS_PER_PIXEL = 0.0012    # cuánto tiempo de hold por pixel de desfase
TURN_MAX_SECONDS = 0.5             # tope para no girar más de la cuenta


def click_to_select(mob):
    """
    Click izquierdo en el nameplate del mob para seleccionarlo en GW2.
    Una vez seleccionado, GW2 muestra HP bar, chevron rojo, etc, y el
    auto-attack/skills van directo a este target.
    """
    plate_y = mob.y - NAMEPLATE_TO_BODY_Y
    # Pequeño jitter para no clickear el pixel exacto siempre
    click_x = mob.x + random.randint(-4, 4)
    click_y = plate_y + random.randint(-2, 2)
    # Coords globales del monitor (importante en multi-monitor)
    screen_x = OFFSET_X + click_x
    screen_y = OFFSET_Y + click_y
    pyautogui.click(screen_x, screen_y)


def turn_camera(dx_pixels):
    """
    Gira la cámara con las teclas de rotación de GW2 (Camera Rotate Left/Right).
    En Mac + Parsec el raw mouse input para mouselook no funciona bien, así
    que usamos teclado que sí pasa por Parsec sin problema.

    Requiere que TURN_LEFT_KEY y TURN_RIGHT_KEY estén bindeadas in-game.
    """
    if dx_pixels == 0:
        return
    key = TURN_RIGHT_KEY if dx_pixels > 0 else TURN_LEFT_KEY
    duration = min(abs(dx_pixels) * TURN_SECONDS_PER_PIXEL, TURN_MAX_SECONDS)
    duration = max(duration, 0.06)
    pyautogui.keyDown(key)
    time.sleep(duration)
    human_key_up(key)


def human_press(key):
    """
    Aprieta y suelta una tecla con tiempo de hold aleatorio tipo humano.
    El key-down es instantáneo (la skill castea al apretar), pero el key-up
    se retrasa entre 70 y 180ms para no parecer robot.
    """
    pyautogui.keyDown(key)
    time.sleep(random.uniform(0.07, 0.18))
    pyautogui.keyUp(key)


def human_key_up(key):
    """Suelta una tecla mantenida con un pequeño delay aleatorio antes."""
    time.sleep(random.uniform(0.04, 0.12))
    pyautogui.keyUp(key)


def maybe_strafe():
    """De vez en cuando hace un strafe corto (A o D) para no caminar 100% recto."""
    if random.random() < 0.08:        # ~8% por tick → un strafe cada 4-5s
        key = random.choice(('a', 'd'))
        duration = random.uniform(0.10, 0.25)
        pyautogui.keyDown(key)
        time.sleep(duration)
        human_key_up(key)


def try_cast_skill():
    """
    Si no estamos casteando y hay alguna skill 2-5 lista, la tira.
    Prioriza la de CD más alto (no tiene sentido guardar la 5 si no la usamos).
    Devuelve la tecla casteada o None.
    """
    global _busy_until
    now = time.time()
    if now < _busy_until:
        return None
    ready = [k for k, t in _skill_ready_at.items() if t <= now]
    if not ready:
        return None
    # CD más alto primero (5 antes que 2)
    chosen = max(ready, key=lambda k: SKILL_CDS[k])
    human_press(chosen)
    _busy_until = now + SKILL_CAST_TIME
    _skill_ready_at[chosen] = now + SKILL_CDS[chosen]
    return chosen


def summon_minions():
    """
    Invoca todos los utility + elite (6, 7, 8, 9, 0). Las minions duran
    hasta que mueren, así que solo se llama una vez al arrancar el script.
    """
    print("Invocando minions...")
    for key in ('6', '7', '8', '9', '0'):
        human_press(key)
        time.sleep(random.uniform(0.35, 0.55))


def face_mob(mob):
    dx = mob.x - SCREEN_W // 2
    if abs(dx) > 30:
        turn_camera(dx)


def engage(initial_mob, scan_img=None, scan_mobs=None):
    """
    Apunta, camina hacia el mob y ataca. Re-escanea cada SCAN_TICK para:
      - corregir el rumbo si el mob se movió a un lado
      - parar de caminar si ya no se ve nameplate
      - cambiar de target si aparece otro más cerca
    Sale antes de tiempo si pierde al mob por más de LOST_GRACE segundos.

    scan_img / scan_mobs: imagen y mobs del escaneo del main loop (se reusan
    para el engage_start capture, evita capturar otra vez).
    """
    LOST_GRACE = 1.5         # segundos sin ver mob antes de rendirse
    OFF_CENTER_PX = 150      # más permisivo: solo gira si está muy descentrado
    LOCK_TOLERANCE_PX = 100  # cuánto puede moverse el mob entre scans y seguir siendo "el mismo"

    # Click en el mob para seleccionarlo. El click va sobre la posición donde
    # detectamos el nameplate, ANTES de girar la cámara (porque después de
    # girar, el mob estará en otra posición de pantalla).
    click_to_select(initial_mob)
    time.sleep(0.1)

    face_mob(initial_mob)
    human_press('1')         # arranca auto-attack (se repite solo)

    # engage_start: usar el scan que ya hizo el main loop (sin capturar de nuevo)
    if scan_img is not None:
        save_capture(scan_img, scan_mobs or [initial_mob], initial_mob, 'engage_start')

    pyautogui.keyDown('w')
    walking = True

    # Estado del engagement para el capture final
    damage_seen = False
    damage_captured_once = False
    last_img = scan_img
    last_mobs = scan_mobs or [initial_mob]
    last_target = initial_mob

    no_mob_since = None
    # Cap por ATTACK_SECONDS pero también por el END_TIME global del run
    end = min(time.time() + ATTACK_SECONDS, END_TIME) if END_TIME else time.time() + ATTACK_SECONDS

    try:
        while time.time() < end and not is_kill_requested():
            img = capture_screen_bgr()
            mobs = find_mobs(img)
            last_img = img
            last_mobs = mobs

            if not mobs:
                # Perdimos al mob. Paramos de caminar y esperamos a ver si
                # vuelve a aparecer (puede ser que está justo encima nuestro).
                if walking:
                    human_key_up('w')
                    walking = False
                if no_mob_since is None:
                    no_mob_since = time.time()
                elif time.time() - no_mob_since > LOST_GRACE:
                    log("    target perdido, salgo del engage")
                    STATS.lost_targets += 1
                    break
            else:
                no_mob_since = None

                # Target lock: buscar el mob más cercano a donde estaba el
                # locked en el scan anterior. Si está cerca → es el mismo.
                # Si nadie cerca → murió, elegir nuevo target.
                candidates_near = [
                    m for m in mobs
                    if abs(m.x - last_target.x) < LOCK_TOLERANCE_PX
                    and abs(m.y - last_target.y) < LOCK_TOLERANCE_PX
                ]
                if candidates_near:
                    current = min(
                        candidates_near,
                        key=lambda m: (m.x - last_target.x) ** 2 + (m.y - last_target.y) ** 2
                    )
                else:
                    current = pick_target(mobs)
                    log(f"    target anterior fuera, switch a ({current.x}, {current.y})")
                    # Clickear el nuevo target para que GW2 lo seleccione
                    click_to_select(current)
                last_target = current
                dx = current.x - SCREEN_W // 2

                # Girar SOLO si el locked target está muy descentrado.
                if abs(dx) > OFF_CENTER_PX:
                    turn_camera(dx)
                    human_press('1')

            # Damage detection: si hay damage visible → en combate, paramos.
            # Sino → caminamos para acercarnos.
            dealing_damage = has_damage_visible(img)
            if dealing_damage:
                STATS.damage_frames += 1
                damage_seen = True
                if walking:
                    human_key_up('w')
                    walking = False
                    log("    damage detectado, paro de caminar")
                if not damage_captured_once:
                    save_capture(img, mobs, last_target, 'damage_first')
                    damage_captured_once = True
            else:
                if not walking:
                    pyautogui.keyDown('w')
                    walking = True
                maybe_strafe()

            show_debug_window(img, mobs, current_target=closest_to_center(mobs) if mobs else None)

            # Tirar la mejor skill disponible (respetando CDs y tiempo de casteo)
            cast = try_cast_skill()
            if cast:
                print(f"    skill {cast}")

            time.sleep(random.uniform(0.10, 0.20))
    finally:
        if walking:
            human_key_up('w')
        # Capture final del engagement: hit (con damage) o miss (al aire)
        end_label = 'engage_end_hit' if damage_seen else 'engage_end_miss'
        save_capture(last_img, last_mobs, last_target, end_label)


def kill_target(mob, scan_img=None, scan_mobs=None):
    """
    Flujo para --single:
      1. Click en el mob para seleccionarlo. Espera 1s.
      2. Si la HP bar está roja (mob agarrado) → camina de frente SOLO mientras
         esté lejos (dY > APPROACH_CLOSE_Y).
      3. Cuando queda cerca, suelta la W y lo mata PARADO con '1'.
      4. Termina cuando la barra desaparece 1s seguido = muerto.
    No corre hacia la manada: para apenas el mob está cerca y se queda quieto.
    Devuelve True si confirmó la muerte, False si no agarró el mob o no murió.
    """
    HP_BAR_GONE_SECONDS = 1.0     # segundos sin barra (sostenido) para cantar muerte
    LOCK_TOLERANCE_PX = 120       # cuánto se mueve el mob entre scans y sigue siendo el mismo

    click_to_select(mob)
    time.sleep(1.0)

    img = capture_screen_bgr()
    if not has_target_hp_bar(img):
        log("    sin HP bar tras click, no agarré el mob")
        show_debug_window(img, scan_mobs or [mob], mob)
        save_capture(img, scan_mobs or [mob], mob, 'engage_end_miss')
        return False

    log("    HP bar roja, mob agarrado")
    save_capture(img, scan_mobs or [mob], mob, 'engage_start')

    face_mob(mob)

    damage_seen = False
    damage_captured_once = False
    hp_bar_gone_since = None
    last_target = mob
    last_img = img
    walking = False

    end = min(time.time() + ATTACK_SECONDS, END_TIME) if END_TIME else time.time() + ATTACK_SECONDS
    try:
        while time.time() < end and not is_kill_requested():
            human_press('1')
            time.sleep(random.uniform(0.30, 0.50))

            img = capture_screen_bgr()
            last_img = img
            mobs = find_mobs(img)

            # Seguir al mismo mob: el más cercano a donde estaba antes.
            near = [m for m in mobs
                    if abs(m.x - last_target.x) < LOCK_TOLERANCE_PX
                    and abs(m.y - last_target.y) < LOCK_TOLERANCE_PX]
            if near:
                last_target = min(near, key=lambda m: (m.x - last_target.x) ** 2
                                  + (m.y - last_target.y) ** 2)
            show_debug_window(img, mobs, last_target)

            # Caminar SOLO si está lejos. Apenas se acerca, parar y atacar parado.
            dY = abs(last_target.y - PLAYER_Y)
            if dY > APPROACH_CLOSE_Y:
                if not walking:
                    pyautogui.keyDown('w')
                    walking = True
            else:
                if walking:
                    human_key_up('w')
                    walking = False

            if has_damage_visible(img):
                STATS.damage_frames += 1
                damage_seen = True
                if not damage_captured_once:
                    save_capture(img, mobs, last_target, 'damage_first')
                    damage_captured_once = True

            if has_target_hp_bar(img):
                hp_bar_gone_since = None
            else:
                now = time.time()
                if hp_bar_gone_since is None:
                    hp_bar_gone_since = now
                elif now - hp_bar_gone_since >= HP_BAR_GONE_SECONDS:
                    log("    HP bar ausente >1s, mob muerto")
                    STATS.kills += 1
                    save_capture(last_img, mobs, last_target, 'engage_end_kill')
                    return True
    finally:
        if walking:
            human_key_up('w')

    # Salió por timeout sin confirmar muerte
    save_capture(last_img, [last_target], last_target,
                 'engage_end_hit' if damage_seen else 'engage_end_miss')
    return False


def wander():
    """
    Buscar mobs en otra dirección. Primero gira fuerte (puede haber mobs
    detrás o a los lados), luego camina un poco hacia adelante.
    """
    turn = random.choice([-1, 1]) * random.randint(250, 500)
    turn_camera(turn)
    time.sleep(random.uniform(0.15, 0.35))
    pyautogui.keyDown('w')
    time.sleep(random.uniform(WANDER_SECONDS * 0.7, WANDER_SECONDS * 1.3))
    human_key_up('w')


def release_all_keys():
    """Suelta cualquier tecla o botón que pudiera haber quedado presionado."""
    for k in ('w', 'a', 's', 'd', '1', '2', '3', '4', '5',
              TURN_LEFT_KEY, TURN_RIGHT_KEY):
        try:
            pyautogui.keyUp(k)
        except Exception:
            pass
    # Soltar botón derecho por si quedó colgado en un right-click drag
    try:
        pyautogui.mouseUp(button='right')
    except Exception:
        pass


# ============================================================================
# Modo debug — probar la detección con una imagen estática
# ============================================================================
def debug_image(path):
    img = cv2.imread(path)
    if img is None:
        print(f"No se pudo leer {path}")
        return

    h, w = img.shape[:2]
    print(f"Imagen original: {w}x{h}")
    print(f"Resolución del monitor: {SCREEN_W}x{SCREEN_H}")

    # Si la imagen no coincide con la resolución del monitor (típico en Mac
    # retina: screenshot a 2x), la escalamos para que la lógica de scan funcione.
    if (w, h) != (SCREEN_W, SCREEN_H):
        print(f"Escalando a {SCREEN_W}x{SCREEN_H} para que coincida con el monitor")
        img = cv2.resize(img, (SCREEN_W, SCREEN_H))

    print(f"Zona de scan: X [{SCAN_LEFT}-{SCAN_RIGHT}], Y [{SCAN_TOP}-{SCAN_BOTTOM}]")
    print(f"Tamaño nameplate aceptado: W [{MIN_NAME_W}-{MAX_NAME_W}], "
          f"H [{MIN_NAME_H}-{MAX_NAME_H}]")
    print(f"Posición fija del personaje: ({PLAYER_X}, {PLAYER_Y})")

    mobs = find_mobs(img)
    print(f"\nMobs detectados: {len(mobs)}")
    for i, m in enumerate(mobs):
        y_dist = abs(m.y - PLAYER_Y)
        print(f"  #{i}: x={m.x} y={m.y} (nameplate {m.name_w}x{m.name_h}, dY={y_dist})")

    target = closest_to_center(mobs) if mobs else None
    overlay = draw_overlay(img, mobs, current_target=target)
    out_path = 'debug_out.png'
    cv2.imwrite(out_path, overlay)
    print(f"\nGuardado: {out_path}")


# ============================================================================
# Main loop
# ============================================================================
def main():
    global RUN_START, END_TIME
    print(f"mobs.py — monitor {MONITOR_IDX}: {SCREEN_W}x{SCREEN_H} "
          f"(offset {OFFSET_X},{OFFSET_Y})")
    print(f"Duración del run: {DURATION}s")
    print()
    print("PARA DETENER ANTES:")
    print("  • Ctrl+C en esta terminal")
    print("  • O mueve el mouse a la esquina top-left de la pantalla")
    print()
    print(f"Haz click en la ventana de Parsec AHORA.")
    for n in range(STARTUP_DELAY, 0, -1):
        print(f"  empieza en {n}...")
        time.sleep(1)

    RUN_START = time.time()
    END_TIME = RUN_START + DURATION

    clear_stop_file()
    print(f"Kill switch: en otra terminal corre `touch {STOP_FILE}` para detener.\n")

    # summon_minions desactivado por ahora (después se hará detección automática
    # de si los minions están vivos antes de invocarlos)
    log("Inicio del run, cazando")

    try:
        while time.time() < END_TIME and not is_kill_requested():
            img = capture_screen_bgr()
            mobs = find_mobs(img)
            target = closest_to_center(mobs) if mobs else None
            show_debug_window(img, mobs, target)

            STATS.scans += 1
            if mobs:
                STATS.mobs_seen_total += len(mobs)
                STATS.max_mobs_in_scan = max(STATS.max_mobs_in_scan, len(mobs))

            if target:
                STATS.engagements += 1
                log(f"engage → mob en ({target.x}, {target.y}), "
                    f"nameplate {target.name_w}x{target.name_h}")
                if SINGLE_KILL:
                    killed = kill_target(target, scan_img=img, scan_mobs=mobs)
                    if killed:
                        log("kill confirmado, modo --single → fin del run")
                        break
                else:
                    engage(target, scan_img=img, scan_mobs=mobs)
            else:
                # Capturar scan throttled (solo durante vagabundeo)
                global _LAST_SCAN_CAPTURE_AT
                now = time.time()
                if now - _LAST_SCAN_CAPTURE_AT >= SCAN_CAPTURE_MIN_GAP:
                    save_capture(img, mobs, target, 'scan')
                    _LAST_SCAN_CAPTURE_AT = now
                STATS.wanders += 1
                log("vagabundeo (sin mobs)")
                wander()

            time.sleep(random.uniform(SCAN_INTERVAL * 0.7, SCAN_INTERVAL * 1.4))
    except KeyboardInterrupt:
        log("Detenido por Ctrl+C")
    except pyautogui.FailSafeException:
        log("Detenido por failsafe (mouse en esquina)")
    finally:
        if is_kill_requested():
            log("Detenido por archivo STOP")
            clear_stop_file()
        release_all_keys()
        if SHOW_OVERLAY:
            cv2.destroyAllWindows()
        elapsed = time.time() - RUN_START
        save_summary(elapsed)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == 'debug':
        debug_image(sys.argv[2])
    else:
        if pyautogui is None or mss is None:
            print("Faltan dependencias. Instala:")
            print("  pip3 install pyautogui mss opencv-python numpy")
            sys.exit(1)
        # Modo single: caza hasta confirmar 1 kill y para
        if '--single' in sys.argv:
            SINGLE_KILL = True
        # Flag para mostrar overlay en vivo
        if '--show' in sys.argv:
            SHOW_OVERLAY = True
            cv2.namedWindow('mobs.py - live', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('mobs.py - live', SCREEN_W // 2, SCREEN_H // 2)
            try:
                cv2.setWindowProperty('mobs.py - live',
                                      cv2.WND_PROP_TOPMOST, 1.0)
            except Exception:
                pass
        # Duración del run (default 60s)
        if '--duration' in sys.argv:
            idx = sys.argv.index('--duration')
            if idx + 1 < len(sys.argv):
                try:
                    DURATION = int(sys.argv[idx + 1])
                except ValueError:
                    print(f"--duration debe ser un entero, ignorando")
        # Recording siempre activo en modo live
        RECORD = True
        init_run_dir()
        main()
