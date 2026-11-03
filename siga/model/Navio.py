from abc import ABC, abstractmethod
from Carga import *

class Navio (ABC):
    __nome : str
    __calado : float
    __tamanho : float
    __cargaAtual : Carga
    __capacidade : float

    def __init__(self, nome, calado, tamanho, cargaAtual, capacidade):
        self.__nome = nome
        self.__calado = calado
        self.__tamanho = tamanho
        self.__cargaAtual = cargaAtual
        self.__capacidade = capacidade
    
    @abstractmethod
    def calcularCaladoMinimo():
        pass

    @abstractmethod
    def tempoEstimadoOperacao():
        pass

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
