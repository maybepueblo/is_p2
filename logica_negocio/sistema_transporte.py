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
        print(f"📥 Cargando datos masivos desde {ruta_archivo}...")
        try:
            self.datos_actuales = self.lector_csv.leer(ruta_archivo)
            if not self.datos_actuales.empty:
                print(f"   Datos cargados: {len(self.datos_actuales)} registros.")
            else:
                print("   Error: El archivo está vacío.")
        except Exception as e:
            print(f"   Error crítico al leer CSV: {e}")

    def suscribir_usuario(self, usuario: Cliente, tipo_incidencia: str):
        if tipo_incidencia == "Ambos":
            self.publisher.suscribir(usuario, "Bloqueo")
            self.publisher.suscribir(usuario, "Salto")
        else:
            self.publisher.suscribir(usuario, tipo_incidencia)

        if usuario not in self.catalogo_clientes:
            self.catalogo_clientes.append(usuario)

    def desuscribir_usuario(self, email: str, tipo_incidencia: str):
        usuario = next((c for c in self.catalogo_clientes if c.email == email), None)
        if usuario:
            self.publisher.desuscribir(usuario, tipo_incidencia)

    def detectar_y_notificar(self):
        print("--- 🔍 Iniciando análisis predictivo masivo ---")

        if self.datos_actuales is None: return
        if not self.modulo_inteligente.is_trained: return

        # 1. Obtenemos TODAS las incidencias (las 78.000)
        todas_incidencias = self.modulo_inteligente.analizar_todo(self.datos_actuales)

        if todas_incidencias:
            total = len(todas_incidencias)
            print(f"⚡ ANÁLISIS COMPLETADO: {total} eventos detectados.")

            # ========================================================
            # 🧠 FILTRADO INTELIGENTE (PRIORIDAD DE SEGURIDAD)
            # ========================================================
            # Separamos las alertas críticas de las informativas
            bloqueos = [i for i in todas_incidencias if "BLOQUEO" in i.upper()]
            saltos = [i for i in todas_incidencias if "SALTO" in i.upper() or "PREDICCIÓN" in i.upper()]
            otros = [i for i in todas_incidencias if i not in bloqueos and i not in saltos]

            alertas_a_enviar = []

            # 1. LOS BLOQUEOS ENTRAN SIEMPRE (VIP)
            alertas_a_enviar.extend(bloqueos)

            # 2. Rellenamos con Saltos (solo los más recientes hasta llegar a 50)
            hueco_disponible = 50 - len(alertas_a_enviar)

            if hueco_disponible > 0 and saltos:
                # Cogemos los ULTIMOS saltos (los más recientes en el tiempo)
                recientes = saltos[-hueco_disponible:]
                alertas_a_enviar.extend(recientes)

            # Aviso de resumen
            if total > 50:
                n_ocultos = total - len(alertas_a_enviar)
                aviso = f"ℹ️ SISTEMA: Se detectaron {len(bloqueos)} Bloqueos Críticos y {len(saltos)} Predicciones. (Ocultando {n_ocultos} alertas antiguas)"
                self.publisher.notificar(aviso, "Ambos")

            # ========================================================

            # Enviamos la lista filtrada y priorizada
            for alerta in alertas_a_enviar:
                if "BLOQUEO" in alerta.upper():
                    self.publisher.notificar(alerta, "Bloqueo")
                elif "SALTO" in alerta.upper() or "PREDICCIÓN" in alerta.upper():
                    self.publisher.notificar(alerta, "Salto")
                else:
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
        if self.datos_actuales is None: return
        # Aquí también usamos el método rápido
        incidencias = self.modulo_inteligente.analizar_todo(self.datos_actuales)
        self.visualizador.generar_grafica_incidencias(incidencias)
        self.visualizador.generar_grafica_sectores(incidencias)
        self.visualizador.generar_grafica_tendencia(self.datos_actuales)