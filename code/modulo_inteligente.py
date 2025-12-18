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

        # Buffer para tiempo real
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
        # ETIQUETADO AUTOMÁTICO A FUTURO (CORREGIDO)
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

            # -----------------------------------------------------------
            # 1. LÓGICA REACTIVA PARA BLOQUEOS (Detectar el silencio AHORA)
            # -----------------------------------------------------------
            # Si el paquete 'i' ha llegado con mucho retraso respecto al 'i-1',
            # es que ACABA de ocurrir un bloqueo. Lo marcamos aquí.
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
                continue  # Si es bloqueo, tiene prioridad máxima. Pasamos al siguiente.

            # -----------------------------------------------------------
            # 2. LÓGICA PREDICTIVA PARA SALTOS (Mirar al FUTURO)
            # -----------------------------------------------------------
            # Si no hay bloqueo ahora, miramos adelante para ver si se avecina un salto.
            j = i + 1
            while j < len(df):
                # ¿Cuánto futuro hemos mirado ya?
                delta_futuro = (
                    (timestamps[j] - t0).astype("timedelta64[s]").item().seconds
                )

                # Si miramos más allá de 2 minutos (horizonte), paramos.
                if delta_futuro > self.HORIZONTE_PREDICCION_SEC:
                    break

                # Comprobamos si en el futuro 'j' ocurre un salto
                # (Diferencia de voltaje brusca entre j y j-1)
                if j > 0:
                    salto_v1 = abs(v1[j] - v1[j - 1])
                    salto_v2 = abs(v2[j] - v2[j - 1])

                    if (
                        salto_v1 >= self.UMBRAL_VOLTAJE
                        or salto_v2 >= self.UMBRAL_VOLTAJE
                    ):
                        # Etiquetamos la fila ACTUAL 'i' como "Precursor de Salto"
                        y[i] = 2
                        break  # Ya sabemos que viene un salto, no necesitamos buscar más

                j += 1

        return y

    # ==========================================================
    # ENTRENAMIENTO
    # ==========================================================
    def entrenar(self, datos_historicos: pd.DataFrame):
        """
        Entrena el modelo forzando el aprendizaje de Bloqueos mediante
        Inyección de Datos Sintéticos (Data Augmentation).
        """
        print(
            f"   [ML] Procesando {len(datos_historicos)} registros para entrenamiento..."
        )

        # 1. Generar Features y Etiquetas iniciales
        X = self._generar_features(datos_historicos)
        y = self._etiquetar_automaticamente(X)

        # 2. Limpieza de columnas (nos quedamos solo con las numéricas para la IA)
        cols_drop = ["timestamp", "medida", "id", "canal", "valor", "status"]
        features_validas = [
            c for c in X.columns if c not in cols_drop and "tiempo" not in c
        ]
        self.features_entrenamiento = features_validas
        X_final = X[features_validas].copy()

        # -------------------------------------------------------------------------
        # ESTRATEGIA DE SEGURIDAD: INYECCIÓN SINTÉTICA DE BLOQUEOS
        # -------------------------------------------------------------------------
        clases_presentes = np.unique(y)

        # Si hay pocos o ningun bloqueo, el modelo no aprenderá.
        # Forzamos la inyección SIEMPRE que haya menos de 500 ejemplos reales.
        conteo_bloqueos = np.count_nonzero(y == 1)

        if conteo_bloqueos < 500:
            CANTIDAD_A_INYECTAR = 2000
            print(
                f"   [ML] ⚠️ Pocos Bloqueos reales ({conteo_bloqueos}). Inyectando {CANTIDAD_A_INYECTAR} muestras sintéticas..."
            )

            # A. Clonamos datos normales aleatorios para tener "base realista" (voltajes, ruido...)
            indices_base = np.random.choice(
                X_final.index, CANTIDAD_A_INYECTAR, replace=True
            )
            df_sintetico = X_final.loc[indices_base].copy()

            # B. "Corrompemos" la columna del tiempo (delta_t)
            # Generamos tiempos aleatorios entre 125s (bloqueo leve) y 1000s (bloqueo grave)
            tiempos_bloqueo = np.random.uniform(
                self.LIMITE_TIEMPO_SEC + 5, 1000, CANTIDAD_A_INYECTAR
            )

            df_sintetico["delta_t"] = tiempos_bloqueo
            df_sintetico["delta_t_rolling"] = tiempos_bloqueo

            # C. Añadimos al set de entrenamiento
            X_final = pd.concat([X_final, df_sintetico], ignore_index=True)
            y = np.append(y, [1] * CANTIDAD_A_INYECTAR)  # Etiqueta 1 = Bloqueo

        # -------------------------------------------------------------------------

        # Verificación de distribución antes de entrenar
        unique, counts = np.unique(y, return_counts=True)
        print(
            f"   [ML] Distribución de clases para entrenamiento: {dict(zip(unique, counts))}"
        )

        # 3. Entrenamiento del Modelo
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
        path = os.path.join(self.MODEL_DIR, self.MODEL_FILENAME)

        if not os.path.exists(path):
            return False

        data = joblib.load(path)
        self.model = data["model"]
        self.features_entrenamiento = data["features"]
        self.is_trained = data["trained"]

        print("[ML] Modelo cargado.")
        return True

    # ==========================================================
    # PREDICCIÓN EN TIEMPO REAL (ANTICIPACIÓN)
    # ==========================================================
    def predecir_tiempo_real(self, lectura: Dict) -> List[str]:
        if not self.is_trained:
            return []

        ts = pd.to_datetime(lectura["timestamp"], dayfirst=True)

        v1 = float(lectura["voltageReceiver1"])
        v2 = float(lectura["voltageReceiver2"])

        # Normalización mV → V si hace falta
        if v1 > 50:
            v1 /= 1000
        if v2 > 50:
            v2 /= 1000

        self.buffer_lecturas.append(
            {"timestamp": ts, "voltageReceiver1": v1, "voltageReceiver2": v2}
        )

        if len(self.buffer_lecturas) > self.WINDOW_SIZE + 1:
            self.buffer_lecturas.pop(0)

        if len(self.buffer_lecturas) < self.WINDOW_SIZE:
            return []

        df = pd.DataFrame(self.buffer_lecturas)
        feats = self._generar_features(df)

        X_curr = feats.iloc[[-1]][self.features_entrenamiento]

        probs = self.model.predict_proba(X_curr)[0]
        pred = np.argmax(probs)

        if pred == 1:
            return [
                f"⚠️ Posible BLOQUEO en los próximos {self.HORIZONTE_PREDICCION_SEC}s"
            ]
        if pred == 2:
            return [f"⚠️ Posible SALTO en los próximos {self.HORIZONTE_PREDICCION_SEC}s"]

        return []

    # ==========================================================
    # ANÁLISIS OFFLINE COMPLETO
    # ==========================================================
    def analizar_todo(self, df: pd.DataFrame) -> List[str]:
        self.buffer_lecturas = []
        alertas = []

        for _, row in df.iterrows():
            lectura = {
                "timestamp": row["timestamp"],
                "voltageReceiver1": row["voltageReceiver1"] * 1000,
                "voltageReceiver2": row["voltageReceiver2"] * 1000,
            }

            alertas.extend(self.predecir_tiempo_real(lectura))

        return list(set(alertas))
