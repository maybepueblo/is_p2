import pandas as pd
from io import StringIO


class LectorCSV:
    def leer(self, ruta_archivo: str) -> pd.DataFrame:
        """
        Transforma el CSV crudo (filas mixtas) en un DataFrame estructurado.
        Responsabilidad: IO y Limpieza de datos (No validación de reglas).
        """
        try:
            # 1. Cargar datos brutos
            # sep=';' según tu ejemplo de datos
            df = pd.read_csv(ruta_archivo, sep=';')

            # 2. Conversión de Tipos Básica
            # Convertir fecha a objeto datetime real
            df['tiempo'] = pd.to_datetime(df['tiempo'], dayfirst=True)

            # 3. Pivotar (Transformación Estructural)
            # Pasamos de tener medidas en filas a tener columnas:
            # [timestamp, voltageReceiver1, voltageReceiver2, status]
            df_pivot = df.pivot_table(
                index='tiempo',
                columns='medida',
                values='valor',
                aggfunc='mean'  # Por si hay duplicados en el mismo milisegundo
            ).reset_index()

            # Limpieza de nombres de columnas
            df_pivot.columns.name = None
            df_pivot = df_pivot.rename(columns={'tiempo': 'timestamp'})

            # 4. Normalización de Unidades (Estandarización)
            # Convertir mV a V para que el sistema trabaje en Voltios
            cols_voltaje = ['voltageReceiver1', 'voltageReceiver2']
            for col in cols_voltaje:
                if col in df_pivot.columns:
                    df_pivot[col] = df_pivot[col] / 1000.0

            # Ordenar cronológicamente es vital para las diferencias de tiempo
            return df_pivot.sort_values('timestamp')

        except Exception as e:
            print(f"Error leyendo el archivo CSV: {e}")
            return pd.DataFrame()  # Retorno vacío en caso de fallo