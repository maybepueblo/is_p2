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
            print(
                "   El sistema no detectará nada hasta que ejecutes 'experimentos.py'."
            )

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
        self.publisher.suscribir(usuario, tipo_incidencia)
        if usuario not in self.catalogo_clientes:
            self.catalogo_clientes.append(usuario)

    def desuscribir_usuario(self, usuario: Cliente, tipo_incidencia: str):
        self.publisher.desuscribir(usuario, tipo_incidencia)

    def ver_estadisticas(self, usuario: Cliente):
        print(f"Generando reporte estadístico solicitado por: {usuario.email}")
        if self.datos_actuales is not None:
            # Asumiendo que el visualizador soporta este método
            self.visualizador.generar_grafica_tendencia(self.datos_actuales)
        else:
            print("No hay datos cargados para visualizar.")

    def detectar_y_notificar(self):
        print("--- 🔍 Iniciando ciclo de detección y predicción ---")

        # Validaciones previas
        if self.datos_actuales is None:
            print("Error: No hay datos para analizar.")
            return

        if not self.modulo_inteligente.is_trained:
            print("Error: El modelo IA no está cargado/entrenado.")
            return

        # Delegamos al subsistema complejo
        # 'analizar_todo' procesa el dataframe y devuelve lista de strings
        incidencias = self.modulo_inteligente.analizar_todo(self.datos_actuales)

        if incidencias:
            n = len(incidencias)
            print(f"🚨 ALERTA: Se han detectado {n} posibles incidencias futuras.")

            # Notificamos (Patrón Observer)
            # Mostramos las primeras 3 para no saturar el mensaje
            detalle = "; ".join(incidencias[:3])
            if n > 3:
                detalle += f"... y {n - 3} más."

            mensaje = f"REPORTE PREDICTIVO: {detalle}"
            self.publisher.notificar(mensaje, "Mantenimiento")

        else:
            print("✅ Sistema estable. No se prevén anomalías.")

    def publicar_incidencia(self, cliente: Cliente, tema: str, mensaje: str):

        # 1. Validación de seguridad
        if not cliente.es_admin:
            print(f"❌ ACCESO DENEGADO: El usuario {cliente.email} no tiene permisos de administrador.")
            return

        # 2. Orquestación: Se delega la difusión al Publisher
        print(f"📢 Publicación autorizada para: {cliente.email}")
        aviso = f"⚠️ AVISO MANUAL (Admin: {cliente.email}): {mensaje}"

        self.publisher.notificar(aviso, tema)
