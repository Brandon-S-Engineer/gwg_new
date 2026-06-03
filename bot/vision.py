"""Captura de pantalla y template matching."""

from pathlib import Path

from .regions import Region


def capture_screen(region: Region | None = None):
    """Devuelve la pantalla (o región) en escala de grises."""
    raise NotImplementedError("Pendiente fase 2")


def find(template_path: Path, region: Region | None = None,
         threshold: float | None = None) -> tuple[int, int] | None:
    """Centro del primer match, o None."""
    raise NotImplementedError("Pendiente fase 2")


def find_all(template_path: Path, region: Region | None = None,
             threshold: float | None = None) -> list[tuple[int, int]]:
    raise NotImplementedError("Pendiente fase 2")


def wait_for(template_path: Path, region: Region | None = None,
             timeout: float | None = None,
             threshold: float | None = None) -> tuple[int, int] | None:
    """Poll hasta encontrar el template o agotar timeout."""
    raise NotImplementedError("Pendiente fase 2")


def is_present(template_path: Path, region: Region | None = None,
               threshold: float | None = None) -> bool:
    raise NotImplementedError("Pendiente fase 2")
