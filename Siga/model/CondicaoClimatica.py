from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from EventoDeRisco import EventoDeRisco, NivelDeImpacto

if TYPE_CHECKING:
    from Navio import Navio


class CondicaoClimatica(EventoDeRisco):
    LIMITES_VENTO: list[tuple[float, NivelDeImpacto]] = [
        (5, NivelDeImpacto.BAIXO), (7, NivelDeImpacto.MEDIO), (11, NivelDeImpacto.ALTO),
    ]
    LIMITES_CHUVA: list[tuple[float, NivelDeImpacto]] = [
        (2.5, NivelDeImpacto.BAIXO), (7.6, NivelDeImpacto.MEDIO), (50, NivelDeImpacto.ALTO),
    ]

    def __init__(self, horario: datetime, velocidade_vento: float,
                 precipitacao: float = 0.0, prob_chuva: float = 0.0) -> None:
        super().__init__("clima", horario.date(), horario.date())
        self._horario = horario
        self._velocidade_vento = velocidade_vento
        self._precipitacao = precipitacao
        self._prob_chuva = prob_chuva
        self.set_nivel_de_impacto(max(self.classificar_vento(velocidade_vento),
                                      self.classificar_chuva(precipitacao)))

    @staticmethod
    def classificar(valor: float, limites: list[tuple[float, NivelDeImpacto]]) -> NivelDeImpacto:
        for limite, nivel in limites:
            if valor <= limite:
                return nivel
        return NivelDeImpacto.CRITICO

    @staticmethod
    def classificar_vento(velocidade: float) -> NivelDeImpacto:
        return CondicaoClimatica.classificar(velocidade, CondicaoClimatica.LIMITES_VENTO)

    @staticmethod
    def classificar_chuva(precipitacao: float) -> NivelDeImpacto:
        return CondicaoClimatica.classificar(precipitacao, CondicaoClimatica.LIMITES_CHUVA)

    @classmethod
    def de_json(cls, dados: str | dict[str, Any]) -> CondicaoClimatica:
        parsed: dict[str, Any] = json.loads(dados) if isinstance(dados, str) else dados
        return cls(
            horario=datetime.fromisoformat(parsed["horario"]),
            velocidade_vento=float(parsed["wind_speed_10m"]),
            precipitacao=float(parsed.get("precipitation") or 0.0),
            prob_chuva=float(parsed.get("precipitation_probability") or 0.0),
        )

    def bloqueia_atracacao(self, navio: Navio) -> bool:
        return self.get_nivel_de_impacto() >= NivelDeImpacto.ALTO

    def descricao(self) -> str:
        return (f"{self._horario:%d/%m %H:%M}: vento {self._velocidade_vento:.1f} m/s, "
                f"chuva {self._precipitacao:.1f} mm "
                f"(impacto {self.get_nivel_de_impacto().name})")

    def get_horario(self) -> datetime:
        return self._horario

    def get_velocidade_vento(self) -> float:
        return self._velocidade_vento

    def get_precipitacao(self) -> float:
        return self._precipitacao

    def get_prob_chuva(self) -> float:
        return self._prob_chuva
