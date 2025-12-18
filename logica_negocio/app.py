import sys
import os
from flask import Flask, jsonify, render_template, request

# Ajusta esta ruta para apuntar a tu carpeta de lógica
sys.path.append(os.path.join(os.path.dirname(__file__), 'logica_negocio'))

from sistema_transporte import SistemaTransporte
from cliente import Cliente

app = Flask(__name__)


# --- CLASE ESPECIAL PARA LA WEB (PATRÓN OBSERVER) ---
class ClienteMonitorWeb(Cliente):
    """
    Cliente 'espía' que permite a la web ver lo que pasa en el sistema.
    Guarda los mensajes en una lista en vez de imprimir por consola.
    """

    def __init__(self, email, id_cliente, es_admin):
        super().__init__(email, id_cliente, es_admin)
        self.buzon_mensajes = []

    def update(self, mensaje: str):
        # En lugar de print(), guardamos el mensaje para que la API lo lea
        self.buzon_mensajes.append(mensaje)


# --- INICIALIZACIÓN DEL SISTEMA ---
print("--- INICIANDO SERVIDOR WEB METRO ---")
sistema = SistemaTransporte()

# 1. Creamos el Monitor Web y lo suscribimos a TODO ("Ambos")
# Así, la pantalla principal siempre mostrará todas las alertas.
monitor_web = ClienteMonitorWeb("monitor@web.interface", "WEB-SYS", True)
sistema.suscribir_usuario(monitor_web, "Ambos")

# 2. Carga de datos inicial
RUTA_DATOS = "datos.csv"  # Asegúrate de que este archivo existe
if os.path.exists(RUTA_DATOS):
    sistema.carga_datos(RUTA_DATOS)
else:
    print(f"⚠️ AVISO: No se encontró {RUTA_DATOS}. El sistema inicia vacío.")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/estado')
def api_estado():
    """
    La web consulta el estado actual.
    El sistema ejecuta su ciclo (detectar_y_notificar) y si hay algo,
    el monitor_web recibirá los mensajes en su método update().
    """
    # Limpiamos el buzón para recibir solo lo nuevo de este ciclo
    monitor_web.buzon_mensajes = []

    # FORZAMOS AL SISTEMA A TRABAJAR
    # (La web no toca la IA, solo le dice al sistema "haz tu trabajo")
    sistema.detectar_y_notificar()

    # Recogemos los mensajes que el sistema envió al monitor
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
            # Decoramos el mensaje para el frontend
            tipo = "INFO"
            if "BLOQUEO" in msg:
                tipo = "PELIGRO 🛑"
            elif "SALTO" in msg:
                tipo = "VOLTAJE ⚡"
            elif "MANUAL" in msg:
                tipo = "ADMIN 📢"

            datos_respuesta.append({
                "tipo": tipo,
                "mensaje": msg,
                "hora": "Reciente"
            })

    return jsonify(datos_respuesta)


@app.route('/api/usuarios', methods=['POST'])
def api_nuevo_usuario():
    """
    Registra un usuario suscrito al tópico 1, 2 o 3.
    """
    datos = request.get_json()
    email = datos.get('email')
    opcion = datos.get('topico')  # Viene como "1", "2" o "3"

    # Mapeo de opciones a Tópicos del Sistema
    tema_real = "Ambos"  # Por defecto
    if opcion == "1": tema_real = "Bloqueo"
    if opcion == "2": tema_real = "Salto"
    if opcion == "3": tema_real = "Ambos"

    if email:
        nuevo_id = f"U-{len(sistema.catalogo_clientes) + 1}"
        # Creamos usuario normal (no admin)
        nuevo_cliente = Cliente(email, nuevo_id, False)

        # El sistema se encarga de la lógica de suscripción compleja
        sistema.suscribir_usuario(nuevo_cliente, tema_real)

        print(f"👤 Nuevo usuario web: {email} -> {tema_real}")
        return jsonify({"msg": f"Registrado correctamente en alertas de: {tema_real}"}), 200

    return jsonify({"error": "Datos incompletos"}), 400


@app.route('/api/aviso_manual', methods=['POST'])
def api_aviso_manual():
    datos = request.get_json()
    mensaje = datos.get('mensaje')

    if mensaje:
        # Enviamos aviso al canal general "Mantenimiento" o a "Ambos" según se decida
        # Aquí usamos 'Bloqueo' y 'Salto' para asegurarnos que llegue a todos
        sistema.publicar_incidencia(monitor_web, "Bloqueo", mensaje)
        sistema.publicar_incidencia(monitor_web, "Salto", mensaje)
        return jsonify({"msg": "Aviso enviado a todos los canales."}), 200

    return jsonify({"error": "Mensaje vacío"}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5000)