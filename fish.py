"""fish.py — solo el minijuego: mueve la barra amarilla (2/3) para seguir la verde.

Uso (Mac: python3, Windows: py):
  python3 fish.py calib            click en esquinas de la barra -> imprime BAR_REGION
  python3 fish.py calib alert      click en esquinas de la zona del "!" -> ALERT_REGION
  python3 fish.py snap             cada click guarda la zona del "!" en captures/alert/
  python3 fish.py watch            igual pero sin tocar teclas
Capturas + frames.csv (captures/fish/): descomentar rec en run()
  python3 fish.py                  detecta el minijuego solo
Salir: Ctrl+C en la terminal, o mouse a la esquina arriba-izquierda.
  python3 fish.py debug img.png    prueba la detección sobre una captura
"""

import random
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()

try:
    import mss
    _sct = getattr(mss, "MSS", getattr(mss, "mss", None))()
except ImportError:
    _sct = None

import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# (x, y, w, h) de la franja de la barra. Sacarlo con `python3 fish.py calib`.
BAR_REGION = (642, 733, 171, 28)

# Zona del "!" rojo sobre la cabeza. None = no lanza ni recoge solo.
ALERT_REGION = (701, 484, 77, 88)

KEY_LEFT = "2"
KEY_RIGHT = "3"
KEY_CAST = "1"

# "!" rojo
RED_HSV = (((0, 120, 110), (10, 255, 255)), ((170, 120, 110), (180, 255, 255)))
ALERT_MIN_FRAC = 0.006  # "!" llena ~1.5% de la zona; sin "!" da 0
ALERT_FRAMES = 2
ALERT_COOLDOWN_S = 4.0  # tras apretar 1, no volver a reaccionar
REACT_ALERT_MS = (220, 420)

# Nodo
AUTO_CASTS = 3          # relanza solo tras las primeras 3; luego lanzas tú
RECAST_DELAY_S = (3.0, 3.2)
SAME_NODE_GAP_S = 20.0  # fin de minijuego -> "!" en menos de esto = mismo nodo

YELLOW_HSV = ((5, 100, 45), (34, 255, 255))
GREEN_HSV = ((38, 70, 140), (75, 255, 255))
BAND = (0.3, 0.8)       # filas de la barra (fracción del alto); fuera quedan íconos
YELLOW_COL_PX = 2       # con la verde adentro solo quedan los 2 bordes amarillos
GREEN_COL_PX = 5
MIN_WIDTH = 4           # ancho mínimo del blob

TICK = 0.012
CONFIRM_FRAMES = 3      # frames seguidos con ambas barras antes de actuar
LOST_FRAMES = 8         # frames sin barras -> minijuego terminado
FROZEN_FRAMES = 6       # barras quietas -> pez atrapado, soltar (3 daba falsos en juego)
FROZEN_TOL = 1          # px; atrapado tiembla ±1, moviendo avanza ~1/frame

# Medido en el juego vía Parsec (frames.csv)
LATENCY_S = 0.20        # tecla -> la amarilla se mueve
BAR_SPEED_YW = 1.08     # velocidad amarilla en anchos-amarillos/s (~40 px/s)
VEL_WINDOW_S = 0.08     # ventana para la velocidad de la verde

# Humanización
REACT_MS = (10, 35)
DZ_ON = (0.03, 0.07)    # fracción del ancho amarillo: empezar a mover
DZ_OFF = (0.00, 0.02)   # dejar de mover
LOOKAHEAD_S = (0.04, 0.09)  # extra sobre LATENCY_S para la verde
MIN_HOLD_MS = (15, 35)


def grab(region):
    x, y, w, h = region
    if _sct:
        img = np.array(_sct.grab({"left": x, "top": y, "width": w, "height": h}))
        return img[:, :, :3]
    return cv2.cvtColor(np.array(pyautogui.screenshot(region=region)), cv2.COLOR_RGB2BGR)


