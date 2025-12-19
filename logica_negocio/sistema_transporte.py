from typing import List
from cliente import Cliente
from lector_csv import LectorCSV
from visualizador import VisualizadorIncidencias
from modulo_inteligente import ModuloInteligente
from publisher import Publisher


class SistemaTransporte:
    def __init__(self):
        self.catalogo_clientes: List[Cliente] = []

        # Subsistemas
        self.lector_csv = LectorCSV()
        self.visualizador = VisualizadorIncidencias()
        self.publisher = Publisher()
        self.datos_actuales = None

        self.modulo_inteligente = ModuloInteligente()

        print("--- Inicializando Sistema de Transporte ---")
        exito = self.modulo_inteligente.cargar_modelo()

        if exito:
            print("✅ IA Operativa: Modelo predictivo cargado correctamente.")
        else:
            print("⚠️ ADVERTENCIA: No se encontró modelo entrenado.")

    def carga_datos(self, ruta_archivo: str):
        print(f"📥 Cargando datos operativos desde {ruta_archivo}...")
        try:
            self.datos_actuales = self.lector_csv.leer(ruta_archivo)
            if not self.datos_actuales.empty:
                print(f"   Datos cargados: {len(self.datos_actuales)} registros.")
            else:
                print("   Error: El archivo está vacío.")
        except Exception as e:
            print(f"   Error crítico al leer CSV: {e}")

    def suscribir_usuario(self, usuario: Cliente, tipo_incidencia: str):
        """
        Lógica corregida para soportar suscripciones múltiples.
        """
        if tipo_incidencia == "Ambos":
            # Suscribimos al usuario a LOS DOS canales principales
            self.publisher.suscribir(usuario, "Bloqueo")
            self.publisher.suscribir(usuario, "Salto")
        else:
            # Suscripción normal (solo Bloqueo o solo Salto)
            self.publisher.suscribir(usuario, tipo_incidencia)

        if usuario not in self.catalogo_clientes:
            self.catalogo_clientes.append(usuario)

    def desuscribir_usuario(self, email: str, tipo_incidencia: str):
        usuario = next((c for c in self.catalogo_clientes if c.email == email), None)
        if usuario:
            self.publisher.desuscribir(usuario, tipo_incidencia)

    def detectar_y_notificar(self):
        print("--- 🔍 Iniciando ciclo de detección y predicción ---")

        if self.datos_actuales is None:
            print("Error: No hay datos para analizar.")
            return

        if not self.modulo_inteligente.is_trained:
            print("Error: El modelo IA no está cargado/entrenado.")
            return

        # Obtenemos predicciones de la IA (lista de strings)
        incidencias = self.modulo_inteligente.analizar_todo(self.datos_actuales)

        if incidencias:
            n = len(incidencias)
            print(f"🚨 ALERTA: Se han detectado {n} incidencias.")

            # --- NUEVA LÓGICA DE CLASIFICACIÓN ---
            # Leemos el texto de la alerta para saber a qué canal enviarla
            for alerta in incidencias:
                if "BLOQUEO" in alerta.upper():
                    self.publisher.notificar(alerta, "Bloqueo")

                elif "SALTO" in alerta.upper():
                    self.publisher.notificar(alerta, "Salto")

                else:
                    # Fallback por si hay otro tipo
                    self.publisher.notificar(alerta, "Ambos")
        else:
            print("✅ Sistema estable. No se prevén anomalías.")

    def publicar_incidencia(self, cliente: Cliente, tema: str, mensaje: str):
        if not cliente.es_admin:
            print(f"❌ ACCESO DENEGADO: {cliente.email} no es admin.")
            return

        print(f"📢 Publicación manual de: {cliente.email}")
        aviso = f"⚠️ AVISO MANUAL (Admin: {cliente.email}): {mensaje}"
        self.publisher.notificar(aviso, tema)

    def ver_estadisticas(self, usuario: Cliente):
        if self.datos_actuales is None:
            return

        incidencias = self.modulo_inteligente.analizar_todo(self.datos_actuales)

        self.visualizador.generar_grafica_incidencias(incidencias)  # Histograma
        self.visualizador.generar_grafica_sectores(incidencias)  # Tarta (Nuevo)
        self.visualizador.generar_grafica_tendencia(self.datos_actuales)  # Líneas