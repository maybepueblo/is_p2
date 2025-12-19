import sys
import os
from flask import Flask, jsonify, render_template, request

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from sistema_transporte import SistemaTransporte
from cliente import Cliente

app = Flask(__name__)

# ==========================================
# 1. INICIALIZACIÓN
# ==========================================
print("--- 🌐 SERVIDOR WEB INICIADO ---")
sistema = SistemaTransporte()

# Monitor Global (Admin) suscrito a todo
monitor_admin = Cliente("admin@sistema.com", "ADMIN-SYS", True)
sistema.suscribir_usuario(monitor_admin, "Ambos")

# Carga de datos
RUTA_DATOS = os.path.join(BASE_DIR, "..", "data", "Dataset-CV.csv")
if not os.path.exists(RUTA_DATOS):
    RUTA_DATOS = os.path.join(BASE_DIR, "data", "Dataset-CV.csv")

if os.path.exists(RUTA_DATOS):
    sistema.carga_datos(RUTA_DATOS)
else:
    print(f"⚠️ AVISO: No se encontró el dataset en {RUTA_DATOS}")


# ⚠️ NOTA: Ya no ejecutamos el análisis al inicio para que arranque rápido.
# Tendrás que darle al botón "Ejecutar Análisis" en la web.

# ==========================================
# 2. RUTAS
# ==========================================

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/estado')
def api_estado():
    """
    Devuelve las alertas del usuario solicitado.
    Si no se pide usuario, devuelve las del Admin (que ve todo).
    """
    email_usuario = request.args.get('email')

    # 1. Decidimos qué buzón mirar
    cliente_objetivo = monitor_admin  # Por defecto, el Admin

    if email_usuario:
        # Buscamos al usuario en la lista del sistema
        encontrado = next((c for c in sistema.catalogo_clientes if c.email == email_usuario), None)
        if encontrado:
            cliente_objetivo = encontrado

    # 2. Leemos SU buzón (que ya está filtrado por el Publisher)
    alertas = cliente_objetivo.buzon_mensajes

    datos_respuesta = []

    if not alertas:
        msj = "Esperando análisis..." if not sistema.modulo_inteligente.is_trained else "Sin alertas nuevas."
        datos_respuesta.append({
            "tipo": "ESTADO",
            "mensaje": f"✅ {msj} (Viendo buzón de: {cliente_objetivo.email})",
            "hora": "Ahora"
        })
    else:
        for msg in alertas:
            tipo = "INFO"
            if "BLOQUEO" in msg.upper():
                tipo = "PELIGRO 🛑"
            elif "SALTO" in msg.upper() or "PREDICCIÓN" in msg.upper():
                tipo = "PREDICCIÓN ⚡"
            elif "SISTEMA" in msg.upper():
                tipo = "SYSTEM ℹ️"
            elif "MANUAL" in msg.upper():
                tipo = "ADMIN 📢"

            datos_respuesta.append({
                "tipo": tipo,
                "mensaje": msg,
                "hora": "Detectado"
            })

    return jsonify(datos_respuesta)


@app.route('/api/recalcular', methods=['POST'])
def api_recalcular():
    print("🔄 Recalculando IA...")

    # Limpiamos buzones de TODOS para no duplicar info
    for c in sistema.catalogo_clientes:
        c.limpiar_buzon()
    monitor_admin.limpiar_buzon()

    # Ejecutamos la IA (Batch Rápido)
    # Esto llenará los buzones de cada usuario según su suscripción
    sistema.detectar_y_notificar()

    return jsonify({"msg": "Recálculo completado"})


@app.route('/api/usuarios', methods=['POST'])
def api_nuevo_usuario():
    datos = request.get_json()
    email = datos.get('email')
    opcion = datos.get('topico')

    tema_real = "Ambos"
    if opcion == "1": tema_real = "Bloqueo"
    if opcion == "2": tema_real = "Salto"

    if email:
        # Comprobamos si ya existe para no duplicar
        existente = next((c for c in sistema.catalogo_clientes if c.email == email), None)
        if existente:
            # Si existe, actualizamos su suscripción
            sistema.desuscribir_usuario(email, "Ambos")
            sistema.desuscribir_usuario(email, "Bloqueo")
            sistema.desuscribir_usuario(email, "Salto")
            # Re-suscribimos
            sistema.suscribir_usuario(existente, tema_real)
            cliente_ref = existente
            print(f"👤 Usuario actualizado: {email} -> {tema_real}")
        else:
            nuevo_id = f"U-{len(sistema.catalogo_clientes) + 1}"
            nuevo_cliente = Cliente(email, nuevo_id, False)
            sistema.suscribir_usuario(nuevo_cliente, tema_real)
            print(f"👤 Nuevo usuario registrado: {email} -> {tema_real}")

        return jsonify({"msg": f"Usuario activo: {email}", "tema": tema_real}), 200

    return jsonify({"error": "Falta email"}), 400


@app.route('/api/aviso_manual', methods=['POST'])
def api_aviso_manual():
    datos = request.get_json()
    mensaje = datos.get('mensaje')
    if mensaje:
        sistema.publicar_incidencia(monitor_admin, "Bloqueo", mensaje)
        sistema.publicar_incidencia(monitor_admin, "Salto", mensaje)
        return jsonify({"msg": "Aviso enviado."}), 200
    return jsonify({"error": "Mensaje vacío"}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5000)
