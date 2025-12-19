import sys
import os
from flask import Flask, jsonify, render_template, request

# Ajuste robusto de rutas para encontrar 'logica_negocio'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'logica_negocio'))

from sistema_transporte import SistemaTransporte
from cliente import Cliente

app = Flask(__name__)

class ClienteMonitorWeb(Cliente):
    """
    Cliente 'espía' que permite a la web ver lo que pasa en el sistema.
    """
    def __init__(self, email, id_cliente, es_admin):
        super().__init__(email, id_cliente, es_admin)
        self.buzon_mensajes = []

    def update(self, mensaje: str):
        self.buzon_mensajes.append(mensaje)


# --- INICIALIZACIÓN DEL SISTEMA ---
print("--- 🌐 INICIANDO SERVIDOR WEB METRO ---")
sistema = SistemaTransporte()

# 1. Creamos el Monitor Web y lo suscribimos a TODO ("Ambos")
monitor_web = ClienteMonitorWeb("monitor@web.interface", "WEB-SYS", True)
sistema.suscribir_usuario(monitor_web, "Ambos")

# 2. CARGA DE DATOS ROBUSTA
# Busca en la carpeta hermana 'data' subiendo un nivel
RUTA_DATOS = os.path.join(BASE_DIR, "..", "data", "Dataset-CV.csv")

if os.path.exists(RUTA_DATOS):
    sistema.carga_datos(RUTA_DATOS)
else:
    # Intento alternativo por si ejecutas desde raíz
    RUTA_DATOS = os.path.join("data", "Dataset-CV.csv")
    if os.path.exists(RUTA_DATOS):
        sistema.carga_datos(RUTA_DATOS)
    else:
        print(f"⚠️ AVISO CRÍTICO: No se encontró el dataset en {os.path.abspath(RUTA_DATOS)}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/estado')
def api_estado():
    # Limpiamos el buzón para recibir solo lo nuevo de este ciclo
    monitor_web.buzon_mensajes = []

    # FORZAMOS AL SISTEMA A TRABAJAR (Modo Batch Rápido)
    sistema.detectar_y_notificar()

    alertas_crudas = monitor_web.buzon_mensajes
    datos_respuesta = []

    if not alertas_crudas:
        datos_respuesta.append({
            "tipo": "ESTADO",
            "mensaje": "✅ Sistema operativo. Sin incidencias reportadas.",
            "hora": "Ahora"
        })
    else:
        for msg in alertas_crudas:
            tipo = "INFO"
            if "BLOQUEO" in msg: tipo = "PELIGRO 🛑"
            elif "SALTO" in msg: tipo = "PREDICCIÓN ⚡" # Cambiado a Predicción
            elif "SISTEMA" in msg: tipo = "SYSTEM ℹ️"
            elif "MANUAL" in msg: tipo = "ADMIN 📢"

            datos_respuesta.append({
                "tipo": tipo,
                "mensaje": msg,
                "hora": "Detectado"
            })

    return jsonify(datos_respuesta)

@app.route('/api/usuarios', methods=['POST'])
def api_nuevo_usuario():
    datos = request.get_json()
    email = datos.get('email')
    opcion = datos.get('topico')

    tema_real = "Ambos"
    if opcion == "1": tema_real = "Bloqueo"
    if opcion == "2": tema_real = "Salto"
    if opcion == "3": tema_real = "Ambos"

    if email:
        nuevo_id = f"U-{len(sistema.catalogo_clientes) + 1}"
        nuevo_cliente = Cliente(email, nuevo_id, False)
        sistema.suscribir_usuario(nuevo_cliente, tema_real)
        print(f"👤 Nuevo usuario web: {email} -> {tema_real}")
        return jsonify({"msg": f"Registrado correctamente en alertas de: {tema_real}"}), 200

    return jsonify({"error": "Datos incompletos"}), 400

@app.route('/api/aviso_manual', methods=['POST'])
def api_aviso_manual():
    datos = request.get_json()
    mensaje = datos.get('mensaje')

    if mensaje:
        sistema.publicar_incidencia(monitor_web, "Bloqueo", mensaje)
        sistema.publicar_incidencia(monitor_web, "Salto", mensaje)
        return jsonify({"msg": "Aviso enviado a todos los canales."}), 200

    return jsonify({"error": "Mensaje vacío"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)