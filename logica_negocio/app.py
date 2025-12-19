import sys
import os
from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from sistema_transporte import SistemaTransporte
from cliente import Cliente

app = Flask(__name__)

# --- INICIALIZACIÓN ---
print("--- 🌐 SERVIDOR INICIADO ---")
sistema = SistemaTransporte()

# Monitor Admin (Suscrito a todo)
admin = Cliente("admin@sys.com", "ADMIN", True)
sistema.suscribir_usuario(admin, "Ambos")

# Carga de datos
RUTA = os.path.join(BASE_DIR, "..", "data", "Dataset-CV.csv")
if not os.path.exists(RUTA): RUTA = os.path.join("data", "Dataset-CV.csv")
if os.path.exists(RUTA): sistema.carga_datos(RUTA)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/estado')
def api_estado():
    email = request.args.get('email')
    target = admin  # Por defecto vemos lo que ve el admin

    if email:
        found = next((c for c in sistema.catalogo_clientes if c.email == email), None)
        if found: target = found

    # Mapeo de colores para el frontend
    respuesta = []
    for m in target.buzon_mensajes:
        tipo = "INFO"
        if "BLOQUEO" in m.upper():
            tipo = "PELIGRO 🛑"
        elif "SALTO" in m.upper() or "PREDICCIÓN" in m.upper():
            tipo = "PREDICCIÓN ⚡"
        elif "ADMIN" in m.upper():
            tipo = "ADMIN 📢"

        respuesta.append({"tipo": tipo, "mensaje": m, "hora": "Detectado"})

    return jsonify(respuesta)


@app.route('/api/recalcular', methods=['POST'])
def api_recalcular():
    # Limpiamos buzones de todos
    for c in sistema.catalogo_clientes: c.limpiar_buzon()
    admin.limpiar_buzon()

    # Recalculamos (rellenará los buzones según suscripciones)
    sistema.detectar_y_notificar()
    return jsonify({"msg": "OK"})


@app.route('/api/usuarios', methods=['POST'])
def api_nuevo_usuario():
    datos = request.get_json()
    email = datos.get('email')
    opcion = datos.get('topico')  # "1", "2", "3"

    tema = "Ambos"
    if opcion == "1": tema = "Bloqueo"
    if opcion == "2": tema = "Salto"

    if email:
        # Buscamos o creamos usuario
        cliente = next((c for c in sistema.catalogo_clientes if c.email == email), None)
        if not cliente:
            cliente = Cliente(email, f"U-{len(sistema.catalogo_clientes)}", False)

        # 1. Cambiamos la suscripción (El método del sistema ya maneja la limpieza)
        sistema.suscribir_usuario(cliente, tema)

        # 2. Vaciamos su buzón visual
        cliente.limpiar_buzon()

        # 3. Recalculamos para que le lleguen sus alertas nuevas INMEDIATAMENTE
        sistema.detectar_y_notificar()

        return jsonify({"msg": f"Suscripción activa: {tema}"})

    return jsonify({"error": "Falta email"}), 400


@app.route('/api/aviso_manual', methods=['POST'])
def api_aviso_manual():
    d = request.get_json()
    if d.get('mensaje'):
        sistema.publicar_incidencia(admin, "Bloqueo", d['mensaje'])
        sistema.publicar_incidencia(admin, "Salto", d['mensaje'])
        return jsonify({"msg": "OK"})
    return jsonify({"error": "Vacío"}), 400


# Variable global para saber por dónde vamos "leyendo" el CSV
# Simula el paso del tiempo.
CURSOR_GRAFICA = 0


@app.route('/api/grafica')
def api_grafica():
    """
    Simula un streaming de datos avanzando por el CSV.
    Cada vez que la web pregunta, avanzamos el cursor.
    """
    global CURSOR_GRAFICA

    if sistema.datos_actuales is None or sistema.datos_actuales.empty:
        return jsonify({"labels": [], "v1": [], "v2": []})

    total_filas = len(sistema.datos_actuales)

    # Definimos el tamaño de la ventana (cuántos puntos se ven a la vez)
    VENTANA_VISIBLE = 50

    # Si hemos llegado al final del archivo, volvemos a empezar (Bucle infinito)
    if CURSOR_GRAFICA + VENTANA_VISIBLE >= total_filas:
        CURSOR_GRAFICA = 0

    # Extraemos el "trozo" actual del CSV
    datos_slice = sistema.datos_actuales.iloc[CURSOR_GRAFICA: CURSOR_GRAFICA + VENTANA_VISIBLE]

    # Preparamos los datos
    labels = datos_slice['timestamp'].dt.strftime('%H:%M:%S').tolist()
    v1 = datos_slice['voltageReceiver1'].astype(float).tolist()
    v2 = datos_slice['voltageReceiver2'].astype(float).tolist()

    # AVANZAMOS EL CURSOR PARA LA PRÓXIMA VEZ
    # Avanzamos 5 filas cada vez que se actualiza (simula velocidad)
    CURSOR_GRAFICA += 5

    return jsonify({
        "labels": labels,
        "v1": v1,
        "v2": v2
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
