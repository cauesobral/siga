from abc import ABCMeta, abstractmethod
from datetime import date

class EventoDeRisco(metaclass=ABCMeta):
    categoria: str
    nivelDeImpacto:str
    dataInicio:date
    dataFim:date
    