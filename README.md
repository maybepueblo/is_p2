# 🚄 Sistema de Mantenimiento Predictivo Ferroviario (IS-P2)

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Framework](https://img.shields.io/badge/Framework-Flask-green)
![AI](https://img.shields.io/badge/AI-XGBoost-orange)
![Frontend](https://img.shields.io/badge/Frontend-Chart.js-pink)
![Env](https://img.shields.io/badge/Env-uv-purple)

Sistema inteligente de monitorización para infraestructuras ferroviarias.  
Combina **Inteligencia Artificial (Machine Learning)** con **reglas físicas deterministas** para detectar y predecir anomalías en el suministro eléctrico ferroviario en tiempo real.

---

## 📋 Descripción del Proyecto

El sistema procesa telemetría de voltaje procedente de sensores en vía (Receptores 1 y 2) para identificar dos tipos de incidencias críticas:

1. **🛑 Bloqueos (Críticos)**  
   Cortes súbitos de comunicación o caída total de señal.  
   Se detectan mediante **lógica reactiva determinista**, garantizando un **Recall del 100%**.

2. **⚡ Saltos de Voltaje (Preventivos)**  
   Inestabilidades eléctricas progresivas.  
   Se predicen con **120 segundos de antelación** mediante un modelo **XGBoost**, siguiendo un **enfoque híbrido**.

El sistema incluye un **Dashboard Web interactivo** que permite:
- Visualizar telemetría en tiempo real (simulado).
- Gestionar suscripciones de alertas.
- Simular distintos roles de usuario.

---

## 🚀 Características Principales

- **Arquitectura Híbrida**
  - Reglas físicas → Seguridad crítica.
  - Machine Learning → Mantenimiento predictivo.

- **Alto rendimiento**
  - Accuracy global: **94.51%**
  - Detección de bloqueos: **100% (sin falsos negativos)**

- **Patrón Publisher–Subscriber**
  - Sistema desacoplado de notificaciones.
  - Cada usuario recibe solo las alertas a las que está suscrito:
    - Seguridad
    - Mantenimiento
    - Global

- **Dashboard Web**
  - Gráficas dinámicas con Chart.js.
  - Buzón de alertas por usuario.
  - Panel de administración y simulación.

- **Procesamiento optimizado**
  - Análisis vectorial batch.
  - Capaz de procesar +100.000 registros en milisegundos.

---

## 📂 Estructura del Proyecto

```text
is_p2/
├── .venv/                     # Entorno virtual (gestionado por uv)
│
├── data/
│   └── Dataset-CV.csv         # Dataset principal
│
├── experiments/               # Experimentación y entrenamiento
│   ├── data/
│   ├── model/
│   ├── experimentos.py        # Pruebas del modelo
│   ├── check_bloqueos.py      # Análisis de bloqueos del dataset
│   └── grid_search.py         # Búsqueda de hiperparámetros
│
├── server/                    # Núcleo del sistema
│   ├── model/                 # Modelo entrenado (.pkl)
│   ├── templates/
│   │   └── index.html         # Dashboard Web
│   ├── __init__.py
│   ├── app.py                 # Servidor Flask (Entry Point)
│   ├── modulo_inteligente.py  # Motor IA + lógica híbrida
│   ├── sistema_transporte.py  # Fachada del sistema
│   ├── publisher.py           # Publisher (Observer)
│   ├── cliente.py             # Entidad Subscriber
│   ├── lector_csv.py          # Ingesta de datos
│   └── interfaces.py          # Contratos e interfaces
│
├── pyproject.toml             # Dependencias y configuración del proyecto
├── uv.lock                    # Lockfile de dependencias
├── .python-version            # Versión de Python
├── README.md
└── pyrightconfig.json
````

---

## ⚙️ Instalación y Ejecución (usando `uv`)

Este proyecto **no usa `requirements.txt`**.
La gestión de dependencias se realiza mediante **`uv` + `pyproject.toml`**.

### 1. Requisitos Previos

* Python **3.10+**
* `uv` instalado

Instalación de `uv` (si no lo tienes):
**Windows**
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

```
**Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

### 2. Crear y sincronizar el entorno virtual

Desde la raíz del proyecto (`is_p2/`):

```bash
uv venv
uv sync
```

Esto:

* Crea `.venv/`
* Instala todas las dependencias definidas en `pyproject.toml`
* Respeta las versiones fijadas en `uv.lock`

---

### 3. Activar el entorno

**Linux / macOS**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

---

### 4. Ejecutar la aplicación web

```bash
python server/app.py
```

Abrir en el navegador:

```
http://127.0.0.1:5000
```

---

## 🖥️ Manual de Uso del Dashboard

### ▶ Panel Principal

* Pulsa **“⚡ Ejecutar Análisis IA”**
* El sistema:

  * Carga el CSV
  * Procesa los datos
  * Prioriza bloqueos
  * Simula streaming de voltaje

---

### 👥 Simulación de Usuarios (Publisher–Subscriber)

Desde el panel lateral:

* **Seguridad**

  * Suscripción: Bloqueos
  * Alertas rojas 🛑

* **Mantenimiento**

  * Suscripción: Predicciones
  * Alertas amarillas ⚡

* **Administrador**

  * Suscripción: Ambas
  * Visión completa del sistema

---

### 🔄 Recalcular

* Limpia memoria
* Reprocesa todo el dataset
* Respuesta inmediata gracias al procesamiento vectorial

---

## 🧠 Estrategia Híbrida (Detalle Técnico)

Durante la experimentación se observó que los modelos ML puros **fallaban al detectar bloqueos reales** debido a su carácter aleatorio.

### Solución implementada

1. **Bloqueos**

   * Monitorización de `Δt` entre paquetes
   * Si `Δt > 120s` → Alerta determinista inmediata

2. **Saltos de voltaje**

   * Modelo **XGBoost**
   * Ventana deslizante (`window = 10`)
   * Features cinemáticas 
   * Horizonte de predicción: **120s**

3. **Data Augmentation**

   * +2000 casos sintéticos de bloqueo
   * Garantiza prioridad absoluta de eventos críticos

---

Proyecto desarrollado para la asignatura
**Ingeniería del Software – Práctica 2**
