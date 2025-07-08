import os
import re
from collections import defaultdict
from typing import List, Dict, Optional
from dotenv import load_dotenv
from redminelib import Redmine

# ────────────────────────────────────────────────
# Cargar variables de entorno
# ────────────────────────────────────────────────
load_dotenv()
REDMINE_URL = os.getenv("REDMINE_URL")
API_KEY = os.getenv("REDMINE_API_KEY")
MAIL_DOMAIN = os.getenv("MAIL_DOMAIN", "@kaizen2b.com")

if not REDMINE_URL or not API_KEY:
    raise RuntimeError("Faltan REDMINE_URL o API_KEY en el .env")

redmine = Redmine(REDMINE_URL.rstrip("/"), key=API_KEY)

# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────
def _slug(txt: str) -> str:
    txt = re.sub(r"[^A-Za-z0-9]+", " ", txt)
    txt = txt.lower().replace("kzn", "")
    return "_".join(txt.split())

# ────────────────────────────────────────────────
# Construcción del diccionario de alias → mails
# ────────────────────────────────────────────────
def construir_diccionario_equipos() -> Dict[str, List[str]]:
    # Alias corregidos según IDs reales en Redmine
    ALIAS_TO_GROUP_IDS = {
    "desarrollo": [53],
    "data": [100],
    "tecnologia": [128],
    "consultores_tactica": [45],     
    "consultoria": [45]                
}

    alias_map: Dict[str, List[str]] = defaultdict(list)

    for alias, group_ids in ALIAS_TO_GROUP_IDS.items():
        for gid in group_ids:
            try:
                grupo = redmine.group.get(gid, include="users")
                for u in grupo.users:
                    try:
                        full_user = redmine.user.get(u.id)
                        alias_map[alias].append(f"{full_user.login}{MAIL_DOMAIN}")
                    except Exception as ue:
                        print(f"❌ No se pudo acceder al usuario {u.id} del grupo {alias}: {ue}")
            except Exception as e:
                print(f"❌ Error al obtener grupo {gid} (alias {alias}): {e}")

    # Resolver variables de entorno por grupo
    grupo_emails: Dict[str, List[str]] = {}
    for env_key, raw in os.environ.items():
        if not env_key.startswith("EMAIL_") or not raw.strip():
            continue

        raw = raw.strip()
        grupo_key = env_key.replace("EMAIL_", "").strip().lower()
        destinatarios: List[str] = []

        for token in [t.strip() for t in raw.split(",") if t.strip()]:
            if "@" in token:
                destinatarios.append(token)
            else:
                alias = token.lower()
                if alias in alias_map:
                    destinatarios.extend(alias_map[alias])
                else:
                    print(f"⚠️ Alias desconocido: '{token}' (clave {env_key})")

        if destinatarios:
            grupo_emails[grupo_key] = sorted(set(destinatarios))

    # EMAIL_TOTAL (todos los mails únicos)
    total_raw = os.getenv("EMAIL_TOTAL", "").strip()
    if total_raw:
        todos = sorted({mail for mails in alias_map.values() for mail in mails})
        extra = [t for t in total_raw.split(",") if "@" in t]
        grupo_emails["total"] = sorted(set(todos + extra))

    return grupo_emails

# ────────────────────────────────────────────────
# Consulta directa por nombre
# ────────────────────────────────────────────────
def destinatarios_equipo(nombre_equipo: str) -> Optional[List[str]]:
    env_key = f"EMAIL_{_slug(nombre_equipo).upper()}"
    raw = os.getenv(env_key, "").strip()
    if not raw:
        return None

    alias_map = construir_diccionario_equipos()
    destinatarios: List[str] = []
    for token in [t.strip() for t in raw.split(",") if t.strip()]:
        if "@" in token:
            destinatarios.append(token)
        else:
            alias = token.lower()
            if alias in alias_map:
                destinatarios.extend(alias_map[alias])
            else:
                print(f"⚠️ Alias desconocido: '{token}' (equipo {nombre_equipo})")

    return sorted(set(destinatarios)) if destinatarios else None

# ────────────────────────────────────────────────
# Compatibilidad con reportes anteriores
# ────────────────────────────────────────────────
def get_destinatarios(nombre_equipo: str) -> Optional[List[str]]:
    return destinatarios_equipo(nombre_equipo)
