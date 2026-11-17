class Carga:
    __tipo: str
    __volume: float
    __origem: str
    __destino: str

    def __init__(self, tipo: str, volume: float, origem: str, destino: str) -> None:
        self.__tipo = tipo
        self.__volume = volume
        self.__origem = origem
        self.__destino = destino

    def get_tipo(self) -> str:
        return self.__tipo

    def get_volume(self) -> float:
        return self.__volume

    def get_origem(self) -> str:
        return self.__origem

    def get_destino(self) -> str:
        return self.__destino
