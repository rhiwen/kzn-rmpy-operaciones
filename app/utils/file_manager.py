from typing import List, Dict, Any
import pandas as pd
import re
from app.utils.fecha import generar_fecha_reporte

def data_to_html(rows: List[Dict[str, Any]]) -> str:
    """
    Genera el HTML del reporte de proyectos con corte por VERSION.
    """
    if not rows:
        return "<p>No se encontraron proyectos relevantes.</p>"

    df = pd.DataFrame(rows)

    if "Equipo" not in df.columns:
        return "<p>Error: Falta la columna 'Equipo'.</p>"

    columnas_ordenadas = [
        "Proyecto", "Version", "Fecha de inicio", "Fecha finalización",
        "Tareas abiertas", "Tareas totales", "Progreso tareas", "Tareas modificadas última semana",
        "Tareas cerradas última semana", "Tareas modificadas últimos 30 días",
        "Tareas cerradas últimos 30 días", "Horas estimadas", "Horas insumidas", "Horas consumidas"
    ]

    fecha_reporte = generar_fecha_reporte()

    html = f"""
    <div style='font-family: Arial, sans-serif; font-size: 13px;'>
    <h2 style='margin-bottom: 8px;'>KZN - Reporte de Avance: Proyectos y Versiones al {fecha_reporte}</h2>
    """

    for equipo, grupo in df.groupby("Equipo"):
        grupo = grupo.drop(columns=["Equipo"])
        grupo = grupo[columnas_ordenadas]

        html += f"<h3 style='margin-top: 20px; margin-bottom: 6px; font-size: 14px;'>{equipo}</h3>"

        html += """
        <table style='border-collapse: collapse; width: 100%; table-layout: fixed;'>
        <thead><tr>
        """

        anchos = {
            "Proyecto": "150px",
            "Version": "180px",
            "Fecha de inicio": "90px",
            "Fecha finalización": "90px",
            "Tareas totales": "70px",
            "Tareas abiertas": "70px",
            "Tareas modificadas última semana": "70px",
            "Tareas cerradas última semana": "70px",
            "Tareas modificadas últimos 30 días": "70px",
            "Tareas cerradas últimos 30 días": "70px",
            "Horas estimadas": "90px",
            "Horas insumidas": "90px",
            "Progreso tareas": "90px",
            "Horas consumidas": "90px"
        }

        for col in columnas_ordenadas:
            html += (
                f"<th style='border: 1px solid #ccc; padding: 4px; "
                f"background-color: #f2f2f2; text-align: center; vertical-align: middle; "
                f"width: {anchos[col]};'>{col}</th>"
            )
        html += "</tr></thead><tbody>"

        # Línea gruesa después del header
        html += "<tr><td colspan='14' style='border: none; border-bottom: 3px solid #333; padding: 0; height: 1px;'></td></tr>"

        # Ordenar por proyecto y luego por versión (Sin versión primero, luego por fecha de inicio)
        grupo['orden_version'] = grupo.apply(lambda row: (
            0 if row["Version"] == "Sin versión" else 
            1 if row["Fecha de inicio"] is not None else 2
        ), axis=1)
        
        grupo['fecha_sort'] = grupo.apply(lambda row: (
            "" if row["Version"] == "Sin versión" else
            row["Fecha de inicio"] if row["Fecha de inicio"] is not None else
            "9999-12-31"
        ), axis=1)
        
        grupo_sorted = grupo.sort_values(['Proyecto', 'orden_version', 'fecha_sort'])
        grupo_sorted = grupo_sorted.drop(['orden_version', 'fecha_sort'], axis=1)
        
        # Agrupar por proyecto y ordenar versiones
        proyecto_actual = None
        for _, row in grupo_sorted.iterrows():
            proyecto_nombre = row["Proyecto"]
            
            # Si cambió el proyecto, agregar línea gruesa
            if proyecto_actual is not None and proyecto_actual != proyecto_nombre:
                html += "<tr><td colspan='14' style='border: none; border-bottom: 3px solid #333; padding: 0; height: 1px;'></td></tr>"
            
            proyecto_actual = proyecto_nombre
            
            html += "<tr>"
            for col in columnas_ordenadas:
                cell = row[col]

                # Formateo
                if col in ["Horas estimadas", "Horas insumidas"] and isinstance(cell, (int, float)):
                    valor = f"{cell:.2f}"
                elif col in ["Progreso tareas", "Horas consumidas"] and isinstance(cell, str) and "%" in cell:
                    valor = cell.split(".")[0] + "%"
                else:
                    valor = cell if cell is not None else ""

                # Proyecto y Version con separación por salto de línea si contiene separador
                if col in ["Proyecto", "Version"] and isinstance(valor, str):
                    match = re.search(r"\s*[-–—]\s*", valor)
                    if match:
                        idx = match.start()
                        parte1 = valor[:idx].strip()
                        parte2 = valor[idx + len(match.group()):].strip()
                        valor = (
                            f"{parte1}<br>"
                            f"<span style='font-size:12px;color:#555;'>{parte2}</span>"
                        )

                html += (
                    f"<td style='border: 1px solid #ccc; padding: 2px 4px; "
                    f"text-align: center; vertical-align: middle; white-space: normal; overflow-wrap: break-word;'>"
                    f"{valor}</td>"
                )
            html += "</tr>"

        # Línea gruesa al final
        html += "<tr><td colspan='14' style='border: none; border-bottom: 3px solid #333; padding: 0; height: 1px;'></td></tr>"

        html += "</tbody></table>"

    html += "</div>"
    return html