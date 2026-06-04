"""Mouse: move suave con pyautogui, click con Win32 mouse_event (ctypes).

Algunas apps de Windows ignoran clicks "altos" de pyautogui. Bajamos
al nivel de Win32 user32.mouse_event con MOUSEEVENTF_ABSOLUTE, que es
lo más cerca al hardware sin drivers de kernel.
"""

import random
import sys
import time

import pyautogui

if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    _user32 = ctypes.windll.user32
else:
    _user32 = None

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# Tunables (ver docs/disimulo.md)
POS_JITTER = 3  # ±3px sobre el target; suficiente random sin fallar templates
# Duración del move escalada con distancia. Mano humana: cerca rápido, lejos lento.
MOVE_DUR_SHORT = 0.12   # distancia ~50px
MOVE_DUR_LONG = 0.60    # distancia ~1500px+
MOVE_DUR_JITTER = 0.10  # ±10% sobre la duración calculada
PRE_CLICK_MIN = 0.05
PRE_CLICK_MAX = 0.12
HOLD_MIN = 0.05
HOLD_MAX = 0.12
POST_CLICK_MIN = 0.05
POST_CLICK_MAX = 0.12

# Win32 mouse_event flags
_MOUSEEVENTF_MOVE = 0x0001
_MOUSEEVENTF_LEFTDOWN = 0x0002
_MOUSEEVENTF_LEFTUP = 0x0004
_MOUSEEVENTF_RIGHTDOWN = 0x0008
_MOUSEEVENTF_RIGHTUP = 0x0010
_MOUSEEVENTF_ABSOLUTE = 0x8000


def _jitter(point):
    if POS_JITTER <= 0:
        return point
    return (point[0] + random.randint(-POS_JITTER, POS_JITTER),
            point[1] + random.randint(-POS_JITTER, POS_JITTER))


def _rand(lo, hi):
    return random.uniform(lo, hi)


def _human_duration(target):
    """Duración del move según distancia desde la posición actual."""
    try:
        cur_x, cur_y = pyautogui.position()
    except Exception:
        cur_x, cur_y = target
    dx = target[0] - cur_x
    dy = target[1] - cur_y
    dist = (dx * dx + dy * dy) ** 0.5
    # interpolación lineal entre SHORT (50px) y LONG (1500px)
    t = max(0.0, min(1.0, (dist - 50) / 1450))
    base = MOVE_DUR_SHORT + (MOVE_DUR_LONG - MOVE_DUR_SHORT) * t
    delta = base * MOVE_DUR_JITTER
    return random.uniform(base - delta, base + delta)


def _abs_move(x, y):
    """Manda evento MOVE absoluto via mouse_event (bypasea pyautogui)."""
    if _user32 is None:
        pyautogui.moveTo(x, y)
        return
    sw = _user32.GetSystemMetrics(0)
    sh = _user32.GetSystemMetrics(1)
    nx = int(x * 65535 / max(sw - 1, 1))
    ny = int(y * 65535 / max(sh - 1, 1))
    _user32.mouse_event(_MOUSEEVENTF_MOVE | _MOUSEEVENTF_ABSOLUTE, nx, ny, 0, 0)


def _abs_press(button="left"):
    if _user32 is None:
        if button == "left":
            pyautogui.click()
        else:
            pyautogui.rightClick()
        return
    down = _MOUSEEVENTF_LEFTDOWN if button == "left" else _MOUSEEVENTF_RIGHTDOWN
    up = _MOUSEEVENTF_LEFTUP if button == "left" else _MOUSEEVENTF_RIGHTUP
    _user32.mouse_event(down, 0, 0, 0, 0)
    time.sleep(_rand(HOLD_MIN, HOLD_MAX))
    _user32.mouse_event(up, 0, 0, 0, 0)


def move_to(point):
    target = _jitter(point)
    pyautogui.moveTo(target[0], target[1],
                     duration=_human_duration(target),
                     tween=pyautogui.easeInOutQuad)
    # Reafirmamos posición con mouse_event absoluto (por si pyautogui
    # dejó el cursor en logical-coord con DPI scaling)
    _abs_move(target[0], target[1])


def move_rel(dx, dy):
    """Calcula target absoluto = pos_actual + (dx, dy) y usa move_to.

    Evita pyautogui.move (relativo) que puede aplicar DPI scaling
    inconsistente con nuestro _abs_move (mouse_event ABSOLUTE).
    """
    cur = pyautogui.position()
    target = (cur[0] + dx, cur[1] + dy)
    move_to(target)


def click(point):
    move_to(point)
    time.sleep(_rand(PRE_CLICK_MIN, PRE_CLICK_MAX))
    _abs_press("left")
    time.sleep(_rand(POST_CLICK_MIN, POST_CLICK_MAX))


def click_here():
    time.sleep(_rand(PRE_CLICK_MIN, PRE_CLICK_MAX))
    _abs_press("left")
    time.sleep(_rand(POST_CLICK_MIN, POST_CLICK_MAX))


def right_click(point):
    move_to(point)
    time.sleep(_rand(PRE_CLICK_MIN, PRE_CLICK_MAX))
    _abs_press("right")
    time.sleep(_rand(POST_CLICK_MIN, POST_CLICK_MAX))


def double_click(point):
    move_to(point)
    time.sleep(_rand(PRE_CLICK_MIN, PRE_CLICK_MAX))
    _abs_press("left")
    time.sleep(_rand(0.04, 0.09))
    _abs_press("left")
    time.sleep(_rand(POST_CLICK_MIN, POST_CLICK_MAX))


def sleep(seconds, jitter=0.15):
    delta = seconds * jitter
    time.sleep(_rand(seconds - delta, seconds + delta))