def _span(mask, min_px):
    cols = np.flatnonzero((mask > 0).sum(0) >= min_px)
    if cols.size == 0:
        return None
    # run más largo de columnas contiguas
    splits = np.flatnonzero(np.diff(cols) > 2) + 1
    run = max(np.split(cols, splits), key=len)
    if len(run) < MIN_WIDTH:
        return None
    return int(run[0]), int(run[-1])


def detect(img):
    """-> (yellow_span, green_span); cada uno (x0, x1) o None."""
    h = img.shape[0]
    hsv = cv2.cvtColor(img[int(h * BAND[0]):int(h * BAND[1])], cv2.COLOR_BGR2HSV)
    return (_span(cv2.inRange(hsv, *YELLOW_HSV), YELLOW_COL_PX),
            _span(cv2.inRange(hsv, *GREEN_HSV), GREEN_COL_PX))


def _ms(r):
    return random.uniform(*r) / 1000


class Keys:
    def __init__(self):
        self.held = None

    def _down(self, k):
        pyautogui.keyDown(k)

    def _up(self, k):
        pyautogui.keyUp(k)

    def set(self, k):
        if k == self.held:
            return
        if self.held:
            self._up(self.held)
        if k:
            self._down(k)
        self.held = k

    def release(self):
        self.set(None)

    def tap(self, k):
        pyautogui.keyDown(k)
        time.sleep(_ms((60, 120)))
        pyautogui.keyUp(k)


class Chaser:
    """Un minijuego: hold 2/3 compensando la latencia de Parsec."""

    _DIR = {None: 0, KEY_RIGHT: 1, KEY_LEFT: -1}

    def __init__(self, keys):
        self.keys = keys
        self.dz_on = random.uniform(*DZ_ON)
        self.dz_off = random.uniform(*DZ_OFF)
        self.look = LATENCY_S + random.uniform(*LOOKAHEAD_S)
        self.gh = deque()
        self.cmds = deque([(0.0, 0)], maxlen=50)
        self.pending = None
        self.pending_at = 0.0
        self.changed_at = 0.0
        self.recent = deque(maxlen=FROZEN_FRAMES + 1)
        self.caught = False

    def _green_vel(self):
        if len(self.gh) < 3:
            return 0.0
        t, g = np.array(self.gh).T
        return float(np.polyfit(t - t[-1], g, 1)[0])

    def _in_flight(self, now, speed):
        """Movimiento de teclas ya mandadas que el juego aún no muestra."""
        total, t_end = 0.0, now
        for t, u in reversed(self.cmds):
            t0 = max(t, now - LATENCY_S)
            if t_end > t0:
                total += u * speed * (t_end - t0)
            if t <= now - LATENCY_S:
                break
            t_end = t
        return total

    def step(self, ys, gs, now):
        if self.caught:
            return
        self.recent.append((*ys, *gs))
        if len(self.recent) == self.recent.maxlen and all(
                abs(a - b) <= FROZEN_TOL for f in self.recent for a, b in zip(f, self.recent[0])):
            print("[fish] barras quietas, suelto")
            self.keys.release()
            self.caught = True
            return
        yc = (ys[0] + ys[1]) / 2
        gc = (gs[0] + gs[1]) / 2
        yw = max(ys[1] - ys[0], 1)
        self.gh.append((now, gc))
        while self.gh[0][0] < now - VEL_WINDOW_S:
            self.gh.popleft()

        err = (gc + self._green_vel() * self.look) - (yc + self._in_flight(now, yw * BAR_SPEED_YW))
        cur = self.keys.held
        if cur is None:
            want = None if abs(err) < yw * self.dz_on else (KEY_RIGHT if err > 0 else KEY_LEFT)
        else:
            dir_ok = (err > 0) == (cur == KEY_RIGHT)
            want = cur if dir_ok and abs(err) > yw * self.dz_off else None

        if want == cur:
            self.pending = None
            return
        if now - self.changed_at < _ms(MIN_HOLD_MS):
            return
        if self.pending != want:
            self.pending = want
            self.pending_at = now + _ms(REACT_MS)
        if now >= self.pending_at:
            self.keys.set(want)
            self.cmds.append((now, self._DIR[want]))
            self.changed_at = now
            self.pending = None


