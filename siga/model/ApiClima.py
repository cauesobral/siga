import json
from datetime import datetime
import requests_cache
from retry_requests import retry

from CondicaoClimatica import CondicaoClimatica


class ApiClima:

    URL = "https://api.open-meteo.com/v1/forecast"
    VARIAVEIS = ["wind_speed_10m", "wind_gusts_10m", "wind_direction_10m",
                 "precipitation", "precipitation_probability"]

    def __init__(self, latitude: float = -23.9608, longitude: float = -46.3336,
                 sessao=None):
        self._latitude = latitude
        self._longitude = longitude
        self._sessao = self.criar_sessao()

    def criar_sessao(self):
        return retry(requests_cache.CachedSession(".cache", expire_after=3600),
                     retries=5, backoff_factor=0.2)

    def buscar_json(self):
        params = {"latitude": self._latitude, "longitude": self._longitude,
                  "hourly": ",".join(self.VARIAVEIS),
                  "wind_speed_unit": "ms",
                  "timezone": "America/Sao_Paulo"}
        resposta = self._sessao.get(self.URL, params=params, timeout=15)
        resposta.raise_for_status()
        return resposta.json()

    def buscar_previsao(self):
        horario = self.buscar_json()["hourly"]
        registros = []
        for i, hora in enumerate(horario["time"]):
            registro = {"horario": hora}
            for variavel in self.VARIAVEIS:
                registro[variavel] = horario[variavel][i]
            registros.append(registro)
        return registros

    def buscar_previsao_json(self):
        return json.dumps(self.buscar_previsao(), ensure_ascii=False)

    def buscar_condicoes(self):
        return [CondicaoClimatica.de_json(r) for r in self.buscar_previsao()]

    def condicao_em(self, horario: datetime) -> CondicaoClimatica | None:
        alvo = horario.replace(minute=0, second=0, microsecond=0)
        for condicao in self.buscar_condicoes():
            if condicao.get_horario().replace(tzinfo=None) == alvo.replace(tzinfo=None):
                return condicao
        return None


if __name__ == "__main__":
    for c in ApiClima().buscar_condicoes()[:24]:
        print(c.descricao(), "| bloqueia:", c.bloqueia_atracacao(None))
