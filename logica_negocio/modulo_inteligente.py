import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os
from typing import List, Dict


class ModuloInteligente:
    def __init__(self):
        # =====================
        # CONFIGURACIÓN GENERAL
        # =====================
        self.UMBRAL_VOLTAJE = 0.5  # V
        self.LIMITE_TIEMPO_SEC = 120  # s
        self.HORIZONTE_PREDICCION_SEC = 120  # s

        self.WINDOW_SIZE = 10

        self.MODEL_DIR = "model"
        self.MODEL_FILENAME = "modelo_ferroviario_predictivo.pkl"

        # =====================
        # MODELO ML
        # =====================
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            random_state=42,
        )

        self.features_entrenamiento = []
        self.is_trained = False

        # Buffer para tiempo real (solo usado en streaming individual)
        self.buffer_lecturas = []

    # ==========================================================
    # INGENIERÍA DE FEATURES (SOLO PASADO)
    # ==========================================================
    def _generar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ingeniería de características optimizada.
        Incluye 'diff' para precisión y 'delta_t_rolling' para evitar errores.
        """
        df = df.copy()

        # 1. Delta Tiempo (Fundamental para Bloqueos)
        df["delta_t"] = df["timestamp"].diff().dt.total_seconds().fillna(0)

        for col in ["voltageReceiver1", "voltageReceiver2"]:
            df[col] = df[col].astype(float)

            # --- MEJORA CLAVE 1: Diferencia instantánea ---
            df[f"{col}_diff"] = df[col].diff().fillna(0)

            # Estadísticas de Ventana
            df[f"{col}_mean"] = df[col].rolling(self.WINDOW_SIZE).mean().fillna(0)
            df[f"{col}_std"] = df[col].rolling(self.WINDOW_SIZE).std().fillna(0)

            # --- MEJORA CLAVE 2: Desviación (Sustituye a trend) ---
            df[f"{col}_dev"] = abs(df[col] - df[f"{col}_mean"])

        # --- MEJORA CLAVE 3: Corrección del Crash ---
        # Necesario porque la inyección de datos sintéticos usa esta columna
        df["delta_t_rolling"] = df["delta_t"].rolling(self.WINDOW_SIZE).mean().fillna(0)

        return df.fillna(0)

    # ==========================================================
    # ETIQUETADO AUTOMÁTICO A FUTURO
    # ==========================================================
    def _etiquetar_automaticamente(self, df: pd.DataFrame) -> np.ndarray:
        """
        Estrategia Híbrida:
        - Bloqueos: Se etiquetan en el momento que ocurren (Reactivo).
        - Saltos: Se etiquetan mirando al futuro (Predictivo).
        """
        y = np.zeros(len(df), dtype=int)

        timestamps = df["timestamp"].values
        v1 = df["voltageReceiver1"].values
        v2 = df["voltageReceiver2"].values

        for i in range(len(df)):
            t0 = timestamps[i]

            # 1. LÓGICA REACTIVA PARA BLOQUEOS
            gap_actual = 0
            if i > 0:
                gap_actual = (
                    (timestamps[i] - timestamps[i - 1])
                    .astype("timedelta64[s]")
                    .item()
                    .seconds
                )

            if gap_actual > self.LIMITE_TIEMPO_SEC:
                y[i] = 1
                continue

            # 2. LÓGICA PREDICTIVA PARA SALTOS
            j = i + 1
            while j < len(df):
                delta_futuro = (
                    (timestamps[j] - t0).astype("timedelta64[s]").item().seconds
                )

                if delta_futuro > self.HORIZONTE_PREDICCION_SEC:
                    break

                if j > 0:
                    salto_v1 = abs(v1[j] - v1[j - 1])
                    salto_v2 = abs(v2[j] - v2[j - 1])

                    if (
                            salto_v1 >= self.UMBRAL_VOLTAJE
                            or salto_v2 >= self.UMBRAL_VOLTAJE
                    ):
                        y[i] = 2
                        break

                j += 1
        return y

    # ==========================================================
    # ENTRENAMIENTO
    # ==========================================================
    def entrenar(self, datos_historicos: pd.DataFrame):
        print(
            f"   [ML] Procesando {len(datos_historicos)} registros para entrenamiento..."
        )

        X = self._generar_features(datos_historicos)
        y = self._etiquetar_automaticamente(X)

        cols_drop = ["timestamp", "medida", "id", "canal", "valor", "status"]
        features_validas = [
            c for c in X.columns if c not in cols_drop and "tiempo" not in c
        ]
        self.features_entrenamiento = features_validas
        X_final = X[features_validas].copy()

        # Inyección Sintética Bloqueos
        clases_presentes = np.unique(y)
        conteo_bloqueos = np.count_nonzero(y == 1)

        if conteo_bloqueos < 500:
            CANTIDAD_A_INYECTAR = 2000
            print(
                f"   [ML] ⚠️ Pocos Bloqueos reales ({conteo_bloqueos}). Inyectando {CANTIDAD_A_INYECTAR} muestras sintéticas..."
            )
            indices_base = np.random.choice(
                X_final.index, CANTIDAD_A_INYECTAR, replace=True
            )
            df_sintetico = X_final.loc[indices_base].copy()

            tiempos_bloqueo = np.random.uniform(
                self.LIMITE_TIEMPO_SEC + 5, 1000, CANTIDAD_A_INYECTAR
            )
            df_sintetico["delta_t"] = tiempos_bloqueo
            df_sintetico["delta_t_rolling"] = tiempos_bloqueo

            X_final = pd.concat([X_final, df_sintetico], ignore_index=True)
            y = np.append(y, [1] * CANTIDAD_A_INYECTAR)

        unique, counts = np.unique(y, return_counts=True)
        print(
            f"   [ML] Distribución de clases para entrenamiento: {dict(zip(unique, counts))}"
        )

        self.model.fit(X_final, y)
        self.is_trained = True
        print("   [ML] Cerebro entrenado y listo para detectar bloqueos.")

    # ==========================================================
    # GUARDAR / CARGAR MODELO
    # ==========================================================
    def guardar_modelo(self):
        if not os.path.exists(self.MODEL_DIR):
            os.makedirs(self.MODEL_DIR)

        path = os.path.join(self.MODEL_DIR, self.MODEL_FILENAME)

        joblib.dump(
            {
                "model": self.model,
                "features": self.features_entrenamiento,
                "trained": self.is_trained,
            },
            path,
        )
        print(f"[ML] Modelo guardado en {path}")

    def cargar_modelo(self) -> bool:
        # Asegúrate de que la ruta sea absoluta respecto a este archivo para evitar errores
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Intentamos ruta relativa hacia arriba (estructura producción)
        path = os.path.join(base_dir, "..", self.MODEL_DIR, self.MODEL_FILENAME)

        # Fallback por si ejecutas desde raíz
        if not os.path.exists(path):
            path = os.path.join(self.MODEL_DIR, self.MODEL_FILENAME)

        if os.path.exists(path):
            try:
                d = joblib.load(path)
                self.model = d['model']
                self.features_entrenamiento = d['features']
                self.is_trained = True
                print(f"[ML] Modelo cargado desde: {path}")
                return True
            except Exception as e:
                print(f"[ML] Error cargando modelo: {e}")
                return False

        return False

    # ==========================================================
    # 🚀 ANÁLISIS EN BATCH (MÉTODO RÁPIDO)
    # ==========================================================
    def analizar_todo(self, df: pd.DataFrame) -> List[str]:
        """
        Realiza inferencia vectorial sobre todo el DataFrame a la vez.
        Velocidad: ~0.1s para 100k registros.
        """
        if not self.is_trained:
            return ["⚠️ Error: Modelo no cargado."]

        # 1. Feature Engineering Masivo (Vectorizado)
        # Pandas calcula todas las columnas de golpe, mucho más rápido que filas sueltas
        df_features = self._generar_features(df)

        # 2. Seleccionar solo las columnas que el modelo aprendió
        try:
            X_batch = df_features[self.features_entrenamiento]
        except KeyError as e:
            return [f"⚠️ Error columnas: {e}. Revisa si cambiaste las features sin re-entrenar."]

        # 3. Predicción Masiva (La magia de C/C++ bajo XGBoost)
        # Le pasamos 100.000 filas de golpe y nos devuelve 100.000 números
        preds = self.model.predict(X_batch)

        # 4. Decodificación Rápida (Usando índices de Numpy)
        alertas = []
        timestamps = df['timestamp'].values  # Acceso rápido a fechas

        # Buscamos dónde hay 1s (Bloqueos) y 2s (Saltos)
        idx_bloqueos = np.where(preds == 1)[0]
        idx_saltos = np.where(preds == 2)[0]

        # Formateamos solo las alertas encontradas
        for i in idx_bloqueos:
            ts = pd.to_datetime(timestamps[i])
            alertas.append(f"🔴 BLOQUEO DETECTADO en {ts}")

        for i in idx_saltos:
            ts = pd.to_datetime(timestamps[i])
            alertas.append(f"⚠️ PREDICCIÓN SALTO (Horizonte 120s) en {ts}")

        # Devolvemos la lista completa (sistema_transporte decidirá cuántas mostrar)
        return alertas

    # Mantenemos este por compatibilidad si algo lo llama, pero no se usa en batch
    def predecir_tiempo_real(self, lectura: Dict) -> List[str]:
        if not self.is_trained: return []
        # ... (implementación antigua, irrelevante para modo rápido) ...
        return []