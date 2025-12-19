import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os
from typing import List, Dict


class ModuloInteligente:
    def __init__(self):
        self.UMBRAL_VOLTAJE = 0.5
        self.LIMITE_TIEMPO_SEC = 120
        self.HORIZONTE_PREDICCION_SEC = 120
        self.WINDOW_SIZE = 10
        self.MODEL_DIR = "model"
        self.MODEL_FILENAME = "modelo_ferroviario_predictivo.pkl"

        self.model = None
        self.features_entrenamiento = []
        self.is_trained = False
        self.buffer_lecturas = []

    def _generar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["delta_t"] = df["timestamp"].diff().dt.total_seconds().fillna(0)
        for col in ["voltageReceiver1", "voltageReceiver2"]:
            df[col] = df[col].astype(float)
            df[f"{col}_diff"] = df[col].diff().fillna(0)
            df[f"{col}_mean"] = df[col].rolling(self.WINDOW_SIZE).mean().fillna(0)
            df[f"{col}_std"] = df[col].rolling(self.WINDOW_SIZE).std().fillna(0)
            df[f"{col}_dev"] = abs(df[col] - df[f"{col}_mean"])
        df["delta_t_rolling"] = df["delta_t"].rolling(self.WINDOW_SIZE).mean().fillna(0)
        return df.fillna(0)

    def _etiquetar_automaticamente(self, df: pd.DataFrame) -> np.ndarray:
        y = np.zeros(len(df), dtype=int)
        timestamps = df["timestamp"].values
        v1 = df["voltageReceiver1"].values
        v2 = df["voltageReceiver2"].values

        for i in range(len(df)):
            t0 = timestamps[i]
            # Reactivo (Bloqueos)
            gap = 0
            if i > 0:
                gap = (timestamps[i] - timestamps[i - 1]).astype("timedelta64[s]").item().seconds
            if gap > self.LIMITE_TIEMPO_SEC:
                y[i] = 1
                continue
            # Predictivo (Saltos)
            j = i + 1
            while j < len(df):
                delta = (timestamps[j] - t0).astype("timedelta64[s]").item().seconds
                if delta > self.HORIZONTE_PREDICCION_SEC: break
                if j > 0:
                    if abs(v1[j] - v1[j - 1]) >= self.UMBRAL_VOLTAJE or abs(v2[j] - v2[j - 1]) >= self.UMBRAL_VOLTAJE:
                        y[i] = 2
                        break
                j += 1
        return y

    def entrenar(self, datos_historicos: pd.DataFrame):
        print(f"   [ML] Procesando {len(datos_historicos)} registros...")
        X = self._generar_features(datos_historicos)
        y = self._etiquetar_automaticamente(X)

        features_validas = [c for c in X.columns if
                            "timestamp" not in c and "medida" not in c and "id" not in c and "canal" not in c and "valor" not in c and "status" not in c]
        self.features_entrenamiento = features_validas
        X_final = X[features_validas].copy()

        # Inyección sintética
        if np.count_nonzero(y == 1) < 500:
            print("   [ML] 💉 Inyectando 2000 bloqueos sintéticos...")
            indices = np.random.choice(X_final.index, 2000, replace=True)
            df_sint = X_final.loc[indices].copy()
            df_sint["delta_t"] = np.random.uniform(130, 1000, 2000)
            df_sint["delta_t_rolling"] = df_sint["delta_t"]
            X_final = pd.concat([X_final, df_sint], ignore_index=True)
            y = np.append(y, [1] * 2000)

        self.model.fit(X_final, y)
        self.is_trained = True
        print("   [ML] Modelo entrenado.")

    def guardar_modelo(self):
        if not os.path.exists(self.MODEL_DIR): os.makedirs(self.MODEL_DIR)
        path = os.path.join(self.MODEL_DIR, self.MODEL_FILENAME)
        joblib.dump({"model": self.model, "features": self.features_entrenamiento, "trained": self.is_trained}, path)
        print(f"[ML] Guardado en {path}")

    def cargar_modelo(self) -> bool:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "..", self.MODEL_DIR, self.MODEL_FILENAME)
        if not os.path.exists(path): path = os.path.join(self.MODEL_DIR, self.MODEL_FILENAME)

        if os.path.exists(path):
            d = joblib.load(path)
            self.model = d['model']
            self.features_entrenamiento = d['features']
            self.is_trained = True
            print(f"[ML] Modelo cargado desde: {path}")
            return True
        return False

    # ==========================================================
    # ⚡ ANÁLISIS EN BATCH (OPTIMIZADO)
    # ==========================================================
    def analizar_todo(self, df: pd.DataFrame) -> List[str]:
        if not self.is_trained: return ["⚠️ Modelo no cargado"]

        # 1. Features Vectorizadas
        df_features = self._generar_features(df)
        X_batch = df_features[self.features_entrenamiento]

        # 2. Predicción Masiva
        preds = self.model.predict(X_batch)

        # 3. GENERACIÓN DE ALERTAS (OPTIMIZADA) 🚀
        # En lugar de un bucle 'for' lento, usamos índices directos
        timestamps = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').values

        idx_bloqueos = np.where(preds == 1)[0]
        idx_saltos = np.where(preds == 2)[0]

        # Creación ultrarrápida de listas
        alertas_bloqueos = [f"🔴 BLOQUEO DETECTADO en {t}" for t in timestamps[idx_bloqueos]]
        alertas_saltos = [f"⚠️ PREDICCIÓN SALTO (Horizonte 120s) en {t}" for t in timestamps[idx_saltos]]

        return alertas_bloqueos + alertas_saltos
