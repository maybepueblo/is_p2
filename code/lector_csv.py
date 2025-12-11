import os.path

import pandas as pd
import numpy as np


class LectorCSV:
    def __init__(self, ruta_archivo: str = ""):
        self.ruta_archivo = ruta_archivo

    def leer(self) -> pd.DataFrame:
        if self.ruta_archivo and os.path.exists(self.ruta_archivo):
            try:
                print(f"Leyendo archivo real: {self.ruta_archivo}")
                datos = pd.read_csv(self.ruta_archivo)
                if 'tiempo' in datos.columns:
                    datos['tiempo'] = pd.to_datetime(datos['tiempo'])
                return datos
            except Exception as e:
                print(f"Error al leer el CSV: {e}. Pasando a modo simulación")

        print("⚠️ Archivo no encontrado, generando datos simulados...")
        datos = pd.DataFrame(
            {
                "voltaje": np.random.uniform(0, 1, 10),
                "tiempo": pd.date_range(start="1/1/2025", periods=10),
                "frecuencia": np.random.uniform(50, 60, 10),
            }
        )
        return datos