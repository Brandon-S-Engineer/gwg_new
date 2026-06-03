"""Clicks y movimiento de mouse.

En Windows + VM los clicks rápidos a veces se pierden. Movemos con
`MOVE_DURATION` y dormimos antes/después de cada press.
"""

import time

import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1  # pausa entre cada llamada de pyautogui

MOVE_DURATION = 0.2
CLICK_HOLD = 0.08


def move_to(point: tuple[int, int]) -> None:
    pyautogui.moveTo(point[0], point[1], duration=MOVE_DURATION)


def move_rel(dx: int, dy: int) -> None:
    pyautogui.move(dx, dy, duration=MOVE_DURATION)


def click(point: tuple[int, int]) -> None:
    pyautogui.moveTo(point[0], point[1], duration=MOVE_DURATION)
    time.sleep(0.1)
    pyautogui.mouseDown()
    time.sleep(CLICK_HOLD)
    pyautogui.mouseUp()


def click_here() -> None:
    time.sleep(0.05)
    pyautogui.mouseDown()
    time.sleep(CLICK_HOLD)
    pyautogui.mouseUp()


def right_click(point: tuple[int, int]) -> None:
    pyautogui.moveTo(point[0], point[1], duration=MOVE_DURATION)
    time.sleep(0.1)
    pyautogui.mouseDown(button='right')
    time.sleep(CLICK_HOLD)
    pyautogui.mouseUp(button='right')


def double_click(point: tuple[int, int]) -> None:
    pyautogui.moveTo(point[0], point[1], duration=MOVE_DURATION)
    time.sleep(0.1)
    pyautogui.mouseDown()
    time.sleep(CLICK_HOLD)
    pyautogui.mouseUp()
    time.sleep(0.08)
    pyautogui.mouseDown()
    time.sleep(CLICK_HOLD)
    pyautogui.mouseUp()


def sleep(seconds: float) -> None:
    time.sleep(seconds)
