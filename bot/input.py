"""Clicks, teclado, scroll, drag."""

from pathlib import Path

from .regions import Region


def click(point: tuple[int, int]) -> None:
    raise NotImplementedError("Pendiente fase 5")


def right_click(point: tuple[int, int]) -> None:
    raise NotImplementedError("Pendiente fase 5")


def double_click(point: tuple[int, int]) -> None:
    raise NotImplementedError("Pendiente fase 5")


def move_to(point: tuple[int, int]) -> None:
    raise NotImplementedError("Pendiente fase 5")


def right_click_menu_option(target: tuple[int, int],
                            option_template: Path) -> bool:
    """Right-click en target, busca la opción en el menú y la clickea."""
    raise NotImplementedError("Pendiente fase 5")


def confirm_dialog(button_template: Path | None = None) -> bool:
    """Busca y clickea un botón dentro de CONFIRM_DIALOG_AREA."""
    raise NotImplementedError("Pendiente fase 5")


def scroll(point: tuple[int, int], ticks: int, direction: str = "down") -> None:
    raise NotImplementedError("Pendiente fase 5")


def drag(start: tuple[int, int], end: tuple[int, int], duration: float = 1.0) -> None:
    raise NotImplementedError("Pendiente fase 5")


def press(key: str) -> None:
    raise NotImplementedError("Pendiente fase 5")


def press_and_hold(key: str, hold_time: float = 0.1) -> None:
    raise NotImplementedError("Pendiente fase 5")


def type_text(text: str, interval: float = 0.05) -> None:
    raise NotImplementedError("Pendiente fase 5")