SAVE_EVERY = 0.25       # watch: franja cada 0.25 s
CTX_EVERY = 2.0         # watch: contexto alrededor cada 2 s
CTX_PAD = 80
MAX_SAVES = 600


class Recorder:
    def __init__(self):
        self.dir = Path("captures/fish") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.dir.mkdir(parents=True, exist_ok=True)
        self.n = 0
        self.last = self.last_ctx = 0.0
        self.prev_state = None
        self.csv = open(self.dir / "frames.csv", "w", buffering=1)
        self.csv.write("t,y0,y1,g0,g1,key\n")
        print(f"[fish] guardando en {self.dir}")

    def __call__(self, img, ys, gs, key, now):
        state = (ys is not None, gs is not None)
        changed = state != self.prev_state
        self.prev_state = state
        if ys or gs or changed:
            y0, y1 = ys or ("", "")
            g0, g1 = gs or ("", "")
            self.csv.write(f"{now:.4f},{y0},{y1},{g0},{g1},{key or ''}\n")
        if not (ys or gs or changed):
            return
        if self.n >= MAX_SAVES or not (changed or now - self.last >= SAVE_EVERY):
            return
        self.last = now
        self.n += 1
        tag = lambda c, sp: f"{c}{sp[0]}-{sp[1]}" if sp else f"{c}-"
        cv2.imwrite(str(self.dir / f"{self.n:04d}_{tag('y', ys)}_{tag('g', gs)}.png"), img)
        if now - self.last_ctx >= CTX_EVERY:
            self.last_ctx = now
            x, y, w, h = BAR_REGION
            ctx = grab((max(0, x - CTX_PAD), max(0, y - CTX_PAD), w + 2 * CTX_PAD, h + 2 * CTX_PAD))
            cv2.imwrite(str(self.dir / f"{self.n:04d}_ctx.png"), ctx)


def _failsafe():
    x, y = pyautogui.position()
    return 0 <= x <= 2 and 0 <= y <= 2  # hay monitor con coords negativas


def _region_visible(region):
    if not _sct:
        return True
    x, y, w, h = region
    return any(m["left"] <= x and m["top"] <= y and x + w <= m["left"] + m["width"]
               and y + h <= m["top"] + m["height"] for m in _sct.monitors[1:])


