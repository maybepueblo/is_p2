import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os
from typing import List, Dict


class ModuloInteligente:
    def __init__(self):
        # Configuración de Reglas
        self.UMBRAL_VOLTAJE = 0.5
        self.LIMITE_TIEMPO_SEC = 120

        # Configuración de Rutas y Modelo
        self.MODEL_DIR = "model"
        self.MODEL_FILENAME = "modelo_ferroviario.pkl"

        # Modelo IA (XGBoost)
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=9,
            objective='multi:softmax',
            num_class=3,
            eval_metric='mlogloss',
            use_label_encoder=False,
            random_state=42
        )
        self.is_trained = False

        # Memoria de Inferencia
        self.WINDOW_SIZE = 3
        self.buffer_lecturas = []
        self.features_entrenamiento = []

    def _generar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ingeniería de características (Rolling Windows)."""
        df_feat = df.copy()
        df_feat['delta_t'] = df_feat['timestamp'].diff().dt.total_seconds().fillna(0)

        cols_v = ['voltageReceiver1', 'voltageReceiver2']
        for col in cols_v:
            df_feat[col] = df_feat[col].astype(float)
            df_feat[f'{col}_mean'] = df_feat[col].rolling(window=self.WINDOW_SIZE).mean().fillna(0)
            df_feat[f'{col}_std'] = df_feat[col].rolling(window=self.WINDOW_SIZE).std().fillna(0)
            df_feat[f'{col}_dev'] = abs(df_feat[col] - df_feat[f'{col}_mean'])

        df_feat['delta_t_rolling'] = df_feat['delta_t'].rolling(window=self.WINDOW_SIZE).mean().fillna(0)
        return df_feat.fillna(0)

    def _etiquetar_automaticamente(self, df_features: pd.DataFrame) -> np.ndarray:
        """Generación de Ground Truth basado en reglas físicas."""
        y = np.zeros(len(df_features))
        # Regla 1: Bloqueo (> 120s)
        y[df_features['delta_t'] > self.LIMITE_TIEMPO_SEC] = 1
        # Regla 2: Salto (Diferencia de voltaje > 0.5V)
        v1_diff = df_features['voltageReceiver1'].diff().abs().fillna(0)
        v2_diff = df_features['voltageReceiver2'].diff().abs().fillna(0)
        max_jump = pd.concat([v1_diff, v2_diff], axis=1).max(axis=1)

        mask_salto = (max_jump >= self.UMBRAL_VOLTAJE) & (y == 0)
        y[mask_salto] = 2
        return y

    def entrenar(self, datos_historicos: pd.DataFrame):
        """Entrena el modelo aplicando Data Augmentation si es necesario."""
        print(f"   [ML] Procesando {len(datos_historicos)} registros para entrenamiento...")

        X = self._generar_features(datos_historicos)
        y = self._etiquetar_automaticamente(X)

        # Limpieza de columnas no utilizables para predicción
        cols_drop = ['timestamp', 'medida', 'id', 'canal', 'valor', 'status']
        features_validas = [c for c in X.columns if c not in cols_drop and 'tiempo' not in c]
        self.features_entrenamiento = features_validas
        X_final = X[features_validas].copy()

        # --- ESTRATEGIA AGRESIVA: OVERSAMPLING DE BLOQUEOS ---
        clases_presentes = np.unique(y)
        if 1 not in clases_presentes:
            CANTIDAD_SINTETICA = 1000
            print(f"   [ML] ⚠️ Clase 1 (Bloqueo) ausente. Inyectando {CANTIDAD_SINTETICA} muestras sintéticas...")

            # Clonación y corrupción
            indices_random = np.random.choice(X_final.index, CANTIDAD_SINTETICA, replace=True)
            df_sintetico = X_final.loc[indices_random].copy()

            # Generar tiempos de bloqueo aleatorios (121s - 600s)
            nuevos_tiempos = np.random.uniform(self.LIMITE_TIEMPO_SEC + 1, 600, CANTIDAD_SINTETICA)
            df_sintetico['delta_t'] = nuevos_tiempos
            df_sintetico['delta_t_rolling'] = nuevos_tiempos

            X_final = pd.concat([X_final, df_sintetico], ignore_index=True)
            y = np.append(y, [1] * CANTIDAD_SINTETICA)

        # Inyección de Saltos si faltaran
        if 2 not in clases_presentes:
            print("   [ML] ⚠️ Clase 2 (Salto) ausente. Inyectando muestra sintética...")
            row_sintetica = pd.DataFrame(0, index=[0], columns=features_validas)
            row_sintetica['voltageReceiver1_dev'] = 2.0
            X_final = pd.concat([X_final, row_sintetica], ignore_index=True)
            y = np.append(y, 2)

        # Entrenamiento
        self.model.fit(X_final, y)
        self.is_trained = True
        print("   [ML] Modelo XGBoost entrenado exitosamente.")

    # --- PERSISTENCIA GESTIONADA INTERNAMENTE ---
    def guardar_modelo(self):
        """Guarda el modelo en la carpeta 'model/' definida en la clase."""
        if not self.is_trained:
            print("   [IO] Error: No se puede guardar un modelo no entrenado.")
            return

        # Crear carpeta si no existe
        if not os.path.exists(self.MODEL_DIR):
            os.makedirs(self.MODEL_DIR)
            print(f"   [IO] Carpeta '{self.MODEL_DIR}/' creada.")

        ruta_completa = os.path.join(self.MODEL_DIR, self.MODEL_FILENAME)

        datos = {
            'modelo': self.model,
            'features': self.features_entrenamiento,
            'is_trained': self.is_trained
        }
        joblib.dump(datos, ruta_completa)
        print(f"   [IO] Cerebro guardado en: {ruta_completa}")

    def cargar_modelo(self) -> bool:
        """Carga el modelo desde la carpeta 'model/'."""
        ruta_completa = os.path.join(self.MODEL_DIR, self.MODEL_FILENAME)

        if os.path.exists(ruta_completa):
            try:
                datos = joblib.load(ruta_completa)
                self.model = datos['modelo']
                self.features_entrenamiento = datos['features']
                self.is_trained = datos['is_trained']
                print(f"   [IO] Cerebro cargado desde: {ruta_completa}")
                return True
            except Exception as e:
                print(f"   [IO] Error cargando el archivo: {e}")
                return False
        else:
            print(f"   [IO] Archivo no encontrado: {ruta_completa}")
            return False

    def predecir_tiempo_real(self, lectura_actual: Dict) -> List[str]:
        """Inferencia dato a dato."""
        if not self.is_trained: return []

        ts = pd.to_datetime(lectura_actual['timestamp'], dayfirst=True)

        # Normalización de unidades si entra en mV
        v1 = float(lectura_actual['voltageReceiver1'])
        v2 = float(lectura_actual['voltageReceiver2'])
        if v1 > 50: v1 /= 1000.0
        if v2 > 50: v2 /= 1000.0

        dato_limpio = {'timestamp': ts, 'voltageReceiver1': v1, 'voltageReceiver2': v2, 'status': 1}
        self.buffer_lecturas.append(dato_limpio)

        if len(self.buffer_lecturas) > self.WINDOW_SIZE + 1: self.buffer_lecturas.pop(0)
        if len(self.buffer_lecturas) < 2: return []

        df_buffer = pd.DataFrame(self.buffer_lecturas)
        df_features = self._generar_features(df_buffer)
        fila_actual = df_features.iloc[[-1]][self.features_entrenamiento]

        pred_class = self.model.predict(fila_actual)[0]

        incidencias = []
        if pred_class == 1:
            incidencias.append(f"BLOQUEO DETECTADO en {ts}")
        elif pred_class == 2:
            incidencias.append(f"SALTO VOLTAJE en {ts}")
        return incidencias

    def analizar_todo(self, dataframe_completo: pd.DataFrame) -> List[str]:
        """Wrapper para analizar DataFrames completos (Simulación batch)."""
        print("   [IA] Analizando bloque completo...")
        alertas_totales = []
        self.buffer_lecturas = []
        for _, row in dataframe_completo.iterrows():
            lectura = {
                'timestamp': row['timestamp'],
                'voltageReceiver1': row['voltageReceiver1'] * 1000,
                'voltageReceiver2': row['voltageReceiver2'] * 1000,
                'status': row['status']
            }
            alertas = self.predecir_tiempo_real(lectura)
            alertas_totales.extend(alertas)
        return list(set(alertas_totales))
