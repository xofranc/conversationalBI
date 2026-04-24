
import sys
from pathlib import Path

# Agrega la ruta del backend al PYTHONPATH
backend_path = str(Path(__file__).parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)