"""Flujos compuestos: sell, salvage, consume."""

from .assets import Template


def sell_via_tp(item: Template, price_modifier: int = 0) -> bool:
    """Vende item en TP. price_modifier en copper (-1 = undercut)."""
    raise NotImplementedError("Pendiente fase 6")


def salvage_with_kit(kit: Template, target_quality: Template) -> bool:
    raise NotImplementedError("Pendiente fase 6")


def consume_stack(item: Template, consume_option: Template) -> bool:
    raise NotImplementedError("Pendiente fase 6")
