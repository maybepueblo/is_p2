from abc import ABC, abstractmethod


class Suscriber(ABC):
    """Interfaz abstracta para los suscriptores."""

    @abstractmethod
    def update(self, mensaje: str):
        pass
