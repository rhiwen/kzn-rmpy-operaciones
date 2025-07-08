# Importación de módulos estándar y externos
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Sequence, Union
from fastapi import BackgroundTasks
from redminelib.exceptions import AuthError, ForbiddenError

# Importación de funciones utilitarias del proyecto
from app.utils.redmine_client import get_projects, process_projects  # Obtiene y procesa proyectos desde Redmine
from app.utils.file_manager import data_to_html  # Convierte datos a formato HTML para emails
from app.utils.gestor_mails import destinatarios_equipo, get_destinatarios  # Obtiene destinatarios según alias o lista directa
from app.utils.email_utils import send_html_email  # Función para enviar emails con contenido HTML
from app.utils.fecha import generar_fecha_reporte  # Genera una cadena con la fecha actual en formato legible

# Función para convertir un texto en slug (minúsculas, sin caracteres especiales, separado por "_")
def _slug(text: str) -> str:
    import re
    text = re.sub(r'[^A-Za-z0-9]+', ' ', text, flags=re.I).lower()
    return "_".join(text.split())

# Asigna un alias estandarizado para identificar el equipo según el nombre
def _alias_equipo(nombre: str) -> str:
    n = nombre.lower()
    if "data" in n:
        return "data"
    if "consultoria" in n or "consultores" in n:
        return "consultoria"
    if "desarrollo" in n:
        return "desarrollo"
    if "tactica" in n:
        return "consultores_tactica"
    if "tecnologia" in n:
        return "tecnologia"
    return _slug(nombre)  # Si no coincide con ninguno, genera un slug genérico

# Filtra el dataset dejando solo los registros del equipo indicado
def _filtrar(data: List[Dict[str, Any]], equipo: str) -> List[Dict[str, Any]]:
    return [r for r in data if (r.get("Equipo") or "").strip() == equipo]

# Función principal que genera el reporte y, si corresponde, envía los mails
def generate_report(
    send_email: bool = True,  # Indica si se debe enviar el mail
    destinatarios: Optional[Union[str, Sequence[str]]] = None,  # Destinatarios opcionales (manuales)
    background_tasks: Optional[BackgroundTasks] = None  # Para enviar mails en segundo plano en FastAPI
) -> str:
    try:
        logging.info("🔄 Generando reporte de proyectos por equipo…")

        # Obtiene los proyectos desde Redmine y los procesa
        projects = get_projects()
        data = process_projects(projects)
        logging.info("✅ Proyectos procesados: %s", len(data))

        # Si se especifican destinatarios, se envía un único reporte general
        if destinatarios:
            html_all = data_to_html(data)  # Convierte todo el reporte a HTML
            subject = (
                "KZN-REDMINE - Reporte de avance de proyectos y tareas al "
                + generar_fecha_reporte()
                + " - EQUIPO TODOS"
            )

            # Si los destinatarios se pasaron como string, se resuelven usando la función
            recip = (
                get_destinatarios(destinatarios)
                if isinstance(destinatarios, str)
                else list(destinatarios)
            )

            send_html_email(subject, html_all, recip)  # Envío directo del correo
            return "Reporte manual enviado"

        # Si no se especificaron destinatarios, se genera y envía un reporte por equipo
        equipos = sorted({r["Equipo"] for r in data if r.get("Equipo")})  # Lista única de equipos presentes en la data
        enviados = 0  # Contador de reportes enviados

        for eq in equipos:
            alias = _alias_equipo(eq)  # Determina el alias del equipo
            recip = destinatarios_equipo(alias)  # Obtiene los destinatarios asociados al alias

            if not recip:
                logging.info("⏭ %s sin destinatarios; se omite", eq)
                continue  # Si no hay destinatarios, se saltea ese equipo

            html = data_to_html(_filtrar(data, eq))  # Convierte en HTML solo los registros de ese equipo
            subject = (
                "KZN-REDMINE - Reporte de avance de proyectos y tareas al "
                + generar_fecha_reporte()
                + " - "
                + eq
            )

            # Envío del email (en segundo plano si se usa FastAPI con background_tasks)
            if send_email:
                if background_tasks:
                    background_tasks.add_task(send_html_email, subject, html, recip)
                else:
                    send_html_email(subject, html, recip)

            enviados += 1  # Se contabiliza el envío

        logging.info("🎉 Reportes enviados: %s", enviados)
        return f"Reportes generados para {enviados} equipos"

    # Manejo de errores de autenticación o permisos en Redmine
    except (AuthError, ForbiddenError) as e:
        logging.error("🚫 Error Redmine: %s", e)
        raise

    # Manejo de cualquier otro error inesperado
    except Exception as e:
        logging.exception("💥 Error inesperado: %s", e)
        raise
