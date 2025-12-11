import pandas as pd
import numpy as np
import xgboost as xgb
import os
from typing import List, Dict, Optional


class ModuloInteligente:
    def __init__(self):
        # Reglas de Negocio (RF2.1 del PDF)
        self.UMBRAL_VOLTAJE = 0.5
        self.LIMITE_TIEMPO_SEC = 120

        # Modelo IA
        self.model = xgb.XGBClassifier(
            objective='multi:softmax',
            num_class=3,
            eval_metric='mlogloss',
            use_label_encoder=False
        )
        self.is_trained = False

        # --- MEMORIA PARA INFERENCIA (VENTANA DE TAMAÑO 1) ---
        self.ultimo_estado: Optional[Dict] = None

    def _calcular_features_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula features para un bloque de datos (Entrenamiento)."""
        df_proc = df.copy()
        df_proc['delta_t'] = df_proc['timestamp'].diff().dt.total_seconds().fillna(0)
        v1_diff = df_proc['voltageReceiver1'].diff().abs().fillna(0)
        v2_diff = df_proc['voltageReceiver2'].diff().abs().fillna(0)
        df_proc['max_v_jump'] = pd.concat([v1_diff, v2_diff], axis=1).max(axis=1)
        return df_proc

    def entrenar(self, datos_historicos: pd.DataFrame):
        """
        Entrena respetando el tiempo e inyectando datos sintéticos si faltan clases.
        """
        print(f"   [Train] Procesando histórico de {len(datos_historicos)} registros...")

        # 1. Calcular features
        df = self._calcular_features_batch(datos_historicos)

        # 2. Etiquetar (0: Normal, 1: Bloqueo, 2: Salto)
        y = np.zeros(len(df))
        y[df['delta_t'] > self.LIMITE_TIEMPO_SEC] = 1
        mask_salto = (df['max_v_jump'] >= self.UMBRAL_VOLTAJE) & (y == 0)
        y[mask_salto] = 2

        features = ['voltageReceiver1', 'voltageReceiver2', 'status', 'delta_t', 'max_v_jump']
        X = df[features].fillna(0)

        # 3. INYECCIÓN SINTÉTICA (Corrección del typo aquí)
        clases_presentes = np.unique(y)  # Variable definida en español

        # Inyección Bloqueo (Clase 1)
        if 1 not in clases_presentes:  # Uso correcto: 'clases_presentes'
            print("   [Info] Inyectando caso sintético de BLOQUEO (Clase 1)")
            row_bloqueo = pd.DataFrame([{
                'voltageReceiver1': 1.5, 'voltageReceiver2': 1.5, 'status': 1,
                'delta_t': 300.0,
                'max_v_jump': 0.0
            }])
            X = pd.concat([X, row_bloqueo], ignore_index=True)
            y = np.append(y, 1)

        # Inyección Salto (Clase 2)
        if 2 not in clases_presentes:  # Uso correcto: 'clases_presentes'
            print("   [Info] Inyectando caso sintético de SALTO (Clase 2)")
            row_salto = pd.DataFrame([{
                'voltageReceiver1': 2.5, 'voltageReceiver2': 1.5, 'status': 1,
                'delta_t': 60.0,
                'max_v_jump': 1.0
            }])
            X = pd.concat([X, row_salto], ignore_index=True)
            y = np.append(y, 2)

        # 4. Entrenar
        self.model.fit(X, y)
        self.is_trained = True
        print("   [Train] Modelo entrenado y listo.")

    def predecir_tiempo_real(self, lectura_actual: Dict) -> List[Dict]:
        """Inferencia dato a dato con memoria (Stateful)."""
        ts_actual = pd.to_datetime(lectura_actual['timestamp'], dayfirst=True)
        # Normalizar a Voltios (asumiendo que entra en mV desde el sensor simulado)
        v1 = float(lectura_actual['voltageReceiver1']) / 1000.0
        v2 = float(lectura_actual['voltageReceiver2']) / 1000.0
        status = lectura_actual['status']

        # 1. Calcular deltas usando la MEMORIA
        delta_t = 0.0
        max_jump = 0.0

        if self.ultimo_estado is not None:
            ts_prev = self.ultimo_estado['ts']
            delta_t = (ts_actual - ts_prev).total_seconds()

            jump_v1 = abs(v1 - self.ultimo_estado['v1'])
            jump_v2 = abs(v2 - self.ultimo_estado['v2'])
            max_jump = max(jump_v1, jump_v2)

        # 2. Actualizar memoria
        self.ultimo_estado = {
            'ts': ts_actual,
            'v1': v1,
            'v2': v2
        }

        # 3. Preparar dato para modelo
        input_data = pd.DataFrame([{
            'voltageReceiver1': v1,
            'voltageReceiver2': v2,
            'status': status,
            'delta_t': delta_t,
            'max_v_jump': max_jump
        }])

        # 4. Predicción Híbrida
        incidencias = []

        # Reglas Deterministas
        if delta_t > self.LIMITE_TIEMPO_SEC:
            incidencias.append({"tipo": "BLOQUEO_DATOS", "valor": f"{delta_t}s", "timestamp": ts_actual})

        if max_jump >= self.UMBRAL_VOLTAJE:
            incidencias.append({"tipo": "SALTO_VOLTAJE", "valor": f"{max_jump:.2f}V", "timestamp": ts_actual})

        # Predicción IA
        if self.is_trained:
            pred_class = self.model.predict(input_data)[0]
            # Si la IA ve algo sutil que la regla estricta no (redundancia)
            if pred_class == 1 and delta_t <= self.LIMITE_TIEMPO_SEC:
                incidencias.append({"tipo": "POSIBLE_BLOQUEO (IA)", "valor": "Predicción", "timestamp": ts_actual})
            if pred_class == 2 and max_jump < self.UMBRAL_VOLTAJE:
                incidencias.append({"tipo": "POSIBLE_SALTO (IA)", "valor": "Predicción", "timestamp": ts_actual})

        return incidencias