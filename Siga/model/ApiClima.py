from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import requests_cache
from retry_requests import retry  # type: ignore[import-untyped]

from CondicaoClimatica import CondicaoClimatica


class ApiClima:

    URL = "https://api.open-meteo.com/v1/forecast"
    VARIAVEIS = ["wind_speed_10m", "wind_gusts_10m", "wind_direction_10m",
                 "precipitation", "precipitation_probability"]

    def __init__(self, latitude: float = -23.9608, longitude: float = -46.3336,
                 sessao: Any = None) -> None:
        self._latitude = latitude
        self._longitude = longitude
        self._sessao: Any = sessao if sessao is not None else self.criar_sessao()

    def criar_sessao(self) -> Any:
        return retry(requests_cache.CachedSession(".cache", expire_after=3600),
                     retries=5, backoff_factor=0.2)

    def buscar_json(self) -> dict[str, Any]:
        params = {"latitude": self._latitude, "longitude": self._longitude,
                  "hourly": ",".join(self.VARIAVEIS),
                  "wind_speed_unit": "ms",
                  "timezone": "America/Sao_Paulo"}
        resposta = self._sessao.get(self.URL, params=params, timeout=15)
        resposta.raise_for_status()
        return resposta.json()  # type: ignore[no-any-return]

    def buscar_previsao(self) -> list[dict[str, str | float | None]]:
        horario = self.buscar_json()["hourly"]
        registros: list[dict[str, str | float | None]] = []
        for i, hora in enumerate(horario["time"]):
            registro: dict[str, str | float | None] = {"horario": hora}
            for variavel in self.VARIAVEIS:
                registro[variavel] = horario[variavel][i]
            registros.append(registro)
        return registros

    def buscar_previsao_json(self) -> str:
        return json.dumps(self.buscar_previsao(), ensure_ascii=False)

    def buscar_condicoes(self) -> list[CondicaoClimatica]:
        return [CondicaoClimatica.de_json(r) for r in self.buscar_previsao()]

    def condicao_em(self, horario: datetime) -> CondicaoClimatica | None:
        alvo = horario.replace(minute=0, second=0, microsecond=0)
        for condicao in self.buscar_condicoes():
            if condicao.get_horario().replace(tzinfo=None) == alvo.replace(tzinfo=None):
                return condicao
        return None


if __name__ == "__main__":
    for c in ApiClima().buscar_condicoes()[:24]:
        print(c.descricao(), "| bloqueia:", c.bloqueia_atracacao(None))  # type: ignore[arg-type]
