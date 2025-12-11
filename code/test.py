import os
import sys
import pandas as pd

# Importamos las clases que ya tienes definidas
try:
    from LectorCSV import LectorCSV
    from ModuloInteligente import ModuloInteligente
except ImportError as e:
    print("❌ Error: No se encuentran los archivos 'LectorCSV.py' o 'ModuloInteligente.py'.")
    print("Asegúrate de ejecutar este script desde la misma carpeta donde están los módulos.")
    sys.exit(1)


def main():
    # 1. DEFINICIÓN DE LA RUTA (Según tus indicaciones)
    RUTA_ARCHIVO = os.path.join("experimets/data", "Dataset-CV.csv")

    print(f"--- INICIANDO SISTEMA DE DETECCIÓN FERROVIARIA ---")

    # Verificación básica de existencia del archivo
    if not os.path.exists(RUTA_ARCHIVO):
        print(f"❌ Error: No se encuentra el archivo en: {RUTA_ARCHIVO}")
        print("Por favor crea la carpeta 'data' y coloca dentro el archivo 'Dataset-CV.csv'.")
        return

    # 2. INSTANCIACIÓN DE COMPONENTES (Arquitectura Modular)
    # Fachada instanciando los subsistemas [cite: 53, 54]
    try:
        lector = LectorCSV()
        cerebro = ModuloInteligente()
        print("✅ Componentes inicializados correctamente.")
    except Exception as e:
        print(f"❌ Error al inicializar componentes: {e}")
        return

    # 3. FASE DE LECTURA (Delegación en LectorCSV) [cite: 97]
    print(f"\n[1/3] Leyendo y procesando {RUTA_ARCHIVO}...")
    try:
        df_datos = lector.leer(RUTA_ARCHIVO)

        if df_datos.empty:
            print("⚠️  Advertencia: El archivo se leyó pero no contiene datos válidos o procesables.")
            return

        print(f"      -> Lectura exitosa. Se han cargado {len(df_datos)} registros temporales.")
        print(f"      -> Rango de fechas: {df_datos['timestamp'].min()} a {df_datos['timestamp'].max()}")

    except Exception as e:
        print(f"❌ Error durante la lectura del CSV: {e}")
        return

    # 4. FASE DE APRENDIZAJE (Entrenamiento del XGBoost)
    # Necesario para que el modelo pueda predecir en el siguiente paso
    print("\n[2/3] Entrenando modelo inteligente (Weak Supervision)...")
    try:
        cerebro.entrenar(df_datos)
    except Exception as e:
        print(f"❌ Error durante el entrenamiento: {e}")
        return

    # 5. FASE DE DETECCIÓN Y PREDICCIÓN (Lógica de Negocio) [cite: 98]
    print("\n[3/3] Analizando datos en busca de incidencias...")
    try:
        reporte_incidencias = cerebro.detectar_y_predecir(df_datos)
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        return

    # 6. REPORTE DE RESULTADOS (Salida)
    print("\n" + "=" * 60)
    print(f"REPORTE FINAL DE INCIDENCIAS ({len(reporte_incidencias)} detectadas)")
    print("=" * 60)

    if not reporte_incidencias:
        print("✅ Estado de la vía: NORMAL. No se detectaron anomalías.")
    else:
        # Mostramos solo las primeras 20 si hay muchísimas, para no saturar la consola
        limite_mostrar = 20
        for i, inc in enumerate(reporte_incidencias):
            if i >= limite_mostrar:
                print(f"... y {len(reporte_incidencias) - limite_mostrar} incidencias más.")
                break

            ts = inc.get('timestamp', 'N/A')
            tipo = inc.get('tipo', 'DESCONOCIDO')
            msj = inc.get('mensaje', '')
            val = inc.get('valor', '')

            # Formato legible
            print(f"[{ts}] {tipo}")
            print(f"   Valor: {val} | Detalle: {msj}")
            print("-" * 60)


if __name__ == "__main__":
    main()