def alert_on(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    red = sum(cv2.countNonZero(cv2.inRange(hsv, lo, hi)) for lo, hi in RED_HSV)
    return red >= ALERT_MIN_FRAC * img.shape[0] * img.shape[1], red


def run(dry=False):
    for name, reg in (("BAR_REGION", BAR_REGION), ("ALERT_REGION", ALERT_REGION)):
        if reg and not _region_visible(reg):
            print(f"[fish] OJO: {name}={reg} no cae en ningún monitor. Corre calib.")
    keys = Keys()
    chaser = None
    seen = lost = alert_seen = 0
    node_n = 0              # peces en el nodo actual
    last_end = None
    recast_at = None
    alert_block = 0.0
    # rec = Recorder()  # capturas + frames.csv para afinar
    print(f"[fish] bar={BAR_REGION} alert={ALERT_REGION} dry={dry}  esperando...")
    try:
        while not _failsafe():
            t0 = time.perf_counter()
            img = grab(BAR_REGION)
            ys, gs = detect(img)
            if ys and gs:
                seen += 1
                lost = 0
                if seen >= CONFIRM_FRAMES:
                    if chaser is None:
                        print("[fish] minijuego")
                        chaser = Chaser(keys)
                        recast_at = None
                    if dry:
                        print(f"amarillo={ys} verde={gs}")
                    else:
                        chaser.step(ys, gs, t0)
            else:
                seen = 0
                lost += 1
                if chaser and lost >= LOST_FRAMES:
                    keys.release()
                    chaser = None
                    node_n += 1
                    last_end = t0
                    alert_block = t0 + 1.0
                    if ALERT_REGION and node_n < AUTO_CASTS:
                        recast_at = t0 + random.uniform(*RECAST_DELAY_S)
                        print(f"[fish] pez #{node_n}, relanzo en {recast_at - t0:.1f}s")
                    else:
                        print(f"[fish] pez #{node_n}, lanza tú")

            if ALERT_REGION and chaser is None:
                on, red = alert_on(grab(ALERT_REGION))
                alert_seen = alert_seen + 1 if on else 0
                if dry and red:
                    print(f"rojo={red}px {'-> !' if on else ''}")
                if alert_seen >= ALERT_FRAMES and t0 >= alert_block:
                    if last_end is None or t0 - last_end > SAME_NODE_GAP_S:
                        if node_n:
                            print("[fish] nodo nuevo")
                        node_n = 0
                    print(f"[fish] ! -> {KEY_CAST} (pez #{node_n + 1})")
                    alert_block = t0 + ALERT_COOLDOWN_S
                    recast_at = None
                    if not dry:
                        time.sleep(_ms(REACT_ALERT_MS))
                        keys.tap(KEY_CAST)
                if recast_at and t0 >= recast_at:
                    recast_at = None
                    alert_block = t0 + 1.0
                    print(f"[fish] relanzo ({KEY_CAST})")
                    if not dry:
                        keys.tap(KEY_CAST)
            # rec(img, ys, gs, keys.held, t0)
            time.sleep(max(0.0, TICK - (time.perf_counter() - t0)))
    except KeyboardInterrupt:
        pass
    finally:
        keys.release()
        print("[fish] apagado")


def _mouse_down():
    if sys.platform == "win32":
        return bool(ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000)
    from Quartz import (CGEventSourceButtonState, kCGEventSourceStateCombinedSessionState,
                        kCGMouseButtonLeft)
    return CGEventSourceButtonState(kCGEventSourceStateCombinedSessionState, kCGMouseButtonLeft)


def _wait_click():
    while _mouse_down():
        time.sleep(0.01)
    while not _mouse_down():
        time.sleep(0.01)
    pos = pyautogui.position()
    while _mouse_down():
        time.sleep(0.01)
    return pos


def calib(what="bar"):
    name, label = {"bar": ("BAR_REGION", "la barra"),
                   "alert": ("ALERT_REGION", 'la zona del "!" (arriba de la cabeza)')}[what]
    pts = []
    for corner in ("arriba-izquierda", "abajo-derecha"):
        print(f"Click en la esquina {corner} de {label}...")
        pts.append(_wait_click())
        print(f"  {pts[-1]}")
    (x0, y0), (x1, y1) = pts
    print(f"{name} = ({min(x0, x1)}, {min(y0, y1)}, {abs(x1 - x0)}, {abs(y1 - y0)})")


def snap():
    out = Path("captures/alert")
    out.mkdir(parents=True, exist_ok=True)
    x, y, w, h = ALERT_REGION
    print("Click cuando salga el '!'. Ctrl+C para salir.")
    try:
        while True:
            _wait_click()
            img = grab(ALERT_REGION)
            ctx = grab((x - 60, y - 60, w + 120, h + 120))
            on, red = alert_on(img)
            name = datetime.now().strftime("%H%M%S_%f")[:9]
            cv2.imwrite(str(out / f"snap_{name}.png"), img)
            cv2.imwrite(str(out / f"snap_{name}_ctx.png"), ctx)
            print(f"  guardada snap_{name}  rojo={red}px {'-> detecta !' if on else '-> NO detecta'}")
    except KeyboardInterrupt:
        pass


def debug(path):
    img = cv2.imread(path)
    ys, gs = detect(img)
    print(f"amarillo={ys} verde={gs}")
    out = img.copy()
    for span, color in ((ys, (0, 200, 255)), (gs, (0, 255, 0))):
        if span:
            cv2.rectangle(out, (span[0], 0), (span[1], out.shape[0] - 1), color, 1)
    cv2.imwrite("debug_fish.png", out)
    print("-> debug_fish.png")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "calib":
        calib(sys.argv[2] if len(sys.argv) > 2 else "bar")
    elif mode == "snap":
        snap()
    elif mode == "watch":
        run(dry=True)
    elif mode == "debug":
        debug(sys.argv[2])
    else:
        run()
