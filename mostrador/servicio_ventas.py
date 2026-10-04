"""Reglas de negocio para registrar una venta.

Esta lógica vive separada de las rutas web para poder probarla de forma
independiente y reutilizarla (desde la caja, la API o un script).
"""

METODOS_PAGO = ("efectivo", "tarjeta", "transferencia")


class ErrorVenta(Exception):
    """Error que se le puede mostrar directamente al cajero."""


def _agrupar_items(items):
    """Valida los renglones del ticket y suma cantidades del mismo producto."""
    if not items:
        raise ErrorVenta("El ticket está vacío. Agrega al menos un producto.")

    cantidades = {}
    for item in items:
        try:
            producto_id = int(item["producto_id"])
            cantidad = int(item["cantidad"])
        except (KeyError, TypeError, ValueError):
            raise ErrorVenta("Hay un renglón del ticket con datos incompletos.")
        if cantidad <= 0:
            raise ErrorVenta("Las cantidades deben ser mayores a cero.")
        cantidades[producto_id] = cantidades.get(producto_id, 0) + cantidad
    return cantidades


def registrar_venta(db, items, metodo_pago, recibido_centavos=None):
    """Registra una venta completa y descuenta el inventario.

    items: lista de diccionarios {"producto_id": 3, "cantidad": 2}
    Devuelve el id de la venta creada.

    Todo ocurre dentro de una transacción: si algo falla (por ejemplo, no
    alcanza el stock), no se guarda nada y el inventario queda intacto.
    """
    if metodo_pago not in METODOS_PAGO:
        raise ErrorVenta("Elige un método de pago: efectivo, tarjeta o transferencia.")

    cantidades = _agrupar_items(items)

    try:
        db.execute("BEGIN IMMEDIATE")  # bloquea escrituras de otras cajas mientras cobramos

        renglones = []
        total = 0
        for producto_id, cantidad in cantidades.items():
            producto = db.execute(
                "SELECT id, nombre, precio_centavos, stock FROM productos"
                " WHERE id = ? AND activo = 1",
                (producto_id,),
            ).fetchone()
            if producto is None:
                raise ErrorVenta("Uno de los productos ya no existe o fue dado de baja.")
            if producto["stock"] < cantidad:
                raise ErrorVenta(
                    f"No hay suficiente \"{producto['nombre']}\": "
                    f"quedan {producto['stock']} y el ticket pide {cantidad}."
                )
            subtotal = producto["precio_centavos"] * cantidad
            renglones.append((producto_id, cantidad, producto["precio_centavos"], subtotal))
            total += subtotal

        if metodo_pago == "efectivo":
            if recibido_centavos is None or recibido_centavos < total:
                raise ErrorVenta("El efectivo recibido no cubre el total de la venta.")
            cambio = recibido_centavos - total
        else:
            recibido_centavos = total
            cambio = 0

        cursor = db.execute(
            "INSERT INTO ventas (total_centavos, metodo_pago, recibido_centavos, cambio_centavos)"
            " VALUES (?, ?, ?, ?)",
            (total, metodo_pago, recibido_centavos, cambio),
        )
        venta_id = cursor.lastrowid

        for producto_id, cantidad, precio, subtotal in renglones:
            db.execute(
                "INSERT INTO venta_detalle"
                " (venta_id, producto_id, cantidad, precio_unitario_centavos, subtotal_centavos)"
                " VALUES (?, ?, ?, ?, ?)",
                (venta_id, producto_id, cantidad, precio, subtotal),
            )
            db.execute(
                "UPDATE productos SET stock = stock - ? WHERE id = ?",
                (cantidad, producto_id),
            )

        db.commit()
        return venta_id
    except Exception:
        db.rollback()
        raise
