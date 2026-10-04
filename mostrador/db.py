"""Conexión a SQLite y comandos de consola para crear y llenar la base de datos."""

import sqlite3

import click
from flask import current_app, g

# Productos de ejemplo de una ferretería: (código, nombre, precio, stock, stock mínimo)
PRODUCTOS_EJEMPLO = [
    ("7501001", "Martillo de uña 16 oz", "189.00", 14, 4),
    ("7501002", "Desarmador plano 1/4\"", "45.50", 30, 8),
    ("7501003", "Desarmador de cruz #2", "45.50", 28, 8),
    ("7501004", "Pinza de electricista 8\"", "165.00", 9, 3),
    ("7501005", "Cinta métrica 5 m", "98.00", 20, 5),
    ("7501006", "Flexómetro 8 m", "149.00", 6, 3),
    ("7501007", "Tornillo para madera 1\" (100 pzas)", "62.00", 40, 10),
    ("7501008", "Taquete de plástico 1/4\" (100 pzas)", "38.00", 35, 10),
    ("7501009", "Clavo estándar 2\" (1 kg)", "54.00", 25, 6),
    ("7501010", "Cinta de aislar negra", "22.00", 60, 15),
    ("7501011", "Foco LED 9 W luz blanca", "35.00", 3, 10),
    ("7501012", "Apagador sencillo", "29.00", 18, 6),
    ("7501013", "Contacto doble polarizado", "42.00", 16, 6),
    ("7501014", "Cable calibre 12 (metro)", "18.50", 300, 50),
    ("7501015", "Brocha 3\"", "48.00", 12, 4),
    ("7501016", "Rodillo para pintar 9\"", "85.00", 7, 3),
    ("7501017", "Lija de agua #120", "9.50", 80, 20),
    ("7501018", "Pegamento PVC 250 ml", "76.00", 2, 4),
    ("7501019", "Llave perica 10\"", "210.00", 5, 2),
    ("7501020", "Candado de latón 40 mm", "135.00", 11, 3),
]


def get_db():
    """Devuelve la conexión de esta petición (la crea si todavía no existe)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # permite usar fila["nombre"]
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Borra y vuelve a crear todas las tablas."""
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


def seed_db():
    """Carga los productos de ejemplo."""
    from .utils import a_centavos

    db = get_db()
    db.executemany(
        "INSERT INTO productos (codigo, nombre, precio_centavos, stock, stock_minimo)"
        " VALUES (?, ?, ?, ?, ?)",
        [(c, n, a_centavos(p), s, m) for c, n, p, s, m in PRODUCTOS_EJEMPLO],
    )
    db.commit()


@click.command("init-db")
def init_db_command():
    """Crea la base de datos vacía."""
    init_db()
    click.echo("Base de datos creada.")


@click.command("seed-db")
def seed_db_command():
    """Crea la base de datos y carga productos de ejemplo."""
    init_db()
    seed_db()
    click.echo(f"Base de datos creada con {len(PRODUCTOS_EJEMPLO)} productos de ejemplo.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command)
