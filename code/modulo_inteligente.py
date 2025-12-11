import pandas as pd
import numpy as np
from typing import List

class AlgortimoDeteccion:
    def detectarAusenciaDatos(self, datos: pd.DataFrame) -> bool:
        return bool(datos.empty)

    def detectarSaltosFrecuencia(self, datos: pd.DataFrame) -> bool:
        if "frecuencia" in datos.columns:
            std_dev = np.std(datos["frecuencia"])
            # CAMBIO AQUÍ: Convertir numpy.bool_ a bool de python
            return bool(std_dev > 5.0)
        return False

class AlgortimoPrediccion:
    def __init__(self):
        self.modelo = None

    def predecir(self, datos: pd.DataFrame) -> List[str]:
        predicciones = []

        if "voltaje" in datos.columns:
            for v in datos["voltaje"]:
                if v > 0.8:
                    predicciones.append("Fallo Crítico")
                elif v > 0.5:
                    predicciones.append("Advertencia")
                else:
                    predicciones.append("Normal")

        return predicciones

class ModuloInteligente:
    def __init__(self):
        self.detector = AlgortimoDeteccion()
        self.predictor = AlgortimoPrediccion()

    def analizar_todo(self, datos: pd.DataFrame) -> List[str]:
        incidencias = []

        # 1. Ejecutar Detección
        if self.detector.detectarAusenciaDatos(datos):
            return ["Error: Ausencia de datos"]

        if self.detector.detectarSaltosFrecuencia(datos):
            incidencias.append("Salto de Frecuencia detectado")

        # 2. Ejecutar Predicción
        predicciones = self.predictor.predecir(datos)
        incidencias.extend([p for p in predicciones if p != "Normal"])

        return incidencias
