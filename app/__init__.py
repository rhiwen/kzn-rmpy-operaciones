from pathlib import Path
from dotenv import load_dotenv
import sys

# Detección si está corriendo como EXE o en desarrollo
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
