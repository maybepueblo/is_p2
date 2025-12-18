import os
import sys
import xgboost as xgb
from sklearn.metrics import classification_report
import itertools

# --- CONFIGURACIÓN DE RUTAS ---
DIR_EXPERIMENTS = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(DIR_EXPERIMENTS))

try:
    from lector_csv import LectorCSV
    from modulo_inteligente import ModuloInteligente
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(DIR_EXPERIMENTS), "logica_negocio"))
    from logica_negocio.lector_csv import LectorCSV
    from logica_negocio.modulo_inteligente import ModuloInteligente


def evaluar_configuracion(train_data, test_data, window_size, xgb_params):
    """
    Entrena y evalúa una configuración específica.
    """
    # 1. Instanciar
    cerebro = ModuloInteligente()

    # 2. Inyección de Parámetros
    cerebro.WINDOW_SIZE = window_size

    # Reconfiguramos el modelo interno con los nuevos hiperparámetros
    cerebro.model = xgb.XGBClassifier(
        objective="multi:softmax",
        num_class=3,
        eval_metric="mlogloss",
        use_label_encoder=False,
        random_state=42,
        **xgb_params,
    )

    # 3. Entrenamiento
    # (Opcional, si quieres ver el progreso borra el block_print)
    sys.stdout = open(os.devnull, "w")
    try:
        cerebro.entrenar(train_data)
    finally:
        sys.stdout = sys.__stdout__

    # 4. Evaluación Rápida (Sin simulación paso a paso para velocidad)
    # Generamos las features del test con la ventana actual
    df_test_feat = cerebro._generar_features(test_data)
    y_real = cerebro._etiquetar_automaticamente(df_test_feat)

    # Preparamos X_test eliminando columnas no válidas
    cols_drop = ["timestamp", "medida", "id", "canal", "valor", "status"]
    features_validas = [
        c for c in df_test_feat.columns if c not in cols_drop and "tiempo" not in c
    ]
    X_test = df_test_feat[features_validas]

    y_pred = cerebro.model.predict(X_test)

    # 5. Cálculo de Métricas
    # Prioridad: Recall de Bloqueo (Clase 1)
    # Usamos zero_division=0 para evitar warnings si no hay bloqueos en el split natural
    report = classification_report(y_real, y_pred, output_dict=True, zero_division=0)

    recall_bloqueo = report.get("1", {}).get("recall", 0.0)
    # A veces las keys son floats '1.0' o ints '1' dependiendo de la versión
    if "1" not in report:
        recall_bloqueo = report.get("1.0", {}).get("recall", 0.0)

    accuracy = report["accuracy"]

    # F1-Score promedio macro (buen balance general)
    f1_macro = report["macro avg"]["f1-score"]

    return accuracy, recall_bloqueo, f1_macro


def main():
    # 1. Carga
    RUTA_DATOS = os.path.join(DIR_EXPERIMENTS, "data", "Dataset-CV.csv")
    if not os.path.exists(RUTA_DATOS):
        # Fallback de ruta
        RUTA_DATOS = os.path.join(
            os.path.dirname(DIR_EXPERIMENTS), "data", "Dataset-CV.csv"
        )

    print(f"Cargando datos desde: {RUTA_DATOS}")
    lector = LectorCSV()
    df_total = lector.leer(RUTA_DATOS)
    df_total = df_total.sort_values("timestamp").reset_index(drop=True)

    # División 80/20
    corte = int(len(df_total) * 0.8)
    train_data = df_total.iloc[:corte]
    test_data = df_total.iloc[corte:]

    print(f"Datos cargados. Train: {len(train_data)}, Test: {len(test_data)}")

    # 2. GRID DEFINITION
    ventanas = [3, 5, 10]
    params_xgboost = {
        "n_estimators": [50, 100, 200],
        "max_depth": [6, 9, 12],
        "learning_rate": [0.05, 0.1],
    }

    # Producto cartesiano de parámetros
    keys, values = zip(*params_xgboost.items())
    combinaciones_xgb = [dict(zip(keys, v)) for v in itertools.product(*values)]

    total_iter = len(ventanas) * len(combinaciones_xgb)
    print(f"\n--- INICIANDO GRID SEARCH ({total_iter} combinaciones) ---")
    print("-" * 95)
    print(
        f"{'WIN':<4} | {'DEPTH':<5} | {'EST':<4} | {'LR':<5} || {'ACCURACY':<8} | {'REC_BLK':<8} | {'F1_MACRO':<8}"
    )
    print("-" * 95)

    mejores_resultados = []

    # 3. EJECUCIÓN
    count = 0
    for w in ventanas:
        for p in combinaciones_xgb:
            count += 1
            try:
                # Barra de progreso simple
                print(f"\rProcesando {count}/{total_iter}...", end="", flush=True)

                acc, rec_blk, f1 = evaluar_configuracion(train_data, test_data, w, p)

                # Limpiamos línea para imprimir resultado
                print(
                    f"\r{w:<4} | {p['max_depth']:<5} | {p['n_estimators']:<4} | {p['learning_rate']:<5} || {acc:.4f}   | {rec_blk:.4f}   | {f1:.4f}"
                )

                mejores_resultados.append(
                    {
                        "window": w,
                        "params": p,
                        "acc": acc,
                        "recall_block": rec_blk,
                        "f1": f1,
                    }
                )
            except Exception as e:
                print(f"\nError en config W={w}, P={p}: {e}")

    # 4. SELECCIÓN DEL GANADOR
    print("-" * 95)
    # Criterio: Mejor Accuracy pero que tenga Recall de Bloqueo decente (>0.8)
    # Si ninguno tiene buen recall de bloqueo, nos quedamos con el mejor F1

    candidatos_seguros = [r for r in mejores_resultados if r["recall_block"] > 0.8]

    if candidatos_seguros:
        mejor = max(candidatos_seguros, key=lambda x: x["acc"])
        criterio = "Mejor Accuracy (con Recall Bloqueo > 0.8)"
    else:
        mejor = max(mejores_resultados, key=lambda x: x["recall_block"])
        criterio = "Mejor Recall Bloqueo (Prioridad Seguridad)"

    print(f"\n🏆 CONFIGURACIÓN GANADORA ({criterio}):")
    print(f"   Ventana: {mejor['window']}")
    print(f"   Params:  {mejor['params']}")
    print(
        f"   Scores:  Acc={mejor['acc']:.4f}, Rec_Block={mejor['recall_block']:.4f}, F1={mejor['f1']:.4f}"
    )


if __name__ == "__main__":
    main()
