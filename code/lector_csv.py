import pandas as pd
import numpy as np


class LectorCSV:
    def __init__(self, ruta_archivo: str = ""):
        self.ruta_archivo = ruta_archivo

    def leer(self) -> pd.DataFrame:
        try:
            print(f"Leyendo archivo CSV desde: {self.ruta_archivo}...")
            # Simulación de datos para que funcione sin archivo físico
            datos = pd.DataFrame(
                {
                    "voltaje": np.random.uniform(0, 1, 10),
                    "tiempo": pd.date_range(start="1/1/2025", periods=10),
                    "frecuencia": np.random.uniform(50, 60, 10),
                }
            )
            return datos
        except Exception as e:
            print(f"Error al leer CSV: {e}")
            return pd.DataFrame()
