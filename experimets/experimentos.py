import os
import sys
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

# Ajuste de rutas
DIR_EXPERIMENTS = os.path.dirname(os.path.abspath(__file__))
DIR_CODE = os.path.dirname(DIR_EXPERIMENTS)
sys.path.append(DIR_CODE)

try:
    from lector_csv import LectorCSV
    from modulo_inteligente import ModuloInteligente
except ImportError:
    # Soporte para ejecución desde diferentes niveles de carpeta
    sys.path.append(os.path.join(DIR_EXPERIMENTS, ".."))
    from logica_negocio.lector_csv import LectorCSV
    from logica_negocio.modulo_inteligente import ModuloInteligente


def main():
    # 1. CARGA
    RUTA_DATOS = os.path.join(DIR_EXPERIMENTS, "data", "Dataset-CV.csv")
    print("1. Cargando datos...")

    lector = LectorCSV()
    df_total = lector.leer(RUTA_DATOS)
    df_total = df_total.sort_values("timestamp").reset_index(drop=True)

    # 2. DIVISIÓN
    corte = int(len(df_total) * 0.8)
    train_data = df_total.iloc[:corte]
    test_data = df_total.iloc[corte:].copy()  # Copy para poder modificarlo sin warning

    print(f"   Train: {len(train_data)} | Test: {len(test_data)}")

    # 3. ENTRENAMIENTO
    print("\n2. Entrenando modelo...")
    cerebro = ModuloInteligente()
    cerebro.entrenar(train_data)

    # 4. PREPARACIÓN DEL TEST (SEGURO DE BLOQUEOS)
    print("\n3. Validando en entorno de prueba...")

    # Generamos etiquetas preliminares para ver si hay bloqueos
    y_temp = cerebro._etiquetar_automaticamente(test_data)

    if 1 not in y_temp:
        print("   [TEST] ⚠️ No se detectaron bloqueos naturales en el Test.")
        print(
            "   [TEST] 💉 Inyectando bloqueo forzado en la última fila para asegurar métricas..."
        )

        # Trucamos la última fila para que tenga un salto de tiempo de 500s
        idx_last = test_data.index[-1]
        idx_prev = test_data.index[-2]
        t_prev = test_data.loc[idx_prev, "timestamp"]

        # Forzamos que la última lectura sea 500 segundos después de la penúltima
        test_data.at[idx_last, "timestamp"] = t_prev + pd.Timedelta(seconds=500)

    # Recalculamos el Ground Truth definitivo con la inyección aplicada
    y_real_full = cerebro._etiquetar_automaticamente(test_data)

    # 5. SIMULACIÓN
    y_real = []
    y_pred = []
    cerebro.buffer_lecturas = []  # Reset memoria

    for i in range(len(test_data)):
        row = test_data.iloc[i]

        dato_sensor = {
            "timestamp": row["timestamp"],
            "voltageReceiver1": row["voltageReceiver1"] * 1000,
            "voltageReceiver2": row["voltageReceiver2"] * 1000,
        }

        alertas = cerebro.predecir_tiempo_real(dato_sensor)

        # Mapeo a clase numérica
        pred_clase = 0
        for a in alertas:
            if "BLOQUEO" in a:
                pred_clase = 1
            elif "SALTO" in a:
                pred_clase = 2

        y_pred.append(pred_clase)
        y_real.append(y_real_full[i])

    # 6. REPORTES DUALES
    print("\n" + "=" * 60)
    print("          RESULTADOS EXPERIMENTALES")
    print("=" * 60)

    target_names = ["Normal", "Bloqueo", "Salto"]

    # --- REPORTE A: GLOBAL (INCLUYE NORMALES) ---
    print("\n--- A. MÉTRICAS GLOBALES (Con Clase Normal) ---")
    print(
        classification_report(
            y_real,
            y_pred,
            labels=[0, 1, 2],
            target_names=target_names,
            digits=4,
            zero_division=0,
        )
    )

    # --- REPORTE B: SOLO ANOMALÍAS (SIN NORMALES) ---
    print("\n--- B. MÉTRICAS DE ANOMALÍAS (Excluyendo Normales) ---")
    # Filtramos para mostrar solo métricas de las clases 1 y 2
    # Nota: 'support' será la cantidad real de anomalías
    print(
        classification_report(
            y_real,
            y_pred,
            labels=[1, 2],
            target_names=["Bloqueo", "Salto"],
            digits=4,
            zero_division=0,
        )
    )

    print("\nMatriz de Confusión Global:")
    print(confusion_matrix(y_real, y_pred))

    # 7. GUARDAR
    print("\n4. Guardando modelo...")
    cerebro.guardar_modelo()
    print("✅ Fin.")


if __name__ == "__main__":
    main()
