"""Captura + template matching con OpenCV."""

import time
from pathlib import Path

import cv2
import numpy as np
import pyautogui

from .config import DEFAULT_MATCH_THRESHOLD, DEFAULT_WAIT_TIMEOUT, POLL_INTERVAL
from .regions import Region


def capture_screen(region: Region | None = None) -> np.ndarray:
    """Screenshot en gris (np.uint8). region=None = pantalla completa."""
    if region:
        shot = pyautogui.screenshot(region=region.as_pyautogui_region())
    else:
        shot = pyautogui.screenshot()
    return cv2.cvtColor(np.array(shot), cv2.COLOR_BGR2GRAY)


def find(template_path: Path, region: Region | None = None,
         threshold: float | None = None) -> tuple[int, int] | None:
    """Devuelve centro absoluto del primer match (>= threshold), o None."""
    th = threshold if threshold is not None else DEFAULT_MATCH_THRESHOLD
    screen = capture_screen(region)
    tpl = cv2.imread(str(template_path), 0)
    if tpl is None:
        raise FileNotFoundError(template_path)
    res = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val < th:
        print(f"[vision] {template_path.name}: max_val={max_val:.3f} < th={th:.2f}")
        return None
    print(f"[vision] {template_path.name}: max_val={max_val:.3f} ok")
    h, w = tpl.shape[:2]
    ox = region.x if region else 0
    oy = region.y if region else 0
    return (ox + max_loc[0] + w // 2, oy + max_loc[1] + h // 2)


def is_present(template_path: Path, region: Region | None = None,
               threshold: float | None = None) -> bool:
    return find(template_path, region, threshold) is not None


def wait_for(template_path: Path, region: Region | None = None,
             timeout: float | None = None,
             threshold: float | None = None) -> tuple[int, int] | None:
    """Poll cada POLL_INTERVAL hasta timeout."""
    deadline = time.time() + (timeout if timeout is not None else DEFAULT_WAIT_TIMEOUT)
    while time.time() < deadline:
        pt = find(template_path, region, threshold)
        if pt:
            return pt
        time.sleep(POLL_INTERVAL)
    return None
