import matplotlib.pyplot as plt
from typing import List
import pandas as pd


class VisualizadorIncidencias:
    def generar_grafica_incidencias(self, incidencias: List[str]):
        # Si la lista viene vacía o con mensajes de "Sistema estable", no graficamos
        alertas_reales = [i for i in incidencias if
                          "ALERTA" in i.upper() or "BLOQUEO" in i.upper() or "SALTO" in i.upper()]

        if not alertas_reales:
            print("ℹ️ No hay incidencias reales para graficar.")
            return

        conteos = {x: alertas_reales.count(x) for x in set(alertas_reales)}

        plt.figure(figsize=(8, 5))
        plt.bar(list(conteos.keys()), list(conteos.values()), color="salmon")
        plt.title("Frecuencia de Alertas Detectadas")
        plt.ylabel("Número de ocurrencias")
        plt.xticks(rotation=20, ha='right')
        plt.tight_layout()
        print("📊 Gráfica de incidencias generada correctamente.")
        plt.show()  # Esta ventana se abrirá en tu ordenador

    def generar_grafica_tendencia(self, datos: pd.DataFrame):
        if datos is None or datos.empty:
            print("⚠️ No hay datos para graficar.")
            return

        cols_voltaje = [c for c in datos.columns if 'voltage' in c.lower()]
        col_tiempo = 'timestamp' if 'timestamp' in datos.columns else 'tiempo'

        if not cols_voltaje:
            print(f"⚠️ Columnas de voltaje no encontradas.")
            return

        plt.figure(figsize=(12, 6))

        # --- SOLUCIÓN AL PROBLEMA DEL "SOLO UN DÍA" ---
        # Si hay muchos datos, tomamos una muestra repartida (1 punto cada 100)
        # en lugar de solo los 1000 primeros.
        if len(datos) > 2000:
            muestra = datos.iloc[::100, :]  # Salta de 100 en 100 para cubrir el mes
        else:
            muestra = datos

        for col in cols_voltaje:
            plt.plot(muestra[col_tiempo], muestra[col], label=col, alpha=0.8, linewidth=1)

        plt.title("Histórico de Voltaje (Vista de todo el periodo)")
        plt.xlabel("Tiempo")
        plt.ylabel("Nivel (mV)")

        # Mostramos solo unas pocas etiquetas en el eje X para que no se amontonen
        paso = max(1, len(muestra) // 10)
        plt.xticks(muestra[col_tiempo][::paso], rotation=45)

        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()

        print(f"📈 Gráfica de tendencia generada cubriendo todo el rango de datos.")
        plt.show()