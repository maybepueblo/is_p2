from typing import List, Dict
from interfaces import Suscriber


class Publisher:
    def __init__(self):
        # Diccionario: Clave=Tema, Valor=Lista de Suscriptores
        self._suscriptores: Dict[str, List[Suscriber]] = {}

    def suscribir(self, suscriptor: Suscriber, tema: str):
        if tema not in self._suscriptores:
            self._suscriptores[tema] = []
        if suscriptor not in self._suscriptores[tema]:
            self._suscriptores[tema].append(suscriptor)
            print(f"DEBUG: Suscriptor añadido al tema '{tema}'.")

    def desuscribir(self, suscriptor: Suscriber, tema: str):
        if tema in self._suscriptores and suscriptor in self._suscriptores[tema]:
            self._suscriptores[tema].remove(suscriptor)

    def notificar(self, incidencia: str, tema: str):
        if tema in self._suscriptores:
            for suscriptor in self._suscriptores[tema]:
                suscriptor.update(incidencia)
