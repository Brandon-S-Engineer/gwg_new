"""fish.py — solo el minijuego: mueve la barra amarilla (2/3) para seguir la verde.

Uso:
  py fish.py calib            marcar esquinas de la barra -> imprime BAR_REGION
  py fish.py watch            solo detecta e imprime, no toca teclas
  py fish.py                  corre (Ctrl+C para salir)
  py fish.py debug img.png    prueba la detección sobre una captura
"""

import random
import sys
import time

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

try:
    import keyboard as _kb
except ImportError:
    _kb = None

# (x, y, w, h) de la franja de la barra. Sacarlo con `py fish.py calib`.
BAR_REGION = (0, 0, 300, 30)

KEY_LEFT = "2"
KEY_RIGHT = "3"

YELLOW_HSV = ((5, 100, 45), (34, 255, 255))
GREEN_HSV = ((38, 70, 140), (75, 255, 255))
MIN_COL_PX = 6          # px por columna para contarla
MIN_WIDTH = 4           # ancho mínimo del blob

TICK = 0.012
CONFIRM_FRAMES = 3      # frames seguidos con ambas barras antes de actuar
LOST_FRAMES = 8         # frames sin barras -> minijuego terminado

# Humanización
REACT_MS = (55, 130)
DZ_ON = (0.10, 0.20)    # fracción del ancho amarillo: empezar a mover
DZ_OFF = (0.03, 0.08)   # dejar de mover
LOOKAHEAD_S = (0.06, 0.12)
MIN_HOLD_MS = (35, 70)


def grab(region):
    x, y, w, h = region
    if _sct:
        img = np.array(_sct.grab({"left": x, "top": y, "width": w, "height": h}))
        return img[:, :, :3]
    return cv2.cvtColor(np.array(pyautogui.screenshot(region=region)), cv2.COLOR_RGB2BGR)


def _span(mask):
    cols = np.flatnonzero((mask > 0).sum(0) >= MIN_COL_PX)
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
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    y = cv2.inRange(hsv, *YELLOW_HSV)
    g = cv2.inRange(hsv, *GREEN_HSV)
    g_span = _span(g)
    if g_span:
        y[:, g_span[0]:g_span[1] + 1] = 0  # el verde dentro del amarillo no lo ensucia
    return _span(y), g_span


def _ms(r):
    return random.uniform(*r) / 1000


class Keys:
    def __init__(self):
        self.held = None

    def _down(self, k):
        _kb.press(k) if _kb else pyautogui.keyDown(k)

    def _up(self, k):
        _kb.release(k) if _kb else pyautogui.keyUp(k)

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


class Chaser:
    """Un minijuego: hold 2/3 con histéresis, predicción y retardo humano."""

    def __init__(self, keys):
        self.keys = keys
        self.dz_on = random.uniform(*DZ_ON)
        self.dz_off = random.uniform(*DZ_OFF)
        self.look = random.uniform(*LOOKAHEAD_S)
        self.prev = None
        self.vel = 0.0
        self.pending = None
        self.pending_at = 0.0
        self.changed_at = 0.0

    def step(self, ys, gs, now):
        yc = (ys[0] + ys[1]) / 2
        gc = (gs[0] + gs[1]) / 2
        yw = max(ys[1] - ys[0], 1)
        if self.prev:
            pc, pt = self.prev
            dt = now - pt
            if dt > 0:
                self.vel = 0.6 * self.vel + 0.4 * (gc - pc) / dt
        self.prev = (gc, now)

        err = gc + self.vel * self.look - yc
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
            self.changed_at = now
            self.pending = None


def run(dry=False):
    keys = Keys()
    chaser = None
    seen = lost = 0
    print(f"[fish] region={BAR_REGION} dry={dry}  Ctrl+C para salir")
    try:
        while True:
            t0 = time.perf_counter()
            ys, gs = detect(grab(BAR_REGION))
            if ys and gs:
                seen += 1
                lost = 0
                if seen >= CONFIRM_FRAMES:
                    if chaser is None:
                        print("[fish] minijuego")
                        chaser = Chaser(keys)
                    if dry:
                        print(f"amarillo={ys} verde={gs}")
                    else:
                        chaser.step(ys, gs, t0)
            else:
                seen = 0
                lost += 1
                if chaser and lost >= LOST_FRAMES:
                    print("[fish] fin")
                    keys.release()
                    chaser = None
            time.sleep(max(0.0, TICK - (time.perf_counter() - t0)))
    except KeyboardInterrupt:
        pass
    finally:
        keys.release()


def calib():
    pts = []
    for name in ("arriba-izquierda", "abajo-derecha"):
        input(f"Mouse en la esquina {name} de la barra y Enter...")
        pts.append(pyautogui.position())
    (x0, y0), (x1, y1) = pts
    print(f"BAR_REGION = ({x0}, {y0}, {x1 - x0}, {y1 - y0})")


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
        calib()
    elif mode == "watch":
        run(dry=True)
    elif mode == "debug":
        debug(sys.argv[2])
    else:
        run()
