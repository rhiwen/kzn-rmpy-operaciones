import os
from datetime import datetime, timedelta, date  # Módulos de fechas
from redminelib import Redmine  # Cliente de Redmine
from redminelib.exceptions import (
    ForbiddenError,
    ResourceNotFoundError,
    ResourceBadMethodError,
    ResourceAttrError,
)

# Carga de variables de entorno para conectarse a Redmine
REDMINE_URL = os.getenv("REDMINE_URL")
API_KEY = os.getenv("REDMINE_API_KEY")

# Validación de que las variables están definidas
if not REDMINE_URL or not API_KEY:
    raise RuntimeError("REDMINE_URL o API_KEY no configurados")

# Inicializa el cliente de Redmine
redmine = Redmine(REDMINE_URL.rstrip("/"), key=API_KEY)

# Obtención de proyectos

def get_projects():
    # Intenta obtener los proyectos donde el usuario tiene membresía
    proyectos = []
    try:
        proyectos = redmine.project.filter(membership="*")
    except ResourceBadMethodError:
        try:
            proyectos = redmine.project.all()  # Fallback si la API vieja no soporta membership
        except Exception:
            pass

    # Si no hay proyectos, devuelve lista vacía
    if not proyectos:
        return []

    # Filtra los proyectos activos (status=1)
    activos = [p for p in proyectos if getattr(p, "status", None) == 1 or getattr(getattr(p, "status", None), "id", None) == 1]

    return activos

# Obtención de tareas

def safe_issues(project_id):
    # Intenta traer todas las issues de un proyecto, maneja errores de permisos y recursos
    try:
        return redmine.issue.filter(project_id=project_id, status_id="*")
    except (ForbiddenError, ResourceNotFoundError, ResourceAttrError):
        return []

# Determina si un proyecto tiene tareas

def project_has_relevant(prj):
    issues = safe_issues(prj.id)
    return bool(issues)


def build_relevant_map(projects):
    mapa = {}
    for p in projects:
        try:
            mapa[p.id] = project_has_relevant(p)  # True si tiene tareas
        except ForbiddenError:
            mapa[p.id] = False  # Si no tiene permisos, lo marca como no relevante
    return mapa

# Obtener la cadena de padres de un proyecto

def parent_chain_names(prj):
    chain, cur = [], prj
    while hasattr(cur, "parent") and hasattr(cur.parent, "id"):
        chain.append(cur.parent.name)
        try:
            cur = redmine.project.get(cur.parent.id)
        except Exception:
            break  # Si falla al traer el padre, corta la búsqueda
    return chain

#Determina si un proyecto tiene hijos

def has_children(pid):
    try:
        for _ in redmine.project.filter(parent_id=pid, limit=1):
            return True  # Si encuentra al menos uno, devuelve True
    except Exception:
        pass
    return False  # Si falla o no encuentra hijos, devuelve False

# Procesamiento de los proyectos

