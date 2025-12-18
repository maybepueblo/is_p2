import matplotlib.pyplot as plt
from typing import List
import pandas as pd


class VisualizadorIncidencias:
    def generar_grafica_incidencias(self, incidencias: List[str]):
        if not incidencias:
            return

        conteos = {x: incidencias.count(x) for x in incidencias}
        plt.figure(figsize=(6, 4))

        # CAMBIO AQUÍ: Envolvemos en list(...)
        claves = list(conteos.keys())
        valores = list(conteos.values())

        plt.bar(claves, valores, color="salmon")
        plt.title("Reporte de Incidencias")
        print("Generando gráfica de incidencias...")
        plt.show()

    def generar_grafica_tendencia(self, datos: pd.DataFrame):
        plt.figure(figsize=(10, 5))
        plt.plot(datos["tiempo"], datos["voltaje"], label="Voltaje")
        plt.title("Tendencia de Voltaje en el Tiempo")
        plt.legend()
        print("Generando gráfica de tendencia...")
        plt.show()
