"""Regiones nombradas de la pantalla."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    w: int
    h: int

    def contains(self, point: tuple[int, int]) -> bool:
        px, py = point
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def as_pyautogui_region(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.w, self.h)


# Placeholders — se calibran en fase 3
INVENTORY_AREA = Region(0, 0, 0, 0)
BANK_AREA = Region(0, 0, 0, 0)
TP_SELL_PANEL = Region(0, 0, 0, 0)
TP_BUY_PANEL = Region(0, 0, 0, 0)
KIT_SLOT_AREA = Region(0, 0, 0, 0)
CONFIRM_DIALOG_AREA = Region(0, 0, 0, 0)
ERROR_DIALOG_AREA = Region(0, 0, 0, 0)
CONTEXT_MENU_OFFSET = Region(0, 0, 0, 0)


def slot_grid(area: Region, rows: int, cols: int) -> list[tuple[int, int]]:
    """Centros de los slots de una grilla uniforme, en orden fila-mayor."""
    raise NotImplementedError("Pendiente fase 3")
