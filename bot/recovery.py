"""
Modelo de errores y recovery.

En v2 handle_errors duplica el mismo bloque de recovery 4 veces. Aquí lo
modelamos como excepciones tipadas que el loop principal captura una vez.
Las rutinas no manejan errores — solo los dejan subir.
"""


class BotError(Exception):
    """Base de todos los errores recuperables del bot."""


class GameCrashedError(BotError):
    """Diálogo de error fatal o pantalla negra detectada."""


class LoggedOutError(BotError):
    """Volvimos a la pantalla de selección de personaje."""


class GameClosedError(BotError):
    """El cliente se cerró por completo (desktop visible)."""


class NavigationError(BotError):
    """El bot perdió la posición/orientación frente al NPC."""


def recover_from(error: BotError) -> None:
    """
    Punto único de recuperación. Mapea el tipo de error a la secuencia
    de pasos para volver al estado de farmeo:
      - GameCrashedError → cerrar diálogo → reset_position → open_menus
      - LoggedOutError   → re-login → seleccionar personaje → ...
      - GameClosedError  → abrir cliente → login → seleccionar → ...
      - NavigationError  → walk_and_center_npc → open_menus
    """
    raise NotImplementedError("Pendiente fase 9")
