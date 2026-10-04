-- Esquema de la base de datos del punto de venta.
-- Los montos se guardan en CENTAVOS (enteros) para evitar errores de redondeo
-- que ocurren al usar números decimales (float) con dinero.

DROP TABLE IF EXISTS venta_detalle;
DROP TABLE IF EXISTS ventas;
DROP TABLE IF EXISTS productos;

CREATE TABLE productos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo          TEXT    NOT NULL UNIQUE,
    nombre          TEXT    NOT NULL,
    precio_centavos INTEGER NOT NULL CHECK (precio_centavos >= 0),
    stock           INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    stock_minimo    INTEGER NOT NULL DEFAULT 0 CHECK (stock_minimo >= 0),
    activo          INTEGER NOT NULL DEFAULT 1   -- 0 = dado de baja (se conserva el historial)
);

CREATE TABLE ventas (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha             TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    total_centavos    INTEGER NOT NULL,
    metodo_pago       TEXT    NOT NULL CHECK (metodo_pago IN ('efectivo', 'tarjeta', 'transferencia')),
    recibido_centavos INTEGER NOT NULL,
    cambio_centavos   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE venta_detalle (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id                 INTEGER NOT NULL REFERENCES ventas (id),
    producto_id              INTEGER NOT NULL REFERENCES productos (id),
    cantidad                 INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario_centavos INTEGER NOT NULL,   -- precio al momento de la venta
    subtotal_centavos        INTEGER NOT NULL
);

CREATE INDEX idx_ventas_fecha ON ventas (fecha);
CREATE INDEX idx_detalle_venta ON venta_detalle (venta_id);
