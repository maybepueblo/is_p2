import pandas as pd
import os

# Importar la clase LectorCSV
from server.lector_csv import LectorCSV

# =====================
# CONFIGURACIÓN
# =====================
LIMITE_TIEMPO_SEC = 120  # debe coincidir con ModuloInteligente

RUTA_DATASET = os.path.join(os.path.dirname(__file__), "data", "Dataset-CV.csv")

# =====================
# CARGA CON LectorCSV
# =====================
print("Cargando dataset con LectorCSV...")
lector = LectorCSV()
df = lector.leer(RUTA_DATASET)

print(f"Dataset cargado: {len(df)} registros")
print(f"Columnas: {list(df.columns)}")
# =====================
# CÁLCULO DE GAPS
# =====================
df["delta_t"] = df["timestamp"].diff().dt.total_seconds()

# Filtrar bloqueos
bloqueos = df[df["delta_t"] > LIMITE_TIEMPO_SEC]

# =====================
# RESULTADOS
# =====================
print("\n" + "=" * 60)
print("RESULTADO DE ANÁLISIS DE BLOQUEOS")
print("=" * 60)

if bloqueos.empty:
    print("❌ No se han encontrado bloqueos (> {} s)".format(LIMITE_TIEMPO_SEC))
else:
    print(f"✅ Bloqueos encontrados: {len(bloqueos)}\n")

    for idx, row in bloqueos.iterrows():
        print(f"🔴 BLOQUEO DETECTADO")
        print(f"   Índice fila     : {idx}")
        print(f"   Timestamp actual: {row['timestamp']}")
        print(f"   Gap (segundos)  : {row['delta_t']}")
        print("-" * 40)

# =====================
# ESTADÍSTICAS EXTRA
# =====================
print("\nEstadísticas de delta_t:")
print(df["delta_t"].describe())
