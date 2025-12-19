import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter


class VisualizadorIncidencias:
    def __init__(self):
        try:
            plt.style.use('fast')
        except:
            pass

    def generar_grafica_incidencias(self, incidencias: list):
        alertas_reales = [
            i for i in incidencias
            if any(k in i.upper() for k in ["ALERTA", "BLOQUEO", "SALTO"])
        ]

        if not alertas_reales:
            print("ℹ️ No hay incidencias reales para graficar en el histograma.")
            return

        conteos = Counter(alertas_reales)

        plt.figure(figsize=(8, 4))
        plt.bar(list(conteos.keys()), list(conteos.values()), color="salmon")
        plt.title("Frecuencia de Alertas Detectadas")
        plt.ylabel("Ocurrencias")
        plt.xticks(rotation=15, ha='right', fontsize=9)
        plt.tight_layout()

        print("📊 Gráfica de frecuencias (barras) generada.")
        plt.show(block=False)
        plt.pause(0.1)

    def generar_grafica_tendencia(self, datos: pd.DataFrame):
        if datos is None or datos.empty:
            print("⚠️ No hay datos para graficar.")
            return

        MAX_PUNTOS = 5000
        total_filas = len(datos)
        step = max(1, total_filas // MAX_PUNTOS)

        muestra = datos.iloc[::step].copy()

        cols_voltaje = [c for c in datos.columns if 'voltage' in c.lower()]
        col_tiempo = 'timestamp' if 'timestamp' in datos.columns else 'tiempo'

        plt.figure(figsize=(10, 5))

        for col in cols_voltaje:
            plt.plot(
                muestra[col_tiempo],
                muestra[col],
                label=col,
                alpha=0.8,
                linewidth=0.6
            )

        plt.title("Monitorización de Voltaje - Fluidez Optimizada")
        plt.ylabel("Nivel (V)")
        plt.xlabel("Tiempo")

        plt.grid(True, linestyle=':', alpha=0.3)
        plt.legend(loc='upper right', fontsize='x-small')

        plt.tight_layout()

        print(f"📈 Gráfica generada")
        plt.show()

    def generar_grafica_sectores(self, incidencias: list):
        """
        Genera un gráfico de tarta mostrando la proporción de tipos de fallos.
        """
        if not incidencias:
            print("ℹ️ No hay incidencias para el gráfico de sectores.")
            return

        conteo = {"Bloqueos": 0, "Saltos de Voltaje": 0}

        for i in incidencias:
            if "BLOQUEO" in i.upper():
                conteo["Bloqueos"] += 1
            elif "SALTO" in i.upper():
                conteo["Saltos de Voltaje"] += 1

        if sum(conteo.values()) == 0:
            print("ℹ️ No hay categorías detectadas para el gráfico de sectores.")
            return

        labels = [k for k, v in conteo.items() if v > 0]
        values = [v for v in conteo.values() if v > 0]


        colors = ['#ff9999', '#66b3ff']

        plt.figure(figsize=(7, 7))
        plt.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            startangle=140,
            colors=colors[:len(labels)],
            explode=[0.05] * len(labels)
        )

        plt.title("Distribución por Tipo de Incidencia")
        plt.axis('equal')
        plt.tight_layout()

        print("📊 Gráfico de sectores generado correctamente.")
        plt.show(block=False)
        plt.pause(0.1)