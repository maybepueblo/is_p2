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
        self.publisher = Publisher()
        self.datos_actuales = None
        self.modulo_inteligente = ModuloInteligente()

        print("--- Inicializando Sistema ---")
        self.modulo_inteligente.cargar_modelo()

    def carga_datos(self, ruta_archivo: str):
        try:
            self.datos_actuales = self.lector_csv.leer(ruta_archivo)
            print(f"📥 Datos cargados: {len(self.datos_actuales)} registros.")
        except Exception as e:
            print(f"❌ Error CSV: {e}")

    def suscribir_usuario(self, usuario: Cliente, opcion: str):
        """
        Gestiona la lógica de suscripción limpia.
        opcion: 'Bloqueo', 'Salto' o 'Ambos'
        """
        # 1. Limpieza total previa (para evitar duplicados al cambiar)
        self.publisher.desuscribir(usuario, "Bloqueo")
        self.publisher.desuscribir(usuario, "Salto")
        self.publisher.desuscribir(usuario, "System")

        # 2. Nueva suscripción
        if opcion == "Bloqueo":
            self.publisher.suscribir(usuario, "Bloqueo")
        elif opcion == "Salto":
            self.publisher.suscribir(usuario, "Salto")
        elif opcion == "Ambos":
            # Si quiere ambos, lo apuntamos a las dos listas
            self.publisher.suscribir(usuario, "Bloqueo")
            self.publisher.suscribir(usuario, "Salto")

        # Siempre suscrito a mensajes del sistema (para errores o avisos globales)
        self.publisher.suscribir(usuario, "System")

        if usuario not in self.catalogo_clientes:
            self.catalogo_clientes.append(usuario)

    def detectar_y_notificar(self):
        if self.datos_actuales is None or not self.modulo_inteligente.is_trained: return

        # 1. Predicciones IA (Lista de strings)
        alertas_ia = self.modulo_inteligente.analizar_todo(self.datos_actuales)

        # 2. Detección Física (Manual) para asegurar los bloqueos reales
        # Esto es necesario por si la IA es muy estricta
        alertas_fisicas = []
        df = self.datos_actuales
        # Calculamos delta_t aquí mismo rápido
        deltas = df["timestamp"].diff().dt.total_seconds().fillna(0)
        # Buscamos índices donde delta > 120
        idx_reales = deltas[deltas > 120].index

        for idx in idx_reales:
            ts = df.iloc[idx]["timestamp"]
            # Usamos EL MISMO formato de texto que la IA para que el 'set' detecte que son iguales
            alertas_fisicas.append(f"🔴 BLOQUEO DETECTADO en {ts}")

        # 3. UNIÓN SIN DUPLICADOS (La clave para que salgan 2 y no 4)
        # Convertimos a conjunto (set) y volvemos a lista
        todas_unicas = list(set(alertas_ia + alertas_fisicas))

        if not todas_unicas:
            return

        # 4. Clasificación y Priorización (VIP)
        bloqueos = sorted([x for x in todas_unicas if "BLOQUEO" in x.upper()])
        saltos = sorted([x for x in todas_unicas if "SALTO" in x.upper() or "PREDICCIÓN" in x.upper()])

        # Cogemos todos los bloqueos + los últimos 50 saltos
        finales = bloqueos + saltos[-50:]

        print(f"⚡ Notificando: {len(bloqueos)} Bloqueos y {len(saltos)} Predicciones.")

        # 5. Envío al Publisher (Canalizado correctamente)
        for msg in finales:
            if "BLOQUEO" in msg.upper():
                self.publisher.notificar(msg, "Bloqueo")
            elif "SALTO" in msg.upper() or "PREDICCIÓN" in msg.upper():
                self.publisher.notificar(msg, "Salto")
            else:
                self.publisher.notificar(msg, "System")

    def publicar_incidencia(self, cliente: Cliente, tema: str, mensaje: str):
        # Para avisos manuales, los mandamos a System para que lleguen a todos
        # o a los canales específicos
        if cliente.es_admin:
            aviso = f"📢 ADMIN: {mensaje}"
            self.publisher.notificar(aviso, "Bloqueo")
            self.publisher.notificar(aviso, "Salto")
