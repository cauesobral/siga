from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date
from typing import Any

from Berco import Berco
from EventoDeRisco import EventoDeRisco
from JanelaDeMare import JanelaDeMare
from Navio import Navio


class PoliticaDeAtracacao(ABC):

    def __init__(self, nome: str, descricao: str) -> None:
        self._nome = nome
        self._descricao = descricao

    @abstractmethod
    def chave_de_ordenacao(self, navio: Navio, eventos: Sequence[EventoDeRisco]) -> Any:
        pass

    def ordenar_fila(self, fila: Sequence[Navio],
                     eventos: Sequence[EventoDeRisco] = ()) -> list[Navio]:
        return sorted(fila, key=lambda navio: self.chave_de_ordenacao(navio, eventos))

    @staticmethod
    def eventos_ativos(eventos: Sequence[EventoDeRisco], data: date) -> list[EventoDeRisco]:
        return [e for e in eventos if e.esta_ativo(data)]

    def bloqueios(self, navio: Navio, eventos: Sequence[EventoDeRisco],
                  data: date) -> list[EventoDeRisco]:
        return [e for e in self.eventos_ativos(eventos, data) if e.bloqueia_atracacao(navio)]

    def motivos_de_bloqueio(self, navio: Navio, eventos: Sequence[EventoDeRisco],
                            data: date) -> list[str]:
        return [e.descricao() for e in self.bloqueios(navio, eventos, data)]

    def pode_atracar(self, navio: Navio, berco: Berco,
                     eventos: Sequence[EventoDeRisco], data: date | None) -> bool:
        return berco.aceita_navio(navio) and not self.bloqueios(
            navio, eventos, data or date.today())

    def proxima_atracacao(self, fila: Sequence[Navio], bercos: Sequence[Berco],
                          eventos: Sequence[EventoDeRisco] = (),
                          data: date | None = None) -> tuple[Navio, Berco] | None:
        for navio in self.ordenar_fila(fila, eventos):
            for berco in bercos:
                if self.pode_atracar(navio, berco, eventos, data):
                    return navio, berco
        return None

    def get_nome(self) -> str:
        return self._nome

    def get_descricao(self) -> str:
        return self._descricao

    def __str__(self) -> str:
        return self._nome


class PorOrdemDeChegada(PoliticaDeAtracacao):
    def __init__(self) -> None:
        super().__init__("Por ordem de chegada",
                         "Mantém a fila na ordem de chegada.")

    def chave_de_ordenacao(self, navio: Navio, eventos: Sequence[EventoDeRisco]) -> int:
        return 0


class PorPrioridadeDeCarga(PoliticaDeAtracacao):
    PRIORIDADE_POR_TIPO: dict[str, int] = {"petróleo": 0, "granel": 1, "contêineres": 2}
    PRIORIDADE_PADRAO: int = 9

    def __init__(self, prioridade_por_tipo: dict[str, int]) -> None:
        super().__init__("Por prioridade de carga",
                         "Prioriza cargas críticas, ex.: petróleo.")
        self._prioridade_por_tipo = prioridade_por_tipo or dict(self.PRIORIDADE_POR_TIPO)

    def chave_de_ordenacao(self, navio: Navio, eventos: Sequence[EventoDeRisco]) -> int:
        tipo = navio.get_carga_atual().get_tipo().strip().lower()
        return self._prioridade_por_tipo.get(tipo, self.PRIORIDADE_PADRAO)


class PorMare(PoliticaDeAtracacao):

    def __init__(self) -> None:
        super().__init__("Por maré",
                         "Prioriza navios de acordo com janelas de maré segura.")

    @staticmethod
    def janela(eventos: Sequence[EventoDeRisco]) -> JanelaDeMare | None:
        return next((e for e in eventos if isinstance(e, JanelaDeMare) and e.esta_ativo()), None)

    def chave_de_ordenacao(self, navio: Navio,
                           eventos: Sequence[EventoDeRisco]) -> tuple[bool, float]:
        janela = self.janela(eventos)
        bloqueado = janela.bloqueia_atracacao(navio) if janela else False
        return (bloqueado, -navio.get_calado())
