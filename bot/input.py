"""
Capa de input: clicks, teclado, scroll, drag.

Envuelve pyautogui/keyboard para que el resto del bot no los importe
directamente. La clave es que estas primitivas son "inteligentes": no
adivinan offsets, buscan los targets por imagen donde aplica.
"""

from pathlib import Path

from .regions import Region


# --- Mouse básico -----------------------------------------------------------
def click(point: tuple[int, int]) -> None:
    raise NotImplementedError("Pendiente fase 5")


def right_click(point: tuple[int, int]) -> None:
    raise NotImplementedError("Pendiente fase 5")


def double_click(point: tuple[int, int]) -> None:
    raise NotImplementedError("Pendiente fase 5")


def move_to(point: tuple[int, int]) -> None:
    raise NotImplementedError("Pendiente fase 5")


# --- Acciones compuestas (lo importante) ------------------------------------
def right_click_menu_option(target: tuple[int, int],
                            option_template: Path) -> bool:
    """
    Click derecho en target → busca option_template en el menú contextual
    que aparece → click en él.

    Reemplaza el patrón v2 `pyautogui.move(16, 88); pyautogui.click()` que
    adivinaba pixel-offsets de la opción "Sell" / "Salvage" / etc.
    """
    raise NotImplementedError("Pendiente fase 5")


def confirm_dialog(button_template: Path | None = None) -> bool:
    """
    Busca un botón de confirmación dentro de CONFIRM_DIALOG_AREA y le da
    click. Reemplaza los 6 confirm_button_N hardcoded de v2.
    """
    raise NotImplementedError("Pendiente fase 5")


def scroll(point: tuple[int, int], ticks: int, direction: str = "down") -> None:
    """
    Scroll N ticks en una dirección, sobre un punto.
    Reemplaza los 32 pyautogui.scroll(-500) seguidos de v2.
    """
    raise NotImplementedError("Pendiente fase 5")


def drag(start: tuple[int, int], end: tuple[int, int], duration: float = 1.0) -> None:
    raise NotImplementedError("Pendiente fase 5")


# --- Teclado ----------------------------------------------------------------
def press(key: str) -> None:
    raise NotImplementedError("Pendiente fase 5")


def press_and_hold(key: str, hold_time: float = 0.1) -> None:
    raise NotImplementedError("Pendiente fase 5")


def type_text(text: str, interval: float = 0.05) -> None:
    raise NotImplementedError("Pendiente fase 5")
