import numpy as np
from typing import List


class ModuloInteligente:
    def __init__(self):
        self.umbral_voltaje: float = 0.5
        self.tiempo_limite_minutos: int = 2

    def predecir(self, datos) -> List[str]:
        predicciones = []
        for v in datos["voltaje"]:
            if v > 0.8:
                predicciones.append("Fallo Crítico")
            elif v > self.umbral_voltaje:
                predicciones.append("Advertencia")
            else:
                predicciones.append("Normal")
        return predicciones

    def comprobar_ausencia_datos(self, datos) -> bool:
        return bool(datos.empty)  # Convertir a bool explícito

    def comprobar_salto_frecuencia(self, datos) -> bool:
        if "frecuencia" in datos.columns:
            std_dev = np.std(datos["frecuencia"])
            # CAMBIO AQUÍ: Convertir numpy.bool_ a bool de python
            return bool(std_dev > 5.0)
        return False

    def analizar_todo(self, datos) -> List[str]:
        if self.comprobar_ausencia_datos(datos):
            return ["Error: Ausencia de datos"]

        incidencias = []
        if self.comprobar_salto_frecuencia(datos):
            incidencias.append("Salto de Frecuencia detectado")

        predicciones = self.predecir(datos)
        incidencias.extend([p for p in predicciones if p != "Normal"])

        return incidencias
