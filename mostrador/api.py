"""API REST en JSON. La usa la pantalla de caja y puede usarla cualquier otro cliente."""

from flask import Blueprint, jsonify, request, url_for

from .db import get_db
from .servicio_ventas import ErrorVenta, registrar_venta
from .utils import a_centavos

bp = Blueprint("api", __name__, url_prefix="/api")


def _producto_a_dict(fila):
    return {
        "id": fila["id"],
        "codigo": fila["codigo"],
        "nombre": fila["nombre"],
        "precio_centavos": fila["precio_centavos"],
        "stock": fila["stock"],
    }


@bp.get("/productos")
def buscar_productos():
    """GET /api/productos?q=martillo  ->  lista de productos activos que coinciden."""
    q = request.args.get("q", "").strip()
    db = get_db()
    if q:
        filas = db.execute(
            "SELECT * FROM productos WHERE activo = 1 AND (codigo = ? OR nombre LIKE ?)"
            " ORDER BY codigo = ? DESC, nombre LIMIT 25",
            (q, f"%{q}%", q),
        ).fetchall()
    else:
        filas = db.execute(
            "SELECT * FROM productos WHERE activo = 1 ORDER BY nombre LIMIT 25"
        ).fetchall()
    return jsonify([_producto_a_dict(f) for f in filas])


@bp.post("/ventas")
def crear_venta():
    """POST /api/ventas

    Cuerpo JSON:
        {"items": [{"producto_id": 1, "cantidad": 2}],
         "metodo_pago": "efectivo",
         "recibido": "500"}
    """
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "Envía los datos de la venta en formato JSON."}), 400

    recibido = None
    if datos.get("metodo_pago") == "efectivo":
        try:
            recibido = a_centavos(datos.get("recibido", ""))
        except ValueError as e:
            return jsonify({"error": f"Efectivo recibido: {e}"}), 400

    db = get_db()
    try:
        venta_id = registrar_venta(db, datos.get("items"), datos.get("metodo_pago"), recibido)
    except ErrorVenta as e:
        return jsonify({"error": str(e)}), 400

    venta = db.execute("SELECT * FROM ventas WHERE id = ?", (venta_id,)).fetchone()
    return jsonify({
        "venta_id": venta_id,
        "total_centavos": venta["total_centavos"],
        "cambio_centavos": venta["cambio_centavos"],
        "ticket_url": url_for("ventas.ticket", venta_id=venta_id),
    }), 201
