"""Funciones de apoyo para convertir y mostrar cantidades de dinero."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


def a_centavos(texto):
    """Convierte un texto como "1,250.50" o "$89" a centavos (125050, 8900).

    Lanza ValueError con un mensaje claro si el texto no es un monto válido.
    """
    limpio = str(texto).replace("$", "").replace(",", "").strip()
    if not limpio:
        raise ValueError("Escribe un monto, por ejemplo 125.50.")
    try:
        valor = Decimal(limpio)
    except InvalidOperation:
        raise ValueError(f"\"{texto}\" no es un monto válido. Usa un formato como 125.50.")
    if valor < 0:
        raise ValueError("El monto no puede ser negativo.")
    return int((valor * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def formato_dinero(centavos):
    """Convierte centavos a texto con formato de pesos: 125050 -> "$1,250.50"."""
    return f"${(centavos or 0) / 100:,.2f}"
