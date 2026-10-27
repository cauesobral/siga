from abc import ABC, abstractmethod
from datetime import date
from enum import IntEnum


class NivelDeImpacto(IntEnum):
    BAIXO = 1
    MEDIO = 2
    ALTO = 3
    CRITICO = 4


class EventoDeRisco(ABC):

    def __init__(self, categoria: str, nivel_de_impacto: NivelDeImpacto,
                 data_inicio: date, data_fim: date):
        if data_fim < data_inicio:
            raise ValueError("data_fim não pode ser anterior a data_inicio")
        self._categoria = categoria
        self._nivel_de_impacto = nivel_de_impacto
        self._data_inicio = data_inicio
        self._data_fim = data_fim


    def get_categoria(self):
        return self._categoria

    def get_nivel_de_impacto(self):
        return self._nivel_de_impacto

    def get_data_inicio(self):
        return self._data_inicio

    def get_data_fim(self):
        return self._data_fim

    def esta_ativo(self, data: date):
        data = data
        return self._data_inicio <= data && data <= self._data_fim

    @abstractmethod
    def bloqueia_atracacao(self, navio):
	pass

    @abstractmethod
    def descricao(self):
        pass