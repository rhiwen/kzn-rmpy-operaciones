import os
from datetime import datetime, timedelta, date
from redminelib import Redmine
from redminelib.exceptions import (
    ForbiddenError,
    ResourceNotFoundError,
    ResourceBadMethodError,
    ResourceAttrError,
)

# ────────────────────────
# CARGA DE CREDENCIALES
# ────────────────────────
REDMINE_URL = os.getenv("REDMINE_URL")
API_KEY = os.getenv("REDMINE_API_KEY")

if not REDMINE_URL or not API_KEY:
    raise RuntimeError("REDMINE_URL o API_KEY no configurados")

redmine = Redmine(REDMINE_URL.rstrip("/"), key=API_KEY)

# ────────────────────────
# OBTENCIÓN DE PROYECTOS
# ────────────────────────

def get_projects():
    proyectos = []
    try:
        proyectos = redmine.project.filter(membership="*")
    except ResourceBadMethodError:
        try:
            proyectos = redmine.project.all()
        except Exception:
            pass

    if not proyectos:
        return []

    activos = [p for p in proyectos if getattr(p, "status", None) == 1 or getattr(getattr(p, "status", None), "id", None) == 1]
    return activos

# ────────────────────────
# OBTENCIÓN DE ISSUES SEGURO
# ────────────────────────

def safe_issues(project_id):
    try:
        return redmine.issue.filter(project_id=project_id, status_id="*")
    except (ForbiddenError, ResourceNotFoundError, ResourceAttrError):
        return []

# ────────────────────────
# VERIFICA SI UN PROYECTO TIENE TAREAS
# ────────────────────────

def project_has_relevant(prj):
    issues = safe_issues(prj.id)
    return bool(issues)

def build_relevant_map(projects):
    mapa = {}
    for p in projects:
        try:
            mapa[p.id] = project_has_relevant(p)
        except ForbiddenError:
            mapa[p.id] = False
    return mapa

# ────────────────────────
# CADENA DE PADRES
# ────────────────────────

def parent_chain_names(prj):
    chain, cur = [], prj
    while hasattr(cur, "parent") and hasattr(cur.parent, "id"):
        chain.append(cur.parent.name)
        try:
            cur = redmine.project.get(cur.parent.id)
        except Exception:
            break
    return chain

# ────────────────────────
# VERIFICACIÓN DE HIJOS
# ────────────────────────

def has_children(pid):
    try:
        for _ in redmine.project.filter(parent_id=pid, limit=1):
            return True
    except Exception:
        pass
    return False

# ────────────────────────
# PROCESAMIENTO PRINCIPAL DE PROYECTOS
# ────────────────────────

def process_projects(projects):
    rel_map = build_relevant_map(projects)

    today = datetime.today()
    start_30 = (today - timedelta(days=30)).date()
    end_today = today.date()

    weekday = today.weekday()
    days_since_saturday = (weekday - 5) % 7
    last_saturday = (today - timedelta(days=days_since_saturday)).date()
    last_sunday = last_saturday - timedelta(days=6)

    data = []
    keywords = ("DATA", "CONSULTORIA", "DESARROLLO", "TECNOLOGIA")

    for prj in projects:
        if not rel_map.get(prj.id):
            continue

        chain = parent_chain_names(prj)
        equipo = chain[-1] if len(chain) > 1 else ""

        if not any(kw in equipo.upper() for kw in keywords):
            continue

        es_padre = has_children(prj.id)
        proyecto_name = "" if es_padre else prj.name

        issues = safe_issues(prj.id)

        # Cache de time entries
        from app.utils.cache_manager import get_cached_time_entries
        try:
            entries_all = get_cached_time_entries(redmine, prj.id, months=12)
        except ForbiddenError:
            entries_all = []

        # Armado del diccionario por issue
        te_by_issue = {}
        for e in entries_all:
            if hasattr(e, "issue") and e.issue:
                te_by_issue.setdefault(e.issue.id, []).append(e)

        # Agrupar issues por versión
        versions_data = {}
        
        for i in issues:
            # Obtener la versión
            version_name = "Sin versión"
            if hasattr(i, "fixed_version") and i.fixed_version:
                version_name = getattr(i.fixed_version, "name", "Sin versión")
            
            # Inicializar la versión si no existe
            if version_name not in versions_data:
                versions_data[version_name] = {
                    "Equipo": equipo,
                    "Proyecto": proyecto_name,
                    "Version": version_name,
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

            rec = versions_data[version_name]
            rec["Tareas totales"] += 1

            # Fechas
            s = getattr(i, "start_date", None)
            if s:
                s_date = s.date() if hasattr(s, "date") else s
                if rec["Fecha de inicio"] is None or s_date < rec["Fecha de inicio"]:
                    rec["Fecha de inicio"] = s_date

            d = getattr(i, "due_date", None)
            if d:
                d_date = d.date() if hasattr(d, "date") else d
                if rec["Fecha finalización"] is None or d_date > rec["Fecha finalización"]:
                    rec["Fecha finalización"] = d_date

            # Estado de tareas
            st = getattr(i.status, "id", None)
            if st in (6, 5, 21, 9):
                c = getattr(i, "closed_on", None)
                if c:
                    c_date = c.date()
                    if last_sunday <= c_date <= last_saturday:
                        rec["Tareas cerradas última semana"] += 1
                    if start_30 <= c_date <= end_today:
                        rec["Tareas cerradas últimos 30 días"] += 1
            else:
                rec["Tareas abiertas"] += 1

            # Actualizaciones
            u = getattr(i, "updated_on", None)
            if u:
                u_date = u.date()
                if last_sunday <= u_date <= last_saturday:
                    rec["Tareas modificadas última semana"] += 1
                if start_30 <= u_date <= end_today:
                    rec["Tareas modificadas últimos 30 días"] += 1

            # Horas estimadas
            est = getattr(i, "estimated_hours", None)
            if est:
                rec["Horas estimadas"] += round(est, 2)

            # Horas insumidas
            for e in te_by_issue.get(i.id, []):
                rec["Horas insumidas"] += round(float(e.hours or 0), 2)

        # Calcular métricas finales para cada versión
        for version_name, rec in versions_data.items():
            rec["Horas estimadas"] = round(rec["Horas estimadas"], 2)
            rec["Horas insumidas"] = round(rec["Horas insumidas"], 2)

            rec["Progreso tareas"] = f"{((rec['Tareas totales'] - rec['Tareas abiertas']) / rec['Tareas totales'] * 100):.2f}%" if rec["Tareas totales"] > 0 else "0.00%"
            rec["Horas consumidas"] = f"{rec['Horas insumidas'] / rec['Horas estimadas'] * 100:.2f}%" if rec["Horas estimadas"] > 0 else "0.00%"

            data.append(rec)

    return data