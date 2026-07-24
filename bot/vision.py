"""Captura + template matching con OpenCV."""

import time
from pathlib import Path

import cv2
import numpy as np
import pyautogui

from .config import DEFAULT_MATCH_THRESHOLD, DEFAULT_WAIT_TIMEOUT, POLL_INTERVAL
from .regions import Region


def capture_screen(region: Region | None = None,
                   color: bool = False) -> np.ndarray:
    """Screenshot (np.uint8). region=None = pantalla completa.

    color=False → gris (default, lo que usa fase 1).
    color=True  → BGR, para distinguir items que solo cambian de color
                  (ej: las 4 tiers de esencia de suerte, mismo dibujo).
    """
    if region:
        shot = pyautogui.screenshot(region=region.as_pyautogui_region())
    else:
        shot = pyautogui.screenshot()
    arr = np.array(shot)  # RGB (PIL)
    if color:
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)  # alinear con cv2.imread
    return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)


def find(template_path: Path, region: Region | None = None,
         threshold: float | None = None,
         color: bool = False) -> tuple[int, int] | None:
    """Devuelve centro absoluto del primer match (>= threshold), o None."""
    th = threshold if threshold is not None else DEFAULT_MATCH_THRESHOLD
    screen = capture_screen(region, color=color)
    tpl = cv2.imread(str(template_path), cv2.IMREAD_COLOR if color else 0)
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
               threshold: float | None = None, color: bool = False) -> bool:
    return find(template_path, region, threshold, color) is not None


def is_calibrated(template_path: Path, min_size: int = 20) -> bool:
    """True si el archivo existe y NO es un placeholder chico (los que se
    dejan para coordenadas nuevas son 10x10; una captura real del picker
    siempre es más grande). Usar para no bloquear/disparar en falso con
    lógica nueva hasta que el usuario capture la imagen de verdad."""
    img = cv2.imread(str(template_path), 0)
    return img is not None and (img.shape[0] > min_size or img.shape[1] > min_size)


def wait_for(template_path: Path, region: Region | None = None,
             timeout: float | None = None,
             threshold: float | None = None,
             color: bool = False) -> tuple[int, int] | None:
    """Poll cada POLL_INTERVAL hasta timeout."""
    deadline = time.time() + (timeout if timeout is not None else DEFAULT_WAIT_TIMEOUT)
    while time.time() < deadline:
        pt = find(template_path, region, threshold, color)
        if pt:
            return pt
        time.sleep(POLL_INTERVAL)
    return None
