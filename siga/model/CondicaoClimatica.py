import json
from datetime import date, datetime

from EventoDeRisco import EventoDeRisco, NivelDeImpacto


class CondicaoClimatica(EventoDeRisco):
    '''
        Condição do tempo em um horário, vinda da ApiClima (JSON da Open-Meteo).
        velocidade_vento -> m/s (a ApiClima pede a API nessa unidade)
        precipitacao -> mm na hora
        prob_chuva -> % de chance de chuva
    '''

    # vento (m/s): até 5 BAIXO, até 7 MEDIO, até 11 ALTO, acima CRITICO
    LIMITES_VENTO = [(5, NivelDeImpacto.BAIXO), (7, NivelDeImpacto.MEDIO),
                     (11, NivelDeImpacto.ALTO)]
    # chuva (mm/h): abaixo de 2.5 BAIXO, até 7.6 MEDIO, até 50 ALTO, acima CRITICO
    LIMITES_CHUVA = [(2.5, NivelDeImpacto.BAIXO), (7.6, NivelDeImpacto.MEDIO),
                     (50, NivelDeImpacto.ALTO)]

    def __init__(self, horario: datetime, velocidade_vento: float,
                 precipitacao: float = 0.0, prob_chuva: float = 0.0):
        super().__init__("clima", horario.date(), horario.date())
        self._horario = horario
        self._velocidade_vento = velocidade_vento
        self._precipitacao = precipitacao
        self._prob_chuva = prob_chuva
        # o pior entre vento e chuva define o impacto
        self.set_nivel_de_impacto(max(self.classificar_vento(velocidade_vento),
                                      self.classificar_chuva(precipitacao)))

    @staticmethod
    def classificar(valor: float, limites):
        for limite, nivel in limites:
            if valor <= limite:
                return nivel
        return NivelDeImpacto.CRITICO

    @staticmethod
    def classificar_vento(velocidade: float):
        return CondicaoClimatica.classificar(velocidade, CondicaoClimatica.LIMITES_VENTO)

    @staticmethod
    def classificar_chuva(precipitacao: float):
        return CondicaoClimatica.classificar(precipitacao, CondicaoClimatica.LIMITES_CHUVA)

    @classmethod
    def de_json(cls, dados):
        if isinstance(dados, str):
            dados = json.loads(dados)
        return cls(horario=datetime.fromisoformat(dados["horario"]),
                   velocidade_vento=float(dados["wind_speed_10m"]),
                   precipitacao=float(dados.get("precipitation") or 0.0),
                   prob_chuva=float(dados.get("precipitation_probability") or 0.0))

    def bloqueia_atracacao(self, navio):
        return self.get_nivel_de_impacto() >= NivelDeImpacto.ALTO

    def descricao(self):
        return (f"Clima {self._horario:%d/%m %H:%M}: vento {self._velocidade_vento:.1f} m/s, "
                f"chuva {self._precipitacao:.1f} mm "
                f"(impacto {self.get_nivel_de_impacto().name})")

    def get_horario(self):
        return self._horario

    def get_velocidade_vento(self):
        return self._velocidade_vento

    def get_precipitacao(self):
        return self._precipitacao

    def get_prob_chuva(self):
        return self._prob_chuva
