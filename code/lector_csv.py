import pandas as pd
import numpy as np


class LectorCSV:
    def leer(self, ruta_archivo: str) -> pd.DataFrame:
        """
        Lee el CSV y lo transforma en una secuencia cronológica de eventos,
        respetando el orden de llegada (canal 'a', luego 'b', etc.)
        sin mezclarlos ni promediarlos.
        """
        try:
            # 1. Cargar datos
            # Ajustamos sep=';' según tu formato
            df = pd.read_csv(ruta_archivo, sep=';')

            # 2. Conversión de Fecha
            df['timestamp'] = pd.to_datetime(df['tiempo'], dayfirst=True)

            # 3. GENERACIÓN DE SECUENCIA (LA CLAVE)
            # El archivo tiene un patrón repetitivo: status -> v1 -> v2.
            # Al agrupar por minuto y tipo de medida, contamos "este es el 1º status del minuto",
            # "este es el 2º status del minuto", etc.
            # Esto alinea automáticamente el 1º status con el 1º v1 (canal a)
            # y el 2º status con el 2º v1 (canal b).
            df['secuencia_evento'] = df.groupby(['timestamp', 'medida']).cumcount()

            # 4. Pivotar (Transformar filas en columnas)
            # Usamos (timestamp + secuencia) como índice único.
            df_pivot = df.pivot_table(
                index=['timestamp', 'secuencia_evento'],
                columns='medida',
                values='valor',
                aggfunc='first'  # Tomamos el valor exacto, sin promediar
            ).reset_index()

            # 5. Limpieza
            df_pivot.columns.name = None

            # Rellenar huecos si algún paquete vino incompleto (Forward Fill)
            df_pivot = df_pivot.ffill().fillna(0)

            # 6. Normalización de Unidades (mV -> V)
            # El sistema trabaja en Voltios. Tu CSV tiene valores como 1776 (mV).
            cols_voltaje = ['voltageReceiver1', 'voltageReceiver2']
            for col in cols_voltaje:
                if col in df_pivot.columns:
                    df_pivot[col] = df_pivot[col] / 1000.0

            # 7. Ordenar por tiempo y secuencia
            # Esto garantiza que el modelo vea: Fila A -> Fila B -> Fila A...
            df_final = df_pivot.sort_values(by=['timestamp', 'secuencia_evento'])

            # Eliminamos la columna auxiliar, ya no sirve para el ML
            df_final = df_final.drop(columns=['secuencia_evento'])

            return df_final

        except Exception as e:
            print(f"❌ Error crítico leyendo el CSV: {e}")
            return pd.DataFrame()