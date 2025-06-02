# main.py ─────────────────────────────────────────────────────────────
from pathlib import Path
from dotenv import load_dotenv
import logging
import os

# 1. Cargar variables de entorno (.env en la raíz del proyecto)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# 2. Configurar logging global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# 3. FastAPI + APScheduler
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.schemas import EmailRequest
from app.services.report_service import generate_report  # <- solo esta función

app = FastAPI(title="Redmine Reporter API")

# 4. Scheduler diario (hora:minuto en zona Buenos Aires)
report_time = os.getenv("REPORT_TIME", "10:00")
hour, minute = map(int, report_time.split(":"))
scheduler = BackgroundScheduler()


def daily_job() -> None:
    """Genera y envía automáticamente el reporte diario (sin BackgroundTasks)."""
    logging.info("⏰ Iniciando job programado diario")
    try:
        generate_report(send_email=True, background_tasks=None)
        logging.info("✅ Job diario completado con éxito")
    except Exception as exc:
        logging.exception("❌ Job diario falló: %s", exc)


scheduler.add_job(
    daily_job,
    CronTrigger(hour=hour, minute=minute, timezone="America/Argentina/Buenos_Aires"),
    id="daily_report",
)
scheduler.start()

# 5. Endpoint manual
@app.post("/generar-reporte", response_class=HTMLResponse)
def generar_reporte(request: EmailRequest, background_tasks: BackgroundTasks):
    """
    • `send_email` en el body decide si el reporte se envía por correo.  
    • Devuelve la tabla HTML en la respuesta para visualización rápida.
    """
    logging.info("📥 Solicitud manual de reporte recibida")
    return generate_report(request.send_email, background_tasks)
#Endpoint Manual_2
@app.get("/", response_class=HTMLResponse)
def vista_reporte():
    return generate_report(send_email=False)
