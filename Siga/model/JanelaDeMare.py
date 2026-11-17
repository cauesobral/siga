from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ApiMare import ApiMare
from EventoDeRisco import EventoDeRisco, NivelDeImpacto

if TYPE_CHECKING:
    from Navio import Navio

FOLGA_MINIMA_PERCENTUAL: float = 0.10
LIMITES_MARE_BAIXA: list[tuple[float, NivelDeImpacto]] = [
    (0.3, NivelDeImpacto.ALTO), (0.6, NivelDeImpacto.MEDIO),
]


class JanelaDeMare(EventoDeRisco):

    def __init__(self, horario: datetime, altura_da_mare: float,
                 profundidade_canal: float) -> None:
        self._horario = horario
        self._altura_da_mare = altura_da_mare
        self._profundidade_canal = profundidade_canal
        super().__init__("mare", horario.date(), horario.date(),
                         self.classificar(altura_da_mare))

    @staticmethod
    def classificar(altura: float) -> NivelDeImpacto:
        for limite, nivel in LIMITES_MARE_BAIXA:
            if altura <= limite:
                return nivel
        return NivelDeImpacto.BAIXO

    @classmethod
    def de_json(cls, dados: str | dict[str, Any], profundidade_canal: float) -> JanelaDeMare:
        parsed: dict[str, Any] = json.loads(dados) if isinstance(dados, str) else dados
        return cls(datetime.fromisoformat(parsed["horario"]),
                   float(parsed["sea_level_height_msl"]), profundidade_canal)

    @classmethod
    def da_api(cls, horario: datetime, profundidade_canal: float,
               api: ApiMare) -> JanelaDeMare | None:
        registro = api.registro_em(horario)
        if not registro or registro["sea_level_height_msl"] is None:
            return None
        return cls.de_json(registro, profundidade_canal)

    @classmethod
    def lista_da_api(cls, profundidade_canal: float,
                     api: ApiMare) -> list[JanelaDeMare]:
        return [cls.de_json(r, profundidade_canal)
                for r in api.buscar_previsao()
                if r["sea_level_height_msl"] is not None]

    def get_horario(self) -> datetime:
        return self._horario

    def get_altura_da_mare(self) -> float:
        return self._altura_da_mare

    def profundidade_disponivel(self) -> float:
        return self._profundidade_canal + self._altura_da_mare

    def folga_sob_quilha(self, navio: Navio) -> float:
        return self.profundidade_disponivel() - navio.get_calado()

    def permite_atracacao(self, navio: Navio) -> bool:
        return self.folga_sob_quilha(navio) >= navio.get_calado() * FOLGA_MINIMA_PERCENTUAL

    def bloqueia_atracacao(self, navio: Navio) -> bool:
        return not self.permite_atracacao(navio)

    def descricao(self) -> str:
        return (f"Maré {self._horario:%d/%m %H:%M}: {self._altura_da_mare:.2f} m, "
                f"profundidade disponível {self.profundidade_disponivel():.2f} m "
                f"(impacto {self.get_nivel_de_impacto().name})")
