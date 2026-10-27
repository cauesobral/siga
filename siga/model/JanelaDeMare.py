from datetime import datetime

from EventoDeRisco import EventoDeRisco, NivelDeImpacto

FOLGA_MINIMA_PERCENTUAL = 0.10  
LIMITES_MARE_BAIXA = [(0.3, NivelDeImpacto.ALTO), (0.6, NivelDeImpacto.MEDIO)]  


class JanelaDeMare(EventoDeRisco):
    
    def __init__(self, horario: datetime, altura_da_mare: float,
                 profundidade_canal: float):
        self._horario = horario
        self._altura_da_mare = altura_da_mare
        self._profundidade_canal = profundidade_canal
        super().__init__("mare", self.classificar(altura_da_mare),
                         horario.date(), horario.date())

    def classificar(altura: float):
        for limite, nivel in LIMITES_MARE_BAIXA:
            if altura <= limite:
                return nivel
        return NivelDeImpacto.BAIXO

    def get_horario(self):
        return self._horario

    def get_altura_da_mare(self):
        return self._altura_da_mare


    def profundidade_disponivel(self):
        return self._profundidade_canal + self._altura_da_mare

    def folga_sob_quilha(self, navio):
        return self.profundidade_disponivel - navio.calado

    def permite_atracacao(self, navio):
        return self.folga_sob_quilha(navio) >= navio.calado * FOLGA_MINIMA_PERCENTUAL

    def bloqueia_atracacao(self, navio):
        return not self.permite_atracacao(navio)

    def descricao(self):
        return (f"Maré {self._horario:%d/%m %H:%M}: {self._altura_da_mare:.2f} m, "
                f"profundidade disponível {self.profundidade_disponivel:.2f} m "
                f"(impacto {self.nivel_de_impacto.name})")