# app/utils/date_utils.py

from datetime import datetime

def generar_fecha_reporte() -> str:
    """
    Devuelve el string de fecha/hora 
    """
    now = datetime.now()
    return f"{now.year}/{now.month:02d}/{now.day:02d} {now.hour:02d}:{now.minute:02d}:{now.second:02d}"
