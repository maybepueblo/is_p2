from typing import List
from interfaces import Suscriber


class Cliente(Suscriber):
    def __init__(self, email: str, id_cliente: str, es_admin: bool):
        self.email = email
        self.id = id_cliente
        self.es_admin = es_admin
        self.temas_suscritos: List[str] = []

    def update(self, mensaje: str):
        print(f"🔔 [NOTIFICACIÓN para {self.email}]: {mensaje}")
