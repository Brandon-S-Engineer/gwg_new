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
    import ctypes.wintypes
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


def _cursor_pos():
    """Posición actual del cursor en píxeles físicos.

    Usa GetCursorPos directo en Win32 (no pyautogui.position), porque
    pyautogui puede devolver coords escaladas por DPI en algunas
    configuraciones de VMware.
    """
    if _user32 is None:
        return pyautogui.position()
    pt = ctypes.wintypes.POINT()
    _user32.GetCursorPos(ctypes.byref(pt))
    return (pt.x, pt.y)

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# Tunables (ver docs/disimulo.md)
POS_JITTER = 5  # ±5px sobre el target; suficiente random sin fallar templates
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
# Tipeo humano: delay aleatorio entre teclas.
TYPE_MIN = 0.09
TYPE_MAX = 0.22

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
    cur_x, cur_y = _cursor_pos()
    dx = target[0] - cur_x
    dy = target[1] - cur_y
    dist = (dx * dx + dy * dy) ** 0.5
    # interpolación lineal entre SHORT (50px) y LONG (1500px)
    t = max(0.0, min(1.0, (dist - 50) / 1450))
    base = MOVE_DUR_SHORT + (MOVE_DUR_LONG - MOVE_DUR_SHORT) * t
    delta = base * MOVE_DUR_JITTER
    return random.uniform(base - delta, base + delta)


EASE_POWER_MIN = 1.6  # curva más pareja (casi lineal)
EASE_POWER_MAX = 2.6  # curva más marcada (acelera/frena más fuerte)


def _ease_in_out(t, power):
    """Arranque y final suaves, pico de velocidad al medio (no lineal).
    `power` variable por movimiento (ver move_to): no siempre la misma
    curva de aceleración/desaceleración, más orgánico."""
    return 0.5 * (2 * t) ** power if t < 0.5 else 1 - 0.5 * (2 * (1 - t)) ** power


STEP_DT = 0.012  # ~12ms por paso del move


DEBUG_ABS_MOVE = False  # Activa los prints internos para diagnosticar DPI


def _abs_move(x, y):
    """Manda evento MOVE absoluto via mouse_event (bypasea pyautogui)."""
    if _user32 is None:
        pyautogui.moveTo(x, y)
        return
    sw = _user32.GetSystemMetrics(0)
    sh = _user32.GetSystemMetrics(1)
    nx = int(x * 65535 / max(sw - 1, 1))
    ny = int(y * 65535 / max(sh - 1, 1))
    if DEBUG_ABS_MOVE:
        before = _cursor_pos()
        _user32.mouse_event(_MOUSEEVENTF_MOVE | _MOUSEEVENTF_ABSOLUTE, nx, ny, 0, 0)
        after = _cursor_pos()
        print(f"[abs_move] target=({x},{y}) sw,sh=({sw},{sh}) "
              f"norm=({nx},{ny}) before={before} after={after}")
    else:
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
    """Move suave hasta el target, TODO en coords físicas vía _abs_move.

    No usamos pyautogui.moveTo: en el VM con escalado DPI aterriza en la
    posición equivocada y obligaba a un _abs_move final que se veía como
    teletransporte. Interpolando con _abs_move el camino es suave y exacto.
    """
    target = _jitter(point)
    start = _cursor_pos()
    dx = target[0] - start[0]
    dy = target[1] - start[1]
    dist = (dx * dx + dy * dy) ** 0.5
    if dist < 2:
        _abs_move(target[0], target[1])
        return
    dur = _human_duration(target)
    steps = max(2, int(dur / STEP_DT))
    power = _rand(EASE_POWER_MIN, EASE_POWER_MAX)
    for s in range(1, steps + 1):
        e = _ease_in_out(s / steps, power)
        _abs_move(int(round(start[0] + dx * e)),
                  int(round(start[1] + dy * e)))
        time.sleep(dur / steps)
    _abs_move(target[0], target[1])  # asegurar el píxel exacto


def move_rel(dx, dy):
    """Calcula target absoluto = pos_actual + (dx, dy) y usa move_to.

    Lee posición con GetCursorPos (Win32) para evitar el escalado DPI
    que puede meter pyautogui.position() en VMware.
    """
    cur = _cursor_pos()
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


def drag(start, end, hold_before: float = 0.5):
    """Drag de start a end (para mover ventanas). Mantiene botón durante el move."""
    move_to(start)
    time.sleep(_rand(PRE_CLICK_MIN, PRE_CLICK_MAX))
    if _user32:
        _user32.mouse_event(_MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    else:
        pyautogui.mouseDown()
    time.sleep(hold_before)
    move_to(end)
    time.sleep(_rand(HOLD_MIN, HOLD_MAX))
    if _user32:
        _user32.mouse_event(_MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    else:
        pyautogui.mouseUp()


# Backspaces de sobra para limpiar un campo de búsqueda (nunca escriben más
# de ~20 chars). Cubre el caso en que ctrl+a/delete no seleccionó nada
# (foco tardío, hotkey interceptado por el juego) y quedaba texto viejo
# pegado, rompiendo la búsqueda siguiente.
CLEAR_FIELD_BACKSPACES = 30


def clear_field():
    """Deja un campo de texto vacío sin depender de que ctrl+a/delete
    hayan funcionado: ctrl+a intenta seleccionar todo, y de todos modos
    se manda backspace de sobra para borrar cualquier resto.

    Los backspaces van con un pequeño delay entre cada uno: mandados todos
    de golpe (sin sleep) se pierden bajo Parsec, y a veces se comían la
    escritura siguiente (quedaba el campo sin nada tecleado).
    """
    import keyboard as _kb
    _kb.send("ctrl+a")
    time.sleep(0.05)
    for _ in range(CLEAR_FIELD_BACKSPACES):
        _kb.send("backspace")
        time.sleep(_rand(0.02, 0.04))
    time.sleep(0.05)


def type_text(text):
    """Teclea letra por letra con delay aleatorio entre teclas (humano)."""
    import keyboard as _kb
    for ch in text:
        _kb.write(ch)
        time.sleep(_rand(TYPE_MIN, TYPE_MAX))


def sleep(seconds, jitter=0.15):
    delta = seconds * jitter
    time.sleep(_rand(seconds - delta, seconds + delta))
