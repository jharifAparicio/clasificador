"""Punto de entrada raíz que delega la ejecución al paquete src/clasificador."""

import sys
from pathlib import Path

# Añadir el directorio src al path para permitir ejecuciones directas
src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from clasificador.main import main

if __name__ == "__main__":
    main()