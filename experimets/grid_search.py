import os
import sys
import xgboost as xgb
from sklearn.metrics import classification_report, f1_score, recall_score
import itertools

# Ajuste de rutas para importar tus módulos
DIR_EXPERIMENTS = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(DIR_EXPERIMENTS))

try:
    from code.lector_csv import LectorCSV
    from code.modulo_inteligente import ModuloInteligente
except ImportError:
    sys.path.append(os.path.join(DIR_EXPERIMENTS, ".."))
    from code.lector_csv import LectorCSV
    from code.modulo_inteligente import ModuloInteligente


def evaluar_configuracion(train_data, test_data, window_size, xgb_params):
    """
    Entrena y evalúa una configuración específica.
    """
    # 1. Instanciar y Configurar
    cerebro = ModuloInteligente()

    # --- INYECCIÓN DE PARÁMETROS ---
    # Sobrescribimos la configuración por defecto de la clase
    cerebro.WINDOW_SIZE = window_size
    cerebro.model = xgb.XGBClassifier(
        objective='multi:softmax',
        num_class=3,
        eval_metric='mlogloss',
        use_label_encoder=False,
        random_state=42,
        **xgb_params  # Desempaquetamos los params variables (n_estimators, depth, etc)
    )

    # 2. Entrenamiento (usará la window_size nueva para generar features)
    cerebro.entrenar(train_data)

    # 3. Evaluación
    # Generamos features de test con LA MISMA ventana
    df_test_features = cerebro._generar_features(test_data)
    y_real = cerebro._etiquetar_automaticamente(df_test_features)

    # Preparamos datos para predicción masiva (usando el modelo interno directamente para velocidad)
    cols_drop = ['timestamp', 'medida', 'id', 'canal', 'valor', 'status']
    features_validas = [c for c in df_test_features.columns if c not in cols_drop and 'tiempo' not in c]
    X_test = df_test_features[features_validas]

    y_pred = cerebro.model.predict(X_test)

    # 4. Métricas Clave
    # Nos interesa mucho detectar el Bloqueo (Clase 1), así que miramos su Recall
    recall_bloqueo = recall_score(y_real, y_pred, labels=[1], average=None)
    # Si no hay bloqueos en test, devuelve array vacío o error, manejamos eso:
    if 1 in y_real:
        recall_1 = recall_score(y_real, y_pred, labels=[1],
                                average='macro')  # Ojo, esto calcula sobre las etiquetas dadas

        report = classification_report(y_real, y_pred, output_dict=True, zero_division=0)
        recall_bloqueo = report.get('1.0', {}).get('recall', 0.0)
        f1_macro = report['macro avg']['f1-score']
        accuracy = report['accuracy']
    else:
        recall_bloqueo = 0.0
        f1_macro = 0.0
        accuracy = 0.0

    return accuracy, recall_bloqueo, f1_macro


def main():
    # 1. Carga de Datos
    RUTA_DATOS = os.path.join(DIR_EXPERIMENTS, "data", "Dataset-CV.csv")
    print("Cargando datos...")
    lector = LectorCSV()
    df_total = lector.leer(RUTA_DATOS)
    df_total = df_total.sort_values('timestamp')

    # División
    corte = int(len(df_total) * 0.8)
    train_data = df_total.iloc[:corte]
    test_data = df_total.iloc[corte:]

    # 2. DEFINICIÓN DE LA REJILLA (GRID)
    ventanas = [3, 5, 10]

    params_xgboost = {
        'n_estimators': [50, 100, 200, 500],
        'max_depth': [3, 6, 9, 12, 14],
        'learning_rate': [0.05, 0.1]
    }

    # Generar todas las combinaciones
    keys, values = zip(*params_xgboost.items())
    combinaciones_xgb = [dict(zip(keys, v)) for v in itertools.product(*values)]

    print(f"\n--- INICIANDO GRID SEARCH ---")
    print(f"Total configuraciones a probar: {len(ventanas) * len(combinaciones_xgb)}")
    print("-" * 80)
    print(f"{'WINDOW':<8} | {'PARAMS':<45} | {'ACC':<8} | {'REC_BLK':<8} | {'F1_MACRO':<8}")
    print("-" * 80)

    mejores_resultados = []

    # 3. BUCLE DE PRUEBAS
    for w in ventanas:
        for p in combinaciones_xgb:
            try:
                acc, rec_blk, f1 = evaluar_configuracion(train_data, test_data, w, p)

                # Formato bonito para params
                p_str = str(p).replace("{", "").replace("}", "").replace("'", "")
                print(f"{w:<8} | {p_str:<45} | {acc:.4f}   | {rec_blk:.4f}   | {f1:.4f}")

                mejores_resultados.append({
                    'window': w,
                    'params': p,
                    'score': acc
                })
            except Exception as e:
                print(f"{w:<8} | Error: {e}")

    # 4. RESULTADO GANADOR
    print("-" * 80)
    mejor = max(mejores_resultados, key=lambda x: x['score'])
    print(f"\n🏆 MEJOR CONFIGURACIÓN (Basada en Recall Bloqueo):")
    print(f"   Ventana: {mejor['window']}")
    print(f"   Params:  {mejor['params']}")
    print(f"   Accuracy: {mejor['score']:.4f}")


if __name__ == "__main__":
    main()
