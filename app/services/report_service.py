# app/services/report_service.py
import logging
from datetime import datetime
from typing import Optional
from app.utils.fecha import generar_fecha_reporte

from fastapi import BackgroundTasks
from redminelib.exceptions import ForbiddenError, AuthError

from app.utils.redmine_client import get_projects, process_projects
from app.utils.email_utils import send_report_email
from app.utils.file_manager import data_to_html  # 🧩 ahora usamos el helper externo


def generate_report(
    send_email: bool = True,
    background_tasks: Optional[BackgroundTasks] = None,
) -> str:
    """
    Obtiene proyectos desde Redmine, genera HTML estilizado en memoria
    y lo envía por email si se solicita.

    Ya no se generan archivos físicos.
    """
    logging.info("🔄 Generando reporte…")

    try:
        logging.info("📡 Obteniendo proyectos…")
        projects = get_projects()
        data = process_projects(projects)
        logging.info("✅ Proyectos procesados: %s", len(data))
    except (ForbiddenError, AuthError) as e:
        logging.error("🚫 Permisos insuficientes: %s", e)
        raise
    except Exception as e:
        logging.exception("💥 Error inesperado: %s", e)
        raise

    # Convertir datos en HTML visual (modularizado en file_manager)
    html_content = data_to_html(data)
    timestamp = generar_fecha_reporte()

    # Enviar correo
    if send_email:
        subject = f"KZN-REDMINE - Reporte de Avance Proyectos y Tareas al {timestamp}"
        if background_tasks is not None:
            logging.info("📨 Programando envío de email (BackgroundTasks)…")
            background_tasks.add_task(
                send_report_email,
                subject,
                html_content,
                None  # sin adjuntos
            )
        else:
            logging.info("📨 Enviando email inmediatamente (scheduler)…")
            send_report_email(subject, html_content, None)

    logging.info("🎉 Reporte generado correctamente")
    return html_content
