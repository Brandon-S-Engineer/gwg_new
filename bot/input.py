"""Mouse/keyboard con movimiento suave y randomizado.

Move suave usa pyautogui (con `duration` y easing). Click usa pynput
porque en Windows/VM resulta más confiable que pyautogui para emitir
eventos. Se añade pequeña jitter a la posición y a los sleeps para
parecer humano.
"""

import random
import time

import pyautogui
from pynput.mouse import Button, Controller

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0  # gestionamos nuestras propias pausas

_mouse = Controller()

# Tunables
MOVE_DURATION_MIN = 0.18
MOVE_DURATION_MAX = 0.32
POS_JITTER = 2          # ± pixeles sobre el destino
PRE_CLICK_MIN = 0.06    # sleep antes de press
PRE_CLICK_MAX = 0.14
HOLD_MIN = 0.05         # tiempo entre press y release
HOLD_MAX = 0.11
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


def _press(button: Button) -> None:
    time.sleep(_rand(PRE_CLICK_MIN, PRE_CLICK_MAX))
    _mouse.press(button)
    time.sleep(_rand(HOLD_MIN, HOLD_MAX))
    _mouse.release(button)
    time.sleep(_rand(POST_CLICK_MIN, POST_CLICK_MAX))


def click(point: tuple[int, int]) -> None:
    move_to(point)
    _press(Button.left)


def click_here() -> None:
    _press(Button.left)


def right_click(point: tuple[int, int]) -> None:
    move_to(point)
    _press(Button.right)


def double_click(point: tuple[int, int]) -> None:
    move_to(point)
    _press(Button.left)
    time.sleep(_rand(0.05, 0.1))
    _press(Button.left)


def sleep(seconds: float, jitter: float = 0.15) -> None:
    """Sleep con jitter ± `jitter` × seconds."""
    delta = seconds * jitter
    time.sleep(_rand(seconds - delta, seconds + delta))
