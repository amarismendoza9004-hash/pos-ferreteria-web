"""Alta, edición, baja y consulta de productos e inventario."""

import json
import os
import sqlite3

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for

from . import importador
from .db import get_db
from .utils import a_centavos

bp = Blueprint("productos", __name__, url_prefix="/productos")


def _leer_formulario(form):
    """Valida el formulario. Devuelve (datos, errores)."""
    errores = []
    datos = {
        "codigo": form.get("codigo", "").strip(),
        "nombre": form.get("nombre", "").strip(),
    }
    if not datos["codigo"]:
        errores.append("Escribe el código del producto.")
    if not datos["nombre"]:
        errores.append("Escribe el nombre del producto.")

    try:
        datos["precio_centavos"] = a_centavos(form.get("precio", ""))
    except ValueError as e:
        errores.append(f"Precio: {e}")

    for campo, etiqueta in (("stock", "Existencias"), ("stock_minimo", "Stock mínimo")):
        try:
            valor = int(form.get(campo, "0") or 0)
            if valor < 0:
                raise ValueError
            datos[campo] = valor
        except ValueError:
            errores.append(f"{etiqueta}: usa un número entero de 0 en adelante.")

    return datos, errores


def _obtener_producto(producto_id):
    producto = get_db().execute(
        "SELECT * FROM productos WHERE id = ? AND activo = 1", (producto_id,)
    ).fetchone()
    if producto is None:
        abort(404)
    return producto


@bp.get("/")
def lista():
    q = request.args.get("q", "").strip()
    solo_bajo = request.args.get("filtro") == "bajo"

    sql = "SELECT * FROM productos WHERE activo = 1"
    params = []
    if q:
        sql += " AND (codigo LIKE ? OR nombre LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if solo_bajo:
        sql += " AND stock <= stock_minimo"
    sql += " ORDER BY nombre"

    productos = get_db().execute(sql, params).fetchall()
    return render_template("productos/lista.html", productos=productos, q=q, solo_bajo=solo_bajo)


@bp.route("/nuevo", methods=("GET", "POST"))
def nuevo():
    if request.method == "POST":
        datos, errores = _leer_formulario(request.form)
        if not errores:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO productos (codigo, nombre, precio_centavos, stock, stock_minimo)"
                    " VALUES (:codigo, :nombre, :precio_centavos, :stock, :stock_minimo)",
                    datos,
                )
                db.commit()
            except sqlite3.IntegrityError:
                errores.append(f"Ya existe un producto con el código {datos['codigo']}.")
            else:
                flash(f"Producto \"{datos['nombre']}\" agregado.", "ok")
                return redirect(url_for("productos.lista"))
        for e in errores:
            flash(e, "error")
    return render_template("productos/formulario.html", producto=None, form=request.form)


@bp.route("/<int:producto_id>/editar", methods=("GET", "POST"))
def editar(producto_id):
    producto = _obtener_producto(producto_id)
    if request.method == "POST":
        datos, errores = _leer_formulario(request.form)
        if not errores:
            datos["id"] = producto_id
            db = get_db()
            try:
                db.execute(
                    "UPDATE productos SET codigo = :codigo, nombre = :nombre,"
                    " precio_centavos = :precio_centavos, stock = :stock,"
                    " stock_minimo = :stock_minimo WHERE id = :id",
                    datos,
                )
                db.commit()
            except sqlite3.IntegrityError:
                errores.append(f"Ya existe otro producto con el código {datos['codigo']}.")
            else:
                flash(f"Cambios guardados en \"{datos['nombre']}\".", "ok")
                return redirect(url_for("productos.lista"))
        for e in errores:
            flash(e, "error")
        return render_template("productos/formulario.html", producto=producto, form=request.form)
    return render_template("productos/formulario.html", producto=producto, form=None)


@bp.post("/<int:producto_id>/baja")
def baja(producto_id):
    """Da de baja sin borrar, para no perder el historial de ventas."""
    producto = _obtener_producto(producto_id)
    db = get_db()
    db.execute("UPDATE productos SET activo = 0 WHERE id = ?", (producto_id,))
    db.commit()
    flash(f"\"{producto['nombre']}\" se dio de baja. Sus ventas anteriores se conservan.", "ok")
    return redirect(url_for("productos.lista"))


# ---------- Importar catálogo (Truper u otro proveedor) ----------

def _ruta_pendiente():
    return os.path.join(current_app.instance_path, "importacion_pendiente.json")


def _leer_pendiente():
    try:
        with open(_ruta_pendiente(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


@bp.route("/importar", methods=("GET", "POST"))
def importar():
    if request.method == "POST":
        archivo = request.files.get("archivo")
        if not archivo or not archivo.filename:
            flash("Elige el archivo del catálogo.", "error")
            return render_template("productos/importar.html")
        try:
            filas = importador.leer_archivo(archivo.filename, archivo.read())
        except importador.ErrorImportacion as e:
            flash(str(e), "error")
            return render_template("productos/importar.html")
        with open(_ruta_pendiente(), "w", encoding="utf-8") as f:
            json.dump({"archivo": archivo.filename, "filas": filas}, f, ensure_ascii=False)
        return redirect(url_for("productos.revisar_importacion"))
    return render_template("productos/importar.html")


@bp.get("/importar/revisar")
def revisar_importacion():
    pendiente = _leer_pendiente()
    if pendiente is None:
        flash("Primero sube el archivo del catálogo.", "error")
        return redirect(url_for("productos.importar"))

    filas = pendiente["filas"]
    try:
        encabezado = int(request.args["encabezado"]) - 1
        encabezado = min(max(encabezado, 0), len(filas) - 1)
    except (KeyError, ValueError):
        encabezado = importador.detectar_encabezado(filas)

    encabezados = filas[encabezado]
    ancho = max(len(f) for f in filas[encabezado:encabezado + 50])
    encabezados = encabezados + [""] * (ancho - len(encabezados))
    columnas = importador.adivinar_columnas(encabezados)

    return render_template(
        "productos/importar_revisar.html",
        archivo=pendiente["archivo"],
        encabezado=encabezado,
        encabezados=encabezados,
        columnas=columnas,
        campos=importador.CAMPOS,
        obligatorios=importador.OBLIGATORIOS,
        muestra=[f for f in filas[encabezado + 1:encabezado + 30] if any(f)][:5],
        total=sum(1 for f in filas[encabezado + 1:] if any(f)),
    )


@bp.post("/importar/confirmar")
def confirmar_importacion():
    pendiente = _leer_pendiente()
    if pendiente is None:
        flash("Primero sube el archivo del catálogo.", "error")
        return redirect(url_for("productos.importar"))

    encabezado = int(request.form.get("encabezado", 0))
    columnas = {}
    for campo in importador.CAMPOS:
        valor = request.form.get(f"col_{campo}", "")
        columnas[campo] = int(valor) if valor.isdigit() else None

    try:
        aumento = float(request.form.get("aumento", "0").replace("%", "").strip() or 0)
    except ValueError:
        aumento = 0

    try:
        resumen = importador.aplicar_importacion(
            get_db(),
            pendiente["filas"][encabezado + 1:],
            columnas,
            si_existe=request.form.get("si_existe", "actualizar"),
            aumento_pct=aumento,
            fila_inicial=encabezado + 2,
        )
    except importador.ErrorImportacion as e:
        flash(str(e), "error")
        return redirect(url_for("productos.revisar_importacion", encabezado=encabezado + 1))

    os.remove(_ruta_pendiente())
    return render_template("productos/importar_resultado.html", resumen=resumen)
