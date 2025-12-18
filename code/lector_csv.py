import pandas as pd

class LectorCSV:
    def leer(self, ruta_archivo: str) -> pd.DataFrame:
        """
        Lee el CSV y lo transforma en una secuencia cronológica de eventos,
        respetando el orden de llegada (canal 'a', luego 'b', etc.)
        sin mezclarlos ni promediarlos.
        """
        try:
            # 1. Cargar datos
            df = pd.read_csv(ruta_archivo, sep=';')

            # 2. Conversión de Fecha
            df['timestamp'] = pd.to_datetime(df['tiempo'], dayfirst=True)

            # 3. GENERACIÓN DE SECUENCIA
            df['secuencia_evento'] = df.groupby(['timestamp', 'medida']).cumcount()

            # 4. Pivotar (Transformar filas en columnas)
            # Usamos (timestamp + secuencia) como índice único.
            df_pivot = df.pivot_table(
                index=['timestamp', 'secuencia_evento'],
                columns='medida',
                values='valor',
                aggfunc='first'
            ).reset_index()

            # 5. Limpieza
            df_pivot.columns.name = None

            # Rellenar huecos si algún paquete vino incompleto (Forward Fill)
            df_pivot = df_pivot.ffill().fillna(0)

            # 6. Normalización de Unidades (mV -> V)
            cols_voltaje = ['voltageReceiver1', 'voltageReceiver2']
            for col in cols_voltaje:
                if col in df_pivot.columns:
                    df_pivot[col] = df_pivot[col] / 1000.0

            # 7. Ordenar por tiempo y secuencia
            df_final = df_pivot.sort_values(by=['timestamp', 'secuencia_evento'])

            # Eliminamos la columna auxiliar, ya no sirve para el ML
            df_final = df_final.drop(columns=['secuencia_evento'])

            return df_final

        except Exception as e:
            print(f"❌ Error crítico leyendo el CSV: {e}")
            return pd.DataFrame()