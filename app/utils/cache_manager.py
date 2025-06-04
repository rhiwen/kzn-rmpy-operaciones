# app/utils/cache_manager.py

import os
import pickle
from datetime import datetime, timedelta

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cached_time_entries(redmine, project_id, months: int = 12):
    """
    Devuelve la lista de time_entries con lógica de actualización parcial:
    ▸ Si existe caché previa: refresca los últimos `months` meses.
    ▸ Si no existe caché: descarga todo y guarda.
    """
    cache_file = os.path.join(CACHE_DIR, f"time_entries_{project_id}.pkl")

    if os.path.exists(cache_file):
        # Carga histórica previa
        with open(cache_file, "rb") as f:
            historico = pickle.load(f)
        ids_historicos = {e.id for e in historico}

        # Nuevo período a refrescar
        desde = (datetime.today() - timedelta(days=months*30)).date()

        nuevos = list(redmine.time_entry.filter(project_id=project_id, from_date=desde))

        # Reemplaza los time_entries nuevos si existen duplicados
        nuevos_ids = {e.id for e in nuevos}
        historico_filtrado = [e for e in historico if e.id not in nuevos_ids]

        combinados = historico_filtrado + nuevos

        # Actualiza la caché
        with open(cache_file, "wb") as f:
            pickle.dump(combinados, f)

        return combinados

    else:
        # Primera ejecución: descarga todo
        todos = list(redmine.time_entry.filter(project_id=project_id))
        with open(cache_file, "wb") as f:
            pickle.dump(todos, f)
        return todos
