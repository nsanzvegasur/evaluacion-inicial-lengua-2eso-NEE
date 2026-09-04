# Punto de entrada estable de la aplicación NNEE.
# Se ejecuta el núcleo directamente para evitar el error de importación _app_core.
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("_app_core.py")), run_name="__main__")
