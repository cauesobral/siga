class Carga:
    __tipo : str
    __volume : float
    __origem : str
    __destino : str

    def __init__ (self, tipo, volume, origem, destino):
        self.__tipo = tipo
        self.__volume = volume
        self.__origem = origem
        self.__destino = destino