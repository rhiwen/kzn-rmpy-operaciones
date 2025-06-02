# app/__init__.py
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")   # carga siempre el .env de la raíz

# El resto de __init__ (puede quedar vacío)