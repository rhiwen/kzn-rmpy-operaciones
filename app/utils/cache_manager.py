# app/utils/cache_manager.py
import os
import pickle
from datetime import datetime, timedelta

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cached_time_entries(redmine, project_id, months: int = 12):
    """
    Devuelve la lista combinada de time_entries históricos + recientes
    para un proyecto, utilizando caché local en disco.
    """
    cache_file = os.path.join(CACHE_DIR, f"time_entries_{project_id}.pkl")

    if os.path.exists(cache_file):
        # Carga histórica previa
        with open(cache_file, "rb") as f:
            historico = pickle.load(f)
        ids_historicos = {e.id for e in historico}

        # Nueva consulta limitada por tiempo
        desde = (datetime.today() - timedelta(days=365)).date()
        nuevos = list(redmine.time_entry.filter(project_id=project_id, from_date=desde))
        combinados = historico + [e for e in nuevos if e.id not in ids_historicos]

        # Actualiza la caché
        with open(cache_file, "wb") as f:
            pickle.dump(combinados, f)
        return combinados
    else:
        # Primera vez: cargar todo y cachear
        todos = list(redmine.time_entry.filter(project_id=project_id))
        with open(cache_file, "wb") as f:
            pickle.dump(todos, f)
        return todos
