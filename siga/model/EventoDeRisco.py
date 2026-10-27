from abc import ABC, abstractmethod
from datetime import date
from enum import IntEnum


class NivelDeImpacto(IntEnum):
    BAIXO = 1
    MEDIO = 2
    ALTO = 3
    CRITICO = 4


class EventoDeRisco(ABC):
    '''
        Categoria -> tipo de Evento (clima, geopolitico,etc)
        data inicio -> quando comecou o evento
        data fim -> quando acabou o evento
        nivel de impacto -> quanto o evento impacta na atracação
    '''

    def __init__(self, categoria: str, data_inicio: date, data_fim: date):
        if data_fim < data_inicio:
            raise ValueError("data_fim não pode ser anterior a data_inicio")
        self._categoria = categoria
        self._nivel_de_impacto = NivelDeImpacto.BAIXO
        self._data_inicio = data_inicio
        self._data_fim = data_fim

    def esta_ativo(self, data: date):
        data = data
        return self._data_inicio <= data and data <= self._data_fim

    @abstractmethod
    def bloqueia_atracacao(self, navio):
        pass

    @abstractmethod
    def bloqueia_atracacao(self, navio):
        pass


    def get_categoria(self):
        return self._categoria


    def set_categoria(self, valor: str) -> None:
        if not valor or not valor.strip():
            raise ValueError("categoria não pode ser vazia")
        self._categoria = valor


    def get_nivel_de_impacto(self):
        return self._nivel_de_impacto


    def set_nivel_de_impacto(self, valor: "NivelDeImpacto") -> None:
        if not isinstance(valor, NivelDeImpacto):
            raise TypeError(
                f"nivel_de_impacto deve ser do tipo NivelDeImpacto, recebeu {type(valor)}")
        self._nivel_de_impacto = valor


    def get_data_inicio(self):
        return self._data_inicio


    def set_data_inicio(self, valor: date) -> None:
        if valor > self._data_fim:
            raise ValueError("data_inicio não pode ser posterior a data_fim")
        self._data_inicio = valor


    def get_data_fim(self):
        return self._data_fim


    def set_data_fim(self, valor: date) -> None:
        if valor < self._data_inicio:
            raise ValueError("data_fim não pode ser anterior a data_inicio")
        self._data_fim = valor
