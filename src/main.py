"""Script de entrada para ejecución directa desde la carpeta src."""

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from clasificador.main import main

if __name__ == "__main__":
    main()
