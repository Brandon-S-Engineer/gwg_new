"""Errores tipados y recovery."""


class BotError(Exception):
    pass


class GameCrashedError(BotError):
    pass


class LoggedOutError(BotError):
    pass


class GameClosedError(BotError):
    pass


class NavigationError(BotError):
    pass


def recover_from(error: BotError) -> None:
    raise NotImplementedError("Pendiente fase 9")
