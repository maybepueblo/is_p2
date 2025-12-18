import os
import sys
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

DIR_EXPERIMENTS = os.path.dirname(os.path.abspath(__file__))
DIR_CODE = os.path.dirname(DIR_EXPERIMENTS)
sys.path.append(DIR_CODE)

try:
    from code.lector_csv import LectorCSV
    from code.modulo_inteligente import ModuloInteligente
except ImportError:
    sys.path.append(os.path.join(DIR_EXPERIMENTS, ".."))
    from code.lector_csv import LectorCSV
    from code.modulo_inteligente import ModuloInteligente


def main():
    # 1. CARGA
    RUTA_DATOS = os.path.join(DIR_EXPERIMENTS, "data", "Dataset-CV.csv")
    print("1. Cargando datos...")
    lector = LectorCSV()
    df_total = lector.leer(RUTA_DATOS)
    df_total = df_total.sort_values('timestamp')

    # 2. DIVISIÓN TEMPORAL
    corte = int(len(df_total) * 0.8)
    train_data = df_total.iloc[:corte]
    test_data = df_total.iloc[corte:]

    print(f"   Train: {len(train_data)} | Test: {len(test_data)}")

    # 3. ENTRENAMIENTO
    print("\n2. Entrenando Modelo (XGBoost + Inyección Sintética)...")
    cerebro = ModuloInteligente()
    cerebro.entrenar(train_data)

    # 4. EXPERIMENTO Y VALIDACIÓN
    print("\n3. Validando en entorno de prueba...")

    # Ground Truth para comparación
    df_test_features = cerebro._generar_features(test_data)
    y_real_full = cerebro._etiquetar_automaticamente(df_test_features)

    y_real = []
    y_pred = []
    cerebro.buffer_lecturas = []  # Reset memoria

    for i in range(len(test_data)):
        row = test_data.iloc[i]
        dato_sensor = {
            'timestamp': row['timestamp'],
            'voltageReceiver1': row['voltageReceiver1'] * 1000,
            'voltageReceiver2': row['voltageReceiver2'] * 1000,
            'status': 1
        }

        # Inferencia
        alertas = cerebro.predecir_tiempo_real(dato_sensor)

        # Mapeo Texto -> Clase para métricas
        pred_clase = 0
        for a in alertas:
            if "BLOQUEO" in a:
                pred_clase = 1
            elif "SALTO" in a:
                pred_clase = 2

        y_pred.append(pred_clase)
        y_real.append(y_real_full[i])

    # Reporte
    print("\n" + "=" * 50)
    print("       RESULTADOS EXPERIMENTALES")
    print("=" * 50)

    target_names = ['Normal', 'Bloqueo', 'Salto']
    labels_presentes = sorted(list(set(y_real) | set(y_pred)))
    names_presentes = [target_names[int(i)] for i in labels_presentes]

    print(classification_report(y_real, y_pred, target_names=names_presentes, digits=4))
    print("Matriz de Confusión:\n", confusion_matrix(y_real, y_pred))

    # 5. PERSISTENCIA AUTOMÁTICA
    print("\n4. Exportando Cerebro Entrenado...")
    cerebro.guardar_modelo()
    print("   ✅ Experimento finalizado.")


if __name__ == "__main__":
    main()
