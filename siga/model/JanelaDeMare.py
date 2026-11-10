import json
from datetime import datetime

from ApiMare import ApiMare
from EventoDeRisco import EventoDeRisco, NivelDeImpacto

FOLGA_MINIMA_PERCENTUAL = 0.10  
LIMITES_MARE_BAIXA = [(0.3, NivelDeImpacto.ALTO), (0.6, NivelDeImpacto.MEDIO)]  


class JanelaDeMare(EventoDeRisco):
    
    def __init__(self, horario: datetime, altura_da_mare: float,
                 profundidade_canal: float):
        self._horario = horario
        self._altura_da_mare = altura_da_mare
        self._profundidade_canal = profundidade_canal
        super().__init__("mare", horario.date(), horario.date(),
                         self.classificar(altura_da_mare))

    @staticmethod
    def classificar(altura: float):
        for limite, nivel in LIMITES_MARE_BAIXA:
            if altura <= limite:
                return nivel
        return NivelDeImpacto.BAIXO

    @classmethod
    def de_json(cls, dados, profundidade_canal: float):
        if isinstance(dados, str):
            dados = json.loads(dados)
        return cls(datetime.fromisoformat(dados["horario"]),
                   float(dados["sea_level_height_msl"]), profundidade_canal)

    @classmethod
    def da_api(cls, horario: datetime, profundidade_canal: float,
               api: ApiMare):
        registro = api.registro_em(horario)
        if not registro or registro["sea_level_height_msl"] is None:
            return None
        return cls.de_json(registro, profundidade_canal)

    @classmethod
    def lista_da_api(cls, profundidade_canal: float,
                     api: ApiMare):
        return [cls.de_json(r, profundidade_canal)
                for r in api.buscar_previsao()
                if r["sea_level_height_msl"] is not None]

    def get_horario(self):
        return self._horario

    def get_altura_da_mare(self):
        return self._altura_da_mare


    def profundidade_disponivel(self):
        return self._profundidade_canal + self._altura_da_mare

    def folga_sob_quilha(self, navio):
        return self.profundidade_disponivel() - navio.get_calado()

    def permite_atracacao(self, navio):
        return self.folga_sob_quilha(navio) >= navio.get_calado() * FOLGA_MINIMA_PERCENTUAL

    def bloqueia_atracacao(self, navio):
        return not self.permite_atracacao(navio)

    def descricao(self):
        return (f"Maré {self._horario:%d/%m %H:%M}: {self._altura_da_mare:.2f} m, "
                f"profundidade disponível {self.profundidade_disponivel():.2f} m "
                f"(impacto {self.get_nivel_de_impacto().name})")
