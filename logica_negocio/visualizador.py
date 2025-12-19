import matplotlib.pyplot as plt
import pandas as pd


class VisualizadorIncidencias:
    def __init__(self):
        try:
            plt.style.use('fast')
        except:
            pass

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