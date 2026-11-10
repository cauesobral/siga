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

    def get_tipo(self):
        return self.__tipo

    def get_volume(self):
        return self.__volume

    def get_origem(self):
        return self.__origem

    def get_destino(self):
        return self.__destino
