from typing import List
from cliente import Cliente
from lector_csv import LectorCSV
from visualizador import VisualizadorIncidencias
from modulo_inteligente import ModuloInteligente
from publisher import Publisher
import os


class SistemaTransporte:
    def __init__(self):
        self.catalogo_clientes: List[Cliente] = []
        self.lector_csv = LectorCSV()
        self.visualizador = VisualizadorIncidencias()
        self.publisher = Publisher()
        self.datos_actuales = None

        # INICIALIZACIÓN INTELIGENTE
        self.modulo_inteligente = ModuloInteligente()

        # Intentamos cargar el cerebro ya entrenado
        if os.path.exists("modelo_ferroviario.pkl"):
            self.modulo_inteligente.cargar_modelo("modelo_ferroviario.pkl")
        else:
            print(
                "⚠️ ADVERTENCIA: No se encontró 'modelo_ferroviario.pkl'. El sistema no detectará nada hasta que se entrene.")

    def carga_datos(self, ruta_archivo: str):
        # Ajuste para usar el método leer(ruta) de LectorCSV
        print(f"Cargando datos desde {ruta_archivo}...")
        self.datos_actuales = self.lector_csv.leer(ruta_archivo)
        print(f"Datos cargados: {len(self.datos_actuales)} registros.")

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
            print("No hay datos cargados.")

    def detectar_y_notificar(self):
        print("--- Iniciando ciclo de detección ---")
        if self.datos_actuales is None:
            print("Error: No hay datos para analizar.")
            return

        # Aquí delegamos al subsistema complejo (ModuloInteligente)
        # Usamos el nuevo método 'analizar_todo' que itera internamente
        incidencias = self.modulo_inteligente.analizar_todo(self.datos_actuales)

        if incidencias:
            print(f"🚨 Se detectaron {len(incidencias)} eventos críticos.")

            # Notificamos (Patrón Observer a través del Publisher)
            # Unificamos alertas para no spammear
            mensaje = f"REPORTE INCIDENCIAS: {'; '.join(incidencias[:5])}..."  # Solo las primeras 5 en el resumen
            self.publisher.notificar(mensaje, "Mantenimiento")

        else:
            print("✅ Sistema estable. No se detectaron anomalías.")