def process_projects(projects):
    # Mapeo de status (por si en algún momento se usa)
    status_map = {
        1: "Activo",
        5: "Archivado",
        9: "Cerrado"
    }

    # Genera mapa de relevancia de proyectos
    rel_map = build_relevant_map(projects)

    # Fechas de referencia (hoy, últimos 30 días, semana anterior)
    today = datetime.today()
    start_30 = (today - timedelta(days=30)).date()
    end_today = today.date()
    last_mon = (today - timedelta(days=today.weekday() + 7)).date()  # Lunes de la semana pasada
    last_fri = last_mon + timedelta(days=4)  # Viernes de la semana pasada

    data = []

    # Palabras clave para filtrar equipos
    keywords = ("DATA", "CONSULTORIA", "DESARROLLO")

    # Recorre todos los proyectos
    for prj in projects:
        if not rel_map.get(prj.id):
            continue  # Si no tiene tareas relevantes, lo saltea

        chain = parent_chain_names(prj)
        proyecto_padre = chain[0] if chain else ""
        equipo = chain[-1] if len(chain) > 1 else ""
        if proyecto_padre == equipo:
            proyecto_padre = ""

        # Filtra solo proyectos que contengan alguna palabra clave en el nombre del equipo
        if not any(kw in equipo.upper() for kw in keywords):
            continue

        es_padre = has_children(prj.id)
        proyecto_name = "" if es_padre else prj.name

        # Inicializa el registro de métricas para el proyecto
        rec = {
            "Equipo": equipo,
            "Proyecto Padre": proyecto_padre,
            "Proyecto": proyecto_name,
            "Fecha de inicio": None,
            "Fecha finalización": None,
            "Tareas totales": 0,
            "Tareas abiertas": 0,
            "Tareas modificadas última semana": 0,
            "Tareas cerradas última semana": 0,
            "Tareas modificadas últimos 30 días": 0,
            "Tareas cerradas últimos 30 días": 0,
            "Horas estimadas": 0.0,
            "Horas insumidas": 0.0,
        }

        issues = safe_issues(prj.id)

        # Carga de registros de horas desde caché (últimos 12 meses)
        from app.utils.cache_manager import get_cached_time_entries
        try:
            entries_all = get_cached_time_entries(redmine, prj.id, months=12)
        except ForbiddenError:
            entries_all = []

        # Construye diccionario de time entries por issue
        hrs_ids = {e.issue.id for e in entries_all if hasattr(e, "issue")}
        te_by_issue = {}
        for e in entries_all:
            if hasattr(e, "issue"):
                te_by_issue.setdefault(e.issue.id, []).append(e)

        # Procesamiento de cada issue
        for i in issues:
            rec["Tareas totales"] += 1  # Cuenta tarea

            # Evalúa fecha de inicio mínima
            s = getattr(i, "start_date", None)
            if s:
                s_date = s.date() if hasattr(s, "date") else s
                if rec["Fecha de inicio"] is None or s_date < rec["Fecha de inicio"]:
                    rec["Fecha de inicio"] = s_date

            # Evalúa fecha de fin máxima
            d = getattr(i, "due_date", None)
            if d:
                d_date = d.date() if hasattr(d, "date") else d
                if rec["Fecha finalización"] is None or d_date > rec["Fecha finalización"]:
                    rec["Fecha finalización"] = d_date

            # Evalúa estado de la tarea (cerrada o abierta)
            st = getattr(i.status, "id", None)
            if st in (6, 5, 21, 9):  # Estados cerrados
                c = getattr(i, "closed_on", None)
                if c:
                    c_date = c.date()
                    if last_mon <= c_date <= last_fri:
                        rec["Tareas cerradas última semana"] += 1
                    if start_30 <= c_date <= end_today:
                        rec["Tareas cerradas últimos 30 días"] += 1
            else:
                rec["Tareas abiertas"] += 1

            # Evalúa fechas de modificación
            u = getattr(i, "updated_on", None)
            if u:
                u_date = u.date()
                if last_mon <= u_date <= last_fri:
                    rec["Tareas modificadas última semana"] += 1
                if start_30 <= u_date <= end_today:
                    rec["Tareas modificadas últimos 30 días"] += 1

            # Horas estimadas
            est = getattr(i, "estimated_hours", None)
            if est:
                rec["Horas estimadas"] += round(est, 2)

            # Horas insumidas por time entries asociados
            for te in te_by_issue.get(i.id, []):
                rec["Horas insumidas"] += round(float(getattr(te, "hours", 0) or 0), 2)

        # Redondea horas acumuladas
        rec["Horas estimadas"] = round(rec["Horas estimadas"], 2)
        rec["Horas insumidas"] = round(rec["Horas insumidas"], 2)

        # Calcula porcentajes de avance de tareas y consumo de horas
        rec["Progreso tareas"] = f"{((rec['Tareas totales'] - rec['Tareas abiertas']) / rec['Tareas totales'] * 100):.2f}%" if rec["Tareas totales"] > 0 else "0.00%"
        rec["Horas consumidas"] = f"{rec['Horas insumidas'] / rec['Horas estimadas'] * 100:.2f}%" if rec["Horas estimadas"] > 0 else "0.00%"

        # Agrega el registro al dataset final
        data.append(rec)

    # Devuelve lista completa de registros procesados
    return data
