from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from Carga import Carga


@dataclass(frozen=True)
class Navio:
    nome: str
    calado: float
    tamanho: float
    carga_atual: Carga
    capacidade: float

    TAXA_POR_HORA: ClassVar[dict[str, int]] = {
        "granel": 2000, "petróleo": 3000, "contêineres": 60
    }

    def calcular_calado_minimo(self) -> float:
        return self.calado

    def tempo_estimado_operacao(self) -> float:
        tipo = self.carga_atual.get_tipo().strip().lower()
        if tipo not in self.TAXA_POR_HORA:
            raise ValueError(f"sem taxa de movimentação definida para o tipo '{tipo}'")
        return self.carga_atual.get_volume() / self.TAXA_POR_HORA[tipo]

    def get_nome(self) -> str:
        return self.nome

    def get_calado(self) -> float:
        return self.calado

    def get_tamanho(self) -> float:
        return self.tamanho

    def get_carga_atual(self) -> Carga:
        return self.carga_atual

    def get_capacidade(self) -> float:
        return self.capacidade
