from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Navio import Navio


class NivelDeImpacto(IntEnum):
    BAIXO = 1
    MEDIO = 2
    ALTO = 3
    CRITICO = 4


class EventoDeRisco(ABC):
    def __init__(self, categoria: str, data_inicio: date, data_fim: date,
                 nivel_de_impacto: NivelDeImpacto = NivelDeImpacto.BAIXO) -> None:
        if data_fim < data_inicio:
            raise ValueError("data_fim não pode ser anterior a data_inicio")
        self._categoria = categoria
        self._data_inicio = data_inicio
        self._data_fim = data_fim
        self._nivel_de_impacto = NivelDeImpacto.BAIXO
        self.set_nivel_de_impacto(nivel_de_impacto)

    def esta_ativo(self, data: date | None = None) -> bool:
        data = data or date.today()
        return self._data_inicio <= data <= self._data_fim

    @abstractmethod
    def bloqueia_atracacao(self, navio: Navio) -> bool:
        pass

    @abstractmethod
    def descricao(self) -> str:
        pass

    def get_categoria(self) -> str:
        return self._categoria

    def set_categoria(self, valor: str) -> None:
        if not valor or not valor.strip():
            raise ValueError("categoria não pode ser vazia")
        self._categoria = valor

    def get_nivel_de_impacto(self) -> NivelDeImpacto:
        return self._nivel_de_impacto

    def set_nivel_de_impacto(self, valor: NivelDeImpacto) -> None:
        if not isinstance(valor, NivelDeImpacto):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"nivel_de_impacto deve ser NivelDeImpacto, não {type(valor).__name__}")
        self._nivel_de_impacto = valor

    def get_data_inicio(self) -> date:
        return self._data_inicio

    def set_data_inicio(self, valor: date) -> None:
        if valor > self._data_fim:
            raise ValueError("data_inicio não pode ser posterior a data_fim")
        self._data_inicio = valor

    def get_data_fim(self) -> date:
        return self._data_fim

    def set_data_fim(self, valor: date) -> None:
        if valor < self._data_inicio:
            raise ValueError("data_fim não pode ser anterior a data_inicio")
        self._data_fim = valor
