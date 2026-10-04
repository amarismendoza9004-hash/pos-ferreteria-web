"""Mostrador: punto de venta web para ferretería, hecho con Flask y SQLite."""

import os

from flask import Flask, redirect, url_for

from .utils import formato_dinero


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion"),
        DATABASE=os.path.join(app.instance_path, "mostrador.sqlite"),
        NOMBRE_NEGOCIO=os.environ.get("NOMBRE_NEGOCIO", "Ferretería Mostrador"),
    )
    if config:
        app.config.update(config)

    os.makedirs(app.instance_path, exist_ok=True)

    from . import db
    db.init_app(app)

    from . import api, productos, reportes, ventas
    app.register_blueprint(ventas.bp)
    app.register_blueprint(productos.bp)
    app.register_blueprint(reportes.bp)
    app.register_blueprint(api.bp)

    app.add_template_filter(formato_dinero, "dinero")

    @app.context_processor
    def datos_globales():
        return {"nombre_negocio": app.config["NOMBRE_NEGOCIO"]}

    @app.route("/")
    def inicio():
        return redirect(url_for("ventas.caja"))

    return app
