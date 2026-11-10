from Carga import Carga

class Navio:
    __nome : str
    __calado : float
    __tamanho : float
    __cargaAtual : Carga
    __capacidade : float

    TAXA_POR_HORA = {"granel": 2000, "petróleo": 3000, "contêineres": 60}

    def __init__(self, nome, calado, tamanho, cargaAtual, capacidade):
        self.__nome = nome
        self.__calado = calado
        self.__tamanho = tamanho
        self.__cargaAtual = cargaAtual
        self.__capacidade = capacidade

    def calcularCaladoMinimo(self):
        return self.__calado

    def tempoEstimadoOperacao(self):
        tipo = self.__cargaAtual.get_tipo().strip().lower()
        if tipo not in self.TAXA_POR_HORA:
            raise ValueError(f"sem taxa de movimentação definida para o tipo '{tipo}'")
        return self.__cargaAtual.get_volume() / self.TAXA_POR_HORA[tipo]

    def get_nome(self):
        return self.__nome

    def get_calado(self):
        return self.__calado

    def get_tamanho(self):
        return self.__tamanho

    def get_carga_atual(self):
        return self.__cargaAtual

    def get_capacidade(self):
        return self.__capacidade
