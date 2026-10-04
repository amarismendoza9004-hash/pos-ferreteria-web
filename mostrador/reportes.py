"""Reportes: corte de caja del día, ventas recientes, más vendidos y stock bajo."""

from flask import Blueprint, render_template

from .db import get_db

bp = Blueprint("reportes", __name__, url_prefix="/reportes")


@bp.get("/")
def resumen():
    db = get_db()

    hoy = db.execute(
        "SELECT COUNT(*) AS tickets, COALESCE(SUM(total_centavos), 0) AS total"
        " FROM ventas WHERE date(fecha) = date('now', 'localtime')"
    ).fetchone()

    corte = db.execute(
        "SELECT metodo_pago, COUNT(*) AS tickets, SUM(total_centavos) AS total"
        " FROM ventas WHERE date(fecha) = date('now', 'localtime')"
        " GROUP BY metodo_pago ORDER BY total DESC"
    ).fetchall()

    ultimos_dias = db.execute(
        "SELECT date(fecha) AS dia, COUNT(*) AS tickets, SUM(total_centavos) AS total"
        " FROM ventas WHERE date(fecha) >= date('now', 'localtime', '-6 days')"
        " GROUP BY dia ORDER BY dia DESC"
    ).fetchall()

    mas_vendidos = db.execute(
        "SELECT p.nombre, SUM(d.cantidad) AS piezas, SUM(d.subtotal_centavos) AS total"
        " FROM venta_detalle d"
        " JOIN ventas v ON v.id = d.venta_id"
        " JOIN productos p ON p.id = d.producto_id"
        " WHERE date(v.fecha) >= date('now', 'localtime', '-29 days')"
        " GROUP BY p.id ORDER BY piezas DESC LIMIT 5"
    ).fetchall()

    stock_bajo = db.execute(
        "SELECT * FROM productos WHERE activo = 1 AND stock <= stock_minimo"
        " ORDER BY stock - stock_minimo, nombre"
    ).fetchall()

    return render_template(
        "reportes/resumen.html",
        hoy=hoy,
        corte=corte,
        ultimos_dias=ultimos_dias,
        mas_vendidos=mas_vendidos,
        stock_bajo=stock_bajo,
    )
