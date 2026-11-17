from __future__ import annotations

from Berco import Berco
from EventoDeRisco import EventoDeRisco, NivelDeImpacto
from Historico import Historico
from Navio import Navio
from StatusOperacional import StatusOperacional


class GerenciadorDeAtracacao:

    def __init__(self, historico: Historico) -> None:
        self._historico = historico

    def status_navio(self, navio: Navio, eventos: list[EventoDeRisco]) -> str:
        if any(e.bloqueia_atracacao(navio) for e in eventos if e.esta_ativo()):
            return "Risco Alto"
        if any(e.get_nivel_de_impacto() >= NivelDeImpacto.MEDIO for e in eventos if e.esta_ativo()):
            return "Atenção"
        return "Normal"

    def atracar(self, navio: Navio, berco: Berco, fila: list[Navio]) -> None:
        # remove da fila primeiro: se o navio não estiver lá, falha antes de ocupar o berço
        fila.remove(navio)
        berco.ocupar(navio)
        self._historico.registrar("ATRACACAO", navio.get_nome(), berco.get_identificador())

    def liberar(self, berco: Berco) -> None:
        navio = berco.get_navio_atual()
        navio_nome = navio.get_nome() if navio else "desconhecido"
        self._historico.registrar("LIBERACAO", navio_nome, berco.get_identificador())
        berco.liberar()

    def avancar_turno(self, bercos: list[Berco]) -> int:
        liberados = 0
        for berco in bercos:
            if berco.get_status() == StatusOperacional.OCUPADO:
                self.liberar(berco)
                liberados += 1
        return liberados
