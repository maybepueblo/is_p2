from typing import List
from cliente import Cliente
from lector_csv import LectorCSV
from visualizador import VisualizadorIncidencias
from modulo_inteligente import ModuloInteligente
from publisher import Publisher


class SistemaTransporte:
    def __init__(self):
        self.catalogo_clientes: List[Cliente] = []
        self.lector_csv = LectorCSV()
        self.visualizador = VisualizadorIncidencias()
        self.modulo_inteligente = ModuloInteligente()
        self.publisher = Publisher()
        self.datos_actuales = None

    def carga_datos(self, ruta_archivo: str):
        self.lector_csv.ruta_archivo = ruta_archivo
        self.datos_actuales = self.lector_csv.leer()
        print("Datos cargados en el sistema.")

    def suscribir_usuario(self, usuario: Cliente, tipo_incidencia: str):
        self.publisher.suscribir(usuario, tipo_incidencia)
        if usuario not in self.catalogo_clientes:
            self.catalogo_clientes.append(usuario)

    def desuscribir_usuario(self, usuario: Cliente, tipo_incidencia: str):
        self.publisher.desuscribir(usuario, tipo_incidencia)

    def ver_estadisticas(self, usuario: Cliente):
        # AQUI LA USAMOS: Imprimimos quién solicita la gráfica
        print(f"Generando reporte estadístico solicitado por: {usuario.email}")

        if self.datos_actuales is not None:
            self.visualizador.generar_grafica_tendencia(self.datos_actuales)
        else:
            print("No hay datos cargados.")

    def detectar_y_notificar(self):
        print("--- Iniciando ciclo de detección ---")
        if self.datos_actuales is None:
            return

        incidencias = self.modulo_inteligente.analizar_todo(self.datos_actuales)

        if incidencias:
            print(f"Se detectaron {len(incidencias)} incidencias.")
            mensaje = f"Alertas: {', '.join(set(incidencias))}"
            self.publisher.notificar(mensaje, "Mantenimiento")
            self.visualizador.generar_grafica_incidencias(incidencias)
        else:
            print("Sistema estable.")
