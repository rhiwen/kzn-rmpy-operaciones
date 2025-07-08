# main.py ─────────────────────────────────────────────────────────────
"""
Arranque de la API + scheduler:

• Carga variables del .env
• Programa UN solo job diario (hora REPORT_TIME) que:
      – Obtiene proyectos 1 vez
      – Genera los 4 reportes (Data, Consultoría, Desarrollo, Tecnología)
      – Envía cada uno al destinatario configurado en .env
• Expone endpoints para lanzar el reporte manualmente
"""

from pathlib import Path
from dotenv import load_dotenv
import logging
import os

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.schemas import EmailRequest
from app.services.report_service import generate_report

# ──────────────────────────────────────────────────────
#  Cargar .env y configurar logging
# ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="Redmine Reporter API")

# ──────────────────────────────────────────────────────
#  Job maestro diario (un solo disparo)
# ──────────────────────────────────────────────────────
def daily_master_job() -> None:
    """Genera todos los reportes y los envía secuencialmente."""
    logging.info("⏰ Iniciando job maestro diario")
    try:
        # generate_report recorre los equipos y envía según .env
        generate_report(send_email=True, background_tasks=None)
        logging.info("✅ Job maestro completado")
    except Exception as exc:
        logging.exception("❌ Job maestro falló: %s", exc)

# Hora programada (HH:MM ART) desde .env
report_time = os.getenv("REPORT_TIME", "21:52")
hour, minute = map(int, report_time.split(":"))

scheduler = BackgroundScheduler()
scheduler.add_job(
    daily_master_job,
    CronTrigger(hour=hour, minute=minute, timezone="America/Argentina/Buenos_Aires"),
    id="daily_master",
)
scheduler.start()

# ──────────────────────────────────────────────────────
#  Endpoints
# ──────────────────────────────────────────────────────
@app.post("/generar-reporte", response_class=HTMLResponse)
def generar_reporte(request: EmailRequest, background_tasks: BackgroundTasks):
    """
    Lanza el reporte manualmente.

    Body JSON:
    {
      "send_email": true,
      "destinatarios": "data" | "correo1,correo2" | null
    }
    """
    logging.info("📥 Solicitud manual de reporte recibida")
    return generate_report(
        send_email=request.send_email,
        destinatarios=request.destinatarios,
        background_tasks=background_tasks,
    )

@app.get("/", response_class=HTMLResponse)
def vista_reporte():
    """
    Devuelve el HTML completo del reporte, sin enviar correos.
    Muestra todos los proyectos juntos (sin dividir por grupo).
    """
    from app.utils.redmine_client import get_projects, process_projects
    from app.utils.file_manager import data_to_html

    try:
        projects = get_projects()
        data = process_projects(projects)

        if not data:
            return "<p>No se encontraron proyectos relevantes.</p>"

        html = data_to_html(data)

        page = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reporte de Proyectos (completo)</title>
        </head>
        <body style="margin: 24px; font-family: Arial, sans-serif;">
        {html}
        </body>
        </html>
        """
        return HTMLResponse(content=page)

    except Exception as e:
        return HTMLResponse(content=f"<p>Error al generar reporte: {e}</p>", status_code=500)
