# is_p2

# Diapos Walter

---

1. Data set
**El Reto:** 
El CSV original presentaba lecturas de múltiples canales (a/b) y receptores mezcladas bajo la misma marca de tiempo (minuto).
**Solución:**
- Pivot Table Dinámica: Transformación de filas a columnas manteniendo la integridad de cada lectura individual.
- Normalización: Conversión estandarizada de milivoltios (mV) a Voltios (V) para el modelo.
**Resultado:**
- Un dataset limpio, secuencial y sin pérdida de picos de señal críticos.

---

2. Arquitectura de Software
Patrón Fachada (SistemaTransporte):
- Abstracción: Centraliza la complejidad. El cliente no interactúa directamente con el modelo ni con el parseo de datos.
- Ciclo de Vida: Gestiona la carga automática del modelo persistido (.pkl) al iniciar, verificando la operatividad de la IA.
Patrón Observer (Publisher):
- Desacoplamiento: Separa la lógica de detección (IA) del sistema de notificación.
- Escalabilidad: Permite notificar a múltiples suscriptores (Mantenimiento, Logs) sin modificar el núcleo inteligente.
Persistencia y Modularidad:
- Serialización con joblib para guardar el estado del modelo entrenado (is_trained, features), permitiendo despliegues sin re-entrenamiento.
- Diseño modular donde ModuloInteligente encapsula toda la lógica de predicción.

---

3. Estrategia de IA (Mecánica de Predicción)
Modelo Híbrido (Reactivo vs. Predictivo) El sistema no trata todas las incidencias igual, respeta su naturaleza física:
- Bloqueos (Modo Reactivo): Al ser cortes súbitos (sin síntomas previos), la detección es inmediata al superar el umbral de seguridad (gap > 120s). Recall: 100%.
- Saltos de Voltaje (Modo Predictivo): Se aprovecha la inercia térmica/eléctrica. El modelo busca "síntomas precursores" para anticipar el pico. 
El Mecanismo de Predicción ¿Cómo sabe el modelo lo que pasará en el futuro?
- Entrenamiento (Look-Ahead): Usamos una ventana futura de 120 segundos. Si en el futuro (T+120) ocurre un fallo, enseñamos al modelo a reconocer el patrón de ondas actual (T) como una "alerta temprana".
- Inferencia (Tiempo Real): El modelo analiza solo los últimos 10 eventos (Ventana Pasada). Si detecta ese patrón aprendido (micro-oscilaciones o aceleración), lanza la predicción. 
Ingeniería de Características (La Física del Dato) No damos al modelo solo el valor crudo, le damos la cinemática:
- Velocidad (diff): Diferencia instantánea. Vital para diferenciar una subida normal de un inicio de salto.
- Contexto (Window=10): Medias y desviaciones de los últimos 10 paquetes para entender la estabilidad.
- Coherencia: Cruce matemático entre Receptor 1 y 2 para descartar ruido de un solo sensor.
Seguridad por Diseño (Data Augmentation)
- Ante la escasez de fallos graves reales, se inyectaron 2.000 bloqueos sintéticos con duración variable (125s - 1000s).
- Objetivo: Forzar al algoritmo XGBoost a priorizar la clase minoritaria ("silencio de señal") sobre la precisión normal.

---

4. Optimización de Hiperparámetros
Configuración Final (Validada): Tras la experimentación usando un grid search, se seleccionaron los siguientes parámetros que maximizan el rendimiento:
- Ventana (Window): 10 (Analiza una secuencia más larga para mayor contexto).
- Profundidad (Max Depth): 6 (Balance entre complejidad y prevención de over-fitting).
- Estimadores: 100 (Árboles de decisión).
- Learning Rate: 0.1.

Justificación: Esta combinación específica logró estabilizar la detección de saltos, reduciendo los falsos positivos en la clase normal.

5. Resultados Experimentales
Rendimiento Global:
- Accuracy: 94.51% (Validado sobre 22.372 registros de test).
- F1-Score Macro: 0.9540 (Excelente equilibrio entre clases).
Análisis por Incidencia:
 - Bloqueos:
   - Recall: 1.00 (100%). Se detectaron todos los eventos de bloqueo.
   - Seguridad: Ningún falso negativo en la categoría.
 - Saltos de Voltaje:
   - Precision: 95.84%.
   - Recall: 96.60%. Capacidad muy alta para anticipar picos de tensión.
Matriz de Confusión:
- Robustez: De 6.196 casos normales, solo 678 fueron falsas alarmas ( ~10% de tasa de falsa alarma, aceptable para priorizar seguridad).
- Eficacia: 15.624 saltos correctamente identificados de un total de 16.174.
   
---
