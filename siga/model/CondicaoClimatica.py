from hashlib import new
from EventoDeRisco import * 

class CondicaoClimatica(EventoDeRisco, NivelDeImpacto):

    def bloqueia_atracacao_ventania(self,ventoSpeed):
        if ventoSpeed <= 5:
            self._nivel_de_impacto = NivelDeImpacto.BAIXO
        elif ventoSpeed < 7:
            self._nivel_de_impacto = NivelDeImpacto.MEDIO
        elif ventoSpeed < 11:
            self._nivel_de_impacto = NivelDeImpacto.ALTO
        else:
            self._nivel_de_impacto = NivelDeImpacto.CRITICO

