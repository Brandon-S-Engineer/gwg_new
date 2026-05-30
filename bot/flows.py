"""
Flujos compuestos: las operaciones que se repiten 15+ veces en v2.

Una vez que existan estos 3-4 helpers, las rutinas se vuelven triviales:
una venta entera cabe en una línea.
"""

from .assets import Template


def sell_via_tp(item: Template, price_modifier: int = 0) -> bool:
    """
    Flujo completo de venta en Trading Post:
      1. Busca el item en INVENTORY_AREA
      2. Click derecho → opción "Sell" del menú contextual
      3. Espera al panel del TP
      4. Click en "agregar a lista" → "cantidad máxima" → ajusta precio
      5. Click en "listar" → espera confirmación de éxito

    price_modifier: copper a sumar/restar al precio sugerido (-1 = undercut).
    Devuelve True si se listó, False si no se encontró el item.
    """
    raise NotImplementedError("Pendiente fase 6")


def salvage_with_kit(kit: Template, target_quality: Template) -> bool:
    """
    Flujo de salvage:
      1. Busca el kit (runecrafter/silver/copper-fed) en KIT_SLOT_AREA
      2. Click derecho → opción "Salvage <calidad>" del menú
      3. Confirma el diálogo si aparece
      4. Espera a que termine la animación

    Devuelve True si se ejecutó, False si no había kit o no había items.
    """
    raise NotImplementedError("Pendiente fase 6")


def consume_stack(item: Template, consume_option: Template) -> bool:
    """
    Flujo para consumir un stack (luck, etc.):
      1. Busca el item en INVENTORY_AREA
      2. Click derecho → opción "Consume All" del menú
      3. Confirma si hay diálogo
    """
    raise NotImplementedError("Pendiente fase 6")
