import os
import sys
import pandas as pd
import numpy as np
# Importamos métricas de sklearn
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# --- CONFIGURACIÓN DE RUTAS ---
DIR_EXPERIMENTS = os.path.dirname(os.path.abspath(__file__))
DIR_CODE = os.path.dirname(DIR_EXPERIMENTS)
sys.path.append(DIR_CODE)

try:
    from lector_csv import LectorCSV
    from modulo_inteligente import ModuloInteligente
except ImportError:
    sys.exit("❌ No se encuentran los módulos LectorCSV o ModuloInteligente.")


def calcular_ground_truth(df_test):
    """
    Calcula las etiquetas REALES (0, 1, 2) del set de prueba basándose
    estrictamente en las reglas físicas, para poder compararlas con la predicción.
    """
    df = df_test.copy()

    # Recalculamos deltas vectorizados (como si tuviéramos la visión completa)
    df['delta_t'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
    v1_diff = df['voltageReceiver1'].diff().abs().fillna(0)
    v2_diff = df['voltageReceiver2'].diff().abs().fillna(0)
    df['max_v_jump'] = pd.concat([v1_diff, v2_diff], axis=1).max(axis=1)

    # Reglas estrictas (Las mismas que definimos en el módulo)
    LIMITE_TIEMPO = 120
    UMBRAL_VOLTAJE = 0.5

    # 0: Normal, 1: Bloqueo, 2: Salto
    y_true = np.zeros(len(df))

    # Prioridad 1: Bloqueo
    y_true[df['delta_t'] > LIMITE_TIEMPO] = 1

    # Prioridad 2: Salto (si no es bloqueo)
    mask_salto = (df['max_v_jump'] >= UMBRAL_VOLTAJE) & (y_true == 0)
    y_true[mask_salto] = 2

    return y_true


def interpretar_prediccion(alertas):
    """
    Convierte la lista de alertas (texto) que devuelve el sistema
    en un número de clase (0, 1, 2) para poder medir la precisión.
    """
    if not alertas:
        return 0  # Clase Normal

    # Buscamos qué tipo de alerta es
    tipos = [a['tipo'] for a in alertas]

    # Damos prioridad al Bloqueo si aparecen ambas (raro)
    if any("BLOQUEO" in t for t in tipos):
        return 1
    if any("SALTO" in t for t in tipos):
        return 2

    return 0  # Por defecto


def main():
    RUTA_DATOS = os.path.join(DIR_EXPERIMENTS, "data", "Dataset-CV.csv")

    # 1. LECTURA
    lector = LectorCSV()
    df_total = lector.leer(RUTA_DATOS)

    # 2. DIVISIÓN TEMPORAL (80/20)
    corte = int(len(df_total) * 0.8)
    train_data = df_total.iloc[:corte]
    test_data = df_total.iloc[corte:]

    print(f"--- ENTRENAMIENTO ---")
    cerebro = ModuloInteligente()
    cerebro.entrenar(train_data)

    # 3. PREPARACIÓN DE MÉTRICAS
    # Calculamos qué DEBERÍA salir (Ground Truth)
    # Nota: La primera fila del test dará 0 delta porque diff() no ve el train,
    # pero es aceptable para la evaluación masiva.
    y_real = calcular_ground_truth(test_data)
    y_predicho = []

    print(f"\n--- SIMULACIÓN TIEMPO REAL ({len(test_data)} filas) ---")

    # 4. BUCLE DE SIMULACIÓN
    for idx, row in test_data.iterrows():
        # A. Transformación del dato sucio/raw (Simulación Sensor)
        dato_sensor = {
            'timestamp': row['timestamp'],
            # Multiplicamos por 1000 simulando que llegan milivoltios
            'voltageReceiver1': row['voltageReceiver1'] * 1000,
            'voltageReceiver2': row['voltageReceiver2'] * 1000,
            'status': 1
        }

        # B. Inferencia con Memoria (El modelo transforma y compara con su estado anterior)
        alertas = cerebro.predecir_tiempo_real(dato_sensor)

        # C. Guardar predicción numérica para métricas
        clase_pred = interpretar_prediccion(alertas)
        y_predicho.append(clase_pred)

        # (Opcional) Imprimir solo si hay alerta para no saturar consola
        if alertas:
            pass  # print(f"🚨 Detectado: {alertas[0]['tipo']}")

    # 5. GENERACIÓN DE REPORTES
    print("\n" + "=" * 50)
    print("       RESULTADOS DE LA EVALUACIÓN")
    print("=" * 50)

    # Matriz de Confusión
    cm = confusion_matrix(y_real, y_predicho)
    print("\nMatriz de Confusión:")
    print(cm)
    print("(Filas: Realidad, Columnas: Predicción)")

    # Reporte completo
    target_names = ['Normal (0)', 'Bloqueo (1)', 'Salto (2)']
    # Ajustamos nombres si alguna clase no aparece en el test
    clases_en_test = sorted(list(set(y_real) | set(y_predicho)))
    nombres_presentes = [target_names[int(i)] for i in clases_en_test]

    print("\nReporte de Métricas:")
    print(classification_report(y_real, y_predicho, target_names=nombres_presentes, digits=4))

    acc = accuracy_score(y_real, y_predicho)
    print(f"Global Accuracy: {acc:.2%}")
    print("=" * 50)


if __name__ == "__main__":
    main()