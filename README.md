# is_p2

# Diapos Walter

---

## Adaptación del Dataset
**El Reto:** 
El CSV original presentaba lecturas de múltiples canales (a/b) y receptores mezcladas bajo la misma marca de tiempo (minuto).
**Solución:**
- Pivot Table Dinámica: Transformación de filas a columnas manteniendo la integridad de cada lectura individual.
- Normalización: Conversión estandarizada de milivoltios (mV) a Voltios (V) para el modelo.
**Resultado:**
- Un dataset limpio, secuencial y sin pérdida de picos de señal críticos.

---

## Arquitectura
**Módulo Inteligente**
- Ahora es solo una clase que encapsula toda la funcionalidad del modelo.
**Patrón Fachada (SistemaTransporte):** 
- Centraliza la complejidad. El cliente no interactúa con el modelo IA ni con el lector CSV directamente.
- Gestiona el ciclo de vida: Carga automática del modelo persistido (.pkl) al iniciar.
**Patrón Observer (Publisher):**
- Desacoplamiento total entre la detección de una incidencia y la notificación.
- Permite múltiples suscriptores (Mantenimiento, Admin, Logs) sin modificar la lógica de detección.
**Persistencia:**
- Implementación de joblib para guardar/cargar el "cerebro" entrenado, permitiendo el pase a producción sin re-entrenar.

---

## Estrategia de IA
**Modelo:**
- XGBoost Classifier (Gradient Boosting) debido a su alta eficiencia en datos tabulares y capacidad de manejar relacionales no lineales complejas entre voltaje y tiempo.
**Ingeniería de Características:**
- El modelo no juzga el valor instantáneo, sino el contexto temporal.
- Uso de Ventanas Deslizantes (Rolling Windows): Cálculo de Media, Desviación Estándar y Delta temporal de los últimos 3 eventos.
**Generación de datos sintéticos:**
- Para detectar la ausencia ya que solo hay 2 en el dataset y ahora los detectamos bien sin memorizarlos.
- 
---

## Optimización de Hiperparám
**Metodología:**
Se realizó una búsqueda experimental exhaustiva (Grid Search) para encontrar el equilibrio entre sensibilidad y precisión.

**Espacio de Búsqueda:**
- Tamaño de Ventana: [3, 5, 10] (Eventos pasados a considerar).
- Profundidad del Árbol (max_depth): [3, 6, 9, 12, 14].
- Estimadores (n_estimators): [50, 100, 200, 500].
- Learning Rate: [0.05, 0.1].

- (Poner en negrita el:
- ventana:3
- profundidad:9
- estimadores:50
- lr= 0.05
- )

---

## Resultados
- Accuracy: 99.9%
- **Conclusión:** El sistema prioriza la seguridad (no dejar pasar ningún bloqueo) asumiendo un coste en falsas alarmas de saltos de voltaje.