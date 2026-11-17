from __future__ import annotations

from typing import TYPE_CHECKING

from StatusOperacional import StatusOperacional

if TYPE_CHECKING:
    from Navio import Navio


class Berco:
    _navio_atual: Navio | None

    def __init__(self, identificador: str, capacidade: float,
                 tipos_carga_aceita: list[str]) -> None:
        self._identificador = identificador
        self._capacidade = capacidade
        self._tipos_carga_aceita = tipos_carga_aceita
        self._status = StatusOperacional.LIVRE
        self._navio_atual = None

    def get_identificador(self) -> str:
        return self._identificador

    def get_capacidade(self) -> float:
        return self._capacidade

    def get_tipos_carga_aceita(self) -> list[str]:
        return self._tipos_carga_aceita

    def get_status(self) -> StatusOperacional:
        return self._status

    def get_navio_atual(self) -> Navio | None:
        return self._navio_atual

    def aceita_navio(self, navio: Navio) -> bool:
        return (self._status == StatusOperacional.LIVRE
                and navio.get_carga_atual().get_tipo().lower()
                in [t.lower() for t in self._tipos_carga_aceita]
                and navio.get_tamanho() <= self._capacidade)

    def ocupar(self, navio: Navio) -> None:
        if not self.aceita_navio(navio):
            raise ValueError("Berço não pode receber este navio")
        self._navio_atual = navio
        self._status = StatusOperacional.OCUPADO

    def liberar(self) -> None:
        self._navio_atual = None
        self._status = StatusOperacional.LIVRE
