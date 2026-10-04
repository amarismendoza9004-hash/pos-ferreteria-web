"""Pantalla de caja, historial de ventas y ticket imprimible."""

from datetime import date

from flask import Blueprint, abort, render_template, request

from .db import get_db

bp = Blueprint("ventas", __name__)


@bp.get("/caja")
def caja():
    return render_template("ventas/caja.html")


@bp.get("/ventas")
def historial():
    dia = request.args.get("dia") or date.today().isoformat()
    db = get_db()
    ventas = db.execute(
        "SELECT v.*, (SELECT SUM(cantidad) FROM venta_detalle WHERE venta_id = v.id) AS piezas"
        " FROM ventas v WHERE date(v.fecha) = ? ORDER BY v.fecha DESC, v.id DESC",
        (dia,),
    ).fetchall()
    total_dia = sum(v["total_centavos"] for v in ventas)
    return render_template("ventas/historial.html", ventas=ventas, dia=dia, total_dia=total_dia)


@bp.get("/ventas/<int:venta_id>")
def ticket(venta_id):
    db = get_db()
    venta = db.execute("SELECT * FROM ventas WHERE id = ?", (venta_id,)).fetchone()
    if venta is None:
        abort(404)
    renglones = db.execute(
        "SELECT d.*, p.nombre, p.codigo FROM venta_detalle d"
        " JOIN productos p ON p.id = d.producto_id WHERE d.venta_id = ? ORDER BY d.id",
        (venta_id,),
    ).fetchall()
    return render_template("ventas/ticket.html", venta=venta, renglones=renglones)
