"""
Capa de visión: capturar pantalla y encontrar cosas en ella.

Esta es la primitiva de la que depende todo lo demás. Si esto está bien,
el resto del bot es composición.
"""

from pathlib import Path

from .regions import Region


def capture_screen(region: Region | None = None):
    """
    Captura la pantalla (completa o una región) y devuelve un array
    en escala de grises listo para template matching.
    """
    raise NotImplementedError("Pendiente fase 2")


def find(template_path: Path, region: Region | None = None,
         threshold: float | None = None) -> tuple[int, int] | None:
    """
    Busca un template y devuelve el centro del primer match, o None.
    Si se pasa region, la búsqueda se restringe a esa zona — es la pieza
    clave del rediseño: en vez de adivinar coordenadas, buscamos íconos
    dentro de áreas conocidas.
    """
    raise NotImplementedError("Pendiente fase 2")


def find_all(template_path: Path, region: Region | None = None,
             threshold: float | None = None) -> list[tuple[int, int]]:
    """Como find pero devuelve todos los matches."""
    raise NotImplementedError("Pendiente fase 2")


def wait_for(template_path: Path, region: Region | None = None,
             timeout: float | None = None,
             threshold: float | None = None) -> tuple[int, int] | None:
    """
    Poll hasta que aparezca el template o se agote el timeout.
    Reemplaza los time.sleep(N) ciegos de v2 — esperamos al estado
    correcto en vez de adivinar cuánto tarda.
    """
    raise NotImplementedError("Pendiente fase 2")


def is_present(template_path: Path, region: Region | None = None,
               threshold: float | None = None) -> bool:
    """Atajo: True si find() encuentra algo. No espera."""
    raise NotImplementedError("Pendiente fase 2")
