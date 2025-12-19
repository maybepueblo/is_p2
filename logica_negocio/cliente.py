from typing import List
from interfaces import Suscriber


class Cliente(Suscriber):
    def __init__(self, email: str, id_cliente: str, es_admin: bool):
        self.email = email
        self.id = id_cliente
        self.es_admin = es_admin
        # Ahora TODOS los clientes tienen memoria
        self.buzon_mensajes: List[str] = []

    def update(self, mensaje: str):
        # Guardamos el mensaje en memoria
        self.buzon_mensajes.append(mensaje)
        # Opcional: imprimir en consola para depurar
        # print(f"🔔 [Buzón {self.email}]: {mensaje}")

    def limpiar_buzon(self):
        self.buzon_mensajes = []