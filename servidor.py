"""Enciende el punto de venta sin ventana negra.

Lo usa abrir_mostrador.vbs a través de pythonw.exe (Python sin consola).
Como no hay consola, los mensajes se guardan en instance/servidor.log.
"""

import os
import sys

CARPETA = os.path.dirname(os.path.abspath(__file__))
INSTANCIA = os.path.join(CARPETA, "instance")
PUERTO = int(os.environ.get("PUERTO", "5000"))

os.makedirs(INSTANCIA, exist_ok=True)

# pythonw no tiene dónde escribir mensajes: los mandamos a un archivo.
if sys.stdout is None or sys.stderr is None:
    registro = open(os.path.join(INSTANCIA, "servidor.log"), "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = registro

# No registra cada clic en el archivo, solo los errores (para que no crezca sin fin).
import logging  # noqa: E402
logging.getLogger("werkzeug").setLevel(logging.ERROR)

sys.path.insert(0, CARPETA)
from mostrador import create_app  # noqa: E402
from mostrador.db import init_db  # noqa: E402

app = create_app()

# Si es la primera vez, crea la base de datos vacía.
if not os.path.exists(app.config["DATABASE"]):
    with app.app_context():
        init_db()

# Guarda el número de proceso para que cerrar_mostrador.vbs pueda apagarlo.
with open(os.path.join(INSTANCIA, "servidor.pid"), "w") as f:
    f.write(str(os.getpid()))

print(f"Mostrador encendido en http://127.0.0.1:{PUERTO}")
app.run(host="127.0.0.1", port=PUERTO, debug=False, use_reloader=False)
