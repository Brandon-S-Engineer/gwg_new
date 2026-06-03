"""Mouse/keyboard con movimiento suave + jitter, clicks como el bot viejo."""

import random
import sys
import time

import pyautogui

if sys.platform == "win32":
    import ctypes
    try:
        # Per-monitor v2: respeta escalado, no más coords lógicas vs físicas
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0  # nosotros manejamos los sleeps

# Tunables
MOVE_DURATION_MIN = 0.18
MOVE_DURATION_MAX = 0.32
POS_JITTER = 2          # ± pixeles sobre el destino
PRE_CLICK_MIN = 0.05
PRE_CLICK_MAX = 0.12
POST_CLICK_MIN = 0.05
POST_CLICK_MAX = 0.12


def _jitter(point: tuple[int, int]) -> tuple[int, int]:
    if POS_JITTER <= 0:
        return point
    return (point[0] + random.randint(-POS_JITTER, POS_JITTER),
            point[1] + random.randint(-POS_JITTER, POS_JITTER))


def _rand(lo: float, hi: float) -> float:
    return random.uniform(lo, hi)


def move_to(point: tuple[int, int]) -> None:
    target = _jitter(point)
    pyautogui.moveTo(target[0], target[1],
                     duration=_rand(MOVE_DURATION_MIN, MOVE_DURATION_MAX),
                     tween=pyautogui.easeInOutQuad)


def move_rel(dx: int, dy: int) -> None:
    pyautogui.move(dx + random.randint(-POS_JITTER, POS_JITTER),
                   dy + random.randint(-POS_JITTER, POS_JITTER),
                   duration=_rand(MOVE_DURATION_MIN, MOVE_DURATION_MAX),
                   tween=pyautogui.easeInOutQuad)


def click(point: tuple[int, int]) -> None:
    target = _jitter(point)
    move_to(target)
    time.sleep(_rand(PRE_CLICK_MIN, PRE_CLICK_MAX))
    pyautogui.click(target[0], target[1])
    time.sleep(_rand(POST_CLICK_MIN, POST_CLICK_MAX))


def click_here() -> None:
    time.sleep(_rand(PRE_CLICK_MIN, PRE_CLICK_MAX))
    pyautogui.click()
    time.sleep(_rand(POST_CLICK_MIN, POST_CLICK_MAX))


def right_click(point: tuple[int, int]) -> None:
    target = _jitter(point)
    move_to(target)
    time.sleep(_rand(PRE_CLICK_MIN, PRE_CLICK_MAX))
    pyautogui.rightClick(target[0], target[1])
    time.sleep(_rand(POST_CLICK_MIN, POST_CLICK_MAX))


def double_click(point: tuple[int, int]) -> None:
    target = _jitter(point)
    move_to(target)
    time.sleep(_rand(PRE_CLICK_MIN, PRE_CLICK_MAX))
    pyautogui.doubleClick(target[0], target[1])
    time.sleep(_rand(POST_CLICK_MIN, POST_CLICK_MAX))


def sleep(seconds: float, jitter: float = 0.15) -> None:
    """Sleep con jitter ± `jitter` × seconds."""
    delta = seconds * jitter
    time.sleep(_rand(seconds - delta, seconds + delta))
