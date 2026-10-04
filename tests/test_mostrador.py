"""Pruebas automáticas. Ejecuta:  python -m unittest discover tests"""

import os
import tempfile
import unittest

from mostrador import create_app
from mostrador.db import get_db, init_db, seed_db
from mostrador.servicio_ventas import ErrorVenta, registrar_venta
from mostrador.utils import a_centavos, formato_dinero


class PruebaBase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({"TESTING": True, "DATABASE": self.db_path})
        with self.app.app_context():
            init_db()
            seed_db()
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def stock(self, producto_id):
        with self.app.app_context():
            return get_db().execute(
                "SELECT stock FROM productos WHERE id = ?", (producto_id,)
            ).fetchone()["stock"]


class PruebasDinero(unittest.TestCase):
    def test_convierte_textos_a_centavos(self):
        self.assertEqual(a_centavos("125.50"), 12550)
        self.assertEqual(a_centavos("$1,250"), 125000)
        self.assertEqual(a_centavos("0.105"), 11)  # redondeo comercial

    def test_rechaza_montos_invalidos(self):
        for texto in ("", "abc", "-5"):
            with self.assertRaises(ValueError):
                a_centavos(texto)

    def test_formato(self):
        self.assertEqual(formato_dinero(125050), "$1,250.50")


class PruebasVentas(PruebaBase):
    def test_venta_en_efectivo_descuenta_stock_y_calcula_cambio(self):
        stock_antes = self.stock(1)  # Martillo: $189.00
        with self.app.app_context():
            db = get_db()
            venta_id = registrar_venta(db, [{"producto_id": 1, "cantidad": 2}], "efectivo", 50000)
            venta = db.execute("SELECT * FROM ventas WHERE id = ?", (venta_id,)).fetchone()
        self.assertEqual(venta["total_centavos"], 37800)
        self.assertEqual(venta["cambio_centavos"], 12200)
        self.assertEqual(self.stock(1), stock_antes - 2)

    def test_suma_renglones_repetidos(self):
        with self.app.app_context():
            db = get_db()
            venta_id = registrar_venta(
                db, [{"producto_id": 2, "cantidad": 1}, {"producto_id": 2, "cantidad": 3}], "tarjeta"
            )
            renglones = db.execute(
                "SELECT * FROM venta_detalle WHERE venta_id = ?", (venta_id,)
            ).fetchall()
        self.assertEqual(len(renglones), 1)
        self.assertEqual(renglones[0]["cantidad"], 4)

    def test_sin_stock_no_guarda_nada(self):
        stock_martillo = self.stock(1)
        with self.app.app_context():
            db = get_db()
            with self.assertRaises(ErrorVenta):
                # El martillo sí alcanza, el foco (id 11, hay 3) no: no debe guardarse nada.
                registrar_venta(
                    db, [{"producto_id": 1, "cantidad": 1}, {"producto_id": 11, "cantidad": 99}], "tarjeta"
                )
            ventas = db.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
        self.assertEqual(ventas, 0)
        self.assertEqual(self.stock(1), stock_martillo)

    def test_efectivo_insuficiente(self):
        with self.app.app_context():
            with self.assertRaises(ErrorVenta):
                registrar_venta(get_db(), [{"producto_id": 1, "cantidad": 1}], "efectivo", 1000)

    def test_ticket_vacio_y_metodo_invalido(self):
        with self.app.app_context():
            with self.assertRaises(ErrorVenta):
                registrar_venta(get_db(), [], "tarjeta")
            with self.assertRaises(ErrorVenta):
                registrar_venta(get_db(), [{"producto_id": 1, "cantidad": 1}], "vales")


class PruebasApi(PruebaBase):
    def test_busca_por_nombre_y_codigo(self):
        respuesta = self.client.get("/api/productos?q=martillo")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.get_json()[0]["nombre"], "Martillo de uña 16 oz")

        por_codigo = self.client.get("/api/productos?q=7501005").get_json()
        self.assertEqual(por_codigo[0]["codigo"], "7501005")

    def test_crear_venta(self):
        respuesta = self.client.post("/api/ventas", json={
            "items": [{"producto_id": 5, "cantidad": 1}],
            "metodo_pago": "efectivo",
            "recibido": "100",
        })
        self.assertEqual(respuesta.status_code, 201)
        datos = respuesta.get_json()
        self.assertEqual(datos["cambio_centavos"], 200)
        self.assertEqual(self.client.get(datos["ticket_url"]).status_code, 200)

    def test_crear_venta_con_error(self):
        respuesta = self.client.post("/api/ventas", json={"items": [], "metodo_pago": "tarjeta"})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("vacío", respuesta.get_json()["error"])


class PruebasPaginas(PruebaBase):
    def test_paginas_principales_cargan(self):
        for url in ("/caja", "/ventas", "/productos/", "/productos/nuevo", "/reportes/", "/productos/1/editar"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_agregar_producto_y_codigo_repetido(self):
        datos = {"codigo": "999", "nombre": "Escalera", "precio": "1,499.00", "stock": "2", "stock_minimo": "1"}
        respuesta = self.client.post("/productos/nuevo", data=datos, follow_redirects=True)
        self.assertIn("Escalera", respuesta.get_data(as_text=True))

        repetido = self.client.post("/productos/nuevo", data=datos)
        self.assertIn("Ya existe un producto", repetido.get_data(as_text=True))

    def test_dar_de_baja_conserva_historial(self):
        self.client.post("/api/ventas", json={
            "items": [{"producto_id": 3, "cantidad": 1}], "metodo_pago": "tarjeta",
        })
        self.client.post("/productos/3/baja")
        busqueda = self.client.get("/api/productos?q=cruz").get_json()
        self.assertEqual(busqueda, [])
        self.assertEqual(self.client.get("/ventas/1").status_code, 200)


if __name__ == "__main__":
    unittest.main()
