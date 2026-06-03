"""Clicks y movimiento de mouse."""

import time

import pyautogui

pyautogui.FAILSAFE = False


def move_to(point: tuple[int, int]) -> None:
    pyautogui.moveTo(point[0], point[1])


def move_rel(dx: int, dy: int) -> None:
    pyautogui.move(dx, dy)


def click(point: tuple[int, int]) -> None:
    pyautogui.click(point[0], point[1])


def click_here() -> None:
    pyautogui.click()


def right_click(point: tuple[int, int]) -> None:
    pyautogui.rightClick(point[0], point[1])


def double_click(point: tuple[int, int]) -> None:
    pyautogui.doubleClick(point[0], point[1])


def sleep(seconds: float) -> None:
    time.sleep(seconds)
