import json
from datetime import datetime
import requests_cache
from retry_requests import retry

class ApiMare:

    URL = "https://marine-api.open-meteo.com/v1/marine"
    VARIAVEIS = ["wave_height", "wave_direction", "wave_period",
                 "sea_level_height_msl"]

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
                  "forecast_days": 7,
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

    def registro_em(self, horario: datetime):
        alvo = horario.replace(minute=0, second=0, microsecond=0, tzinfo=None)
        for registro in self.buscar_previsao():
            if datetime.fromisoformat(registro["horario"]).replace(tzinfo=None) == alvo:
                return registro
        return None


if __name__ == "__main__":
    for registro in ApiMare().buscar_previsao()[:24]:
        print(registro)
