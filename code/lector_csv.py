import pandas as pd
import numpy as np


class LectorCSV:
    def leer(self, ruta_archivo: str) -> pd.DataFrame:
        df = pd.read_csv(ruta_archivo, sep=';')

        df['timestamp'] = pd.to_datetime(df['tiempo'], dayfirst=True)

        df['secuencia_evento'] = df.groupby(['timestamp', 'medida']).cumcount()

        df_pivot = df.pivot_table(
            index=['timestamp', 'secuencia_evento'],
            columns='medida',
            values='valor',
            aggfunc='first'
        ).reset_index()

        df_pivot.columns.name = None

        # ❗ NO forward fill
        df_pivot = df_pivot.fillna(np.nan)

        # Normalización mV → V
        for col in ['voltageReceiver1', 'voltageReceiver2']:
            if col in df_pivot.columns:
                df_pivot[col] = df_pivot[col] / 1000.0

        df_final = df_pivot.sort_values(
            by=['timestamp', 'secuencia_evento']
        ).reset_index(drop=True)

        df_final = df_final.drop(columns=['secuencia_evento'])

        return df_final
