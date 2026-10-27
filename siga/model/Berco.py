from enum import Enum

class StatusOperacional(Enum):
    LIVRE = "livre"
    OCUPADO = "ocupado"
    MANUTENCAO = "manutencao"

class Berco:
    def __init__(self, identificador: str, capacidade: float, tipos_carga_aceita: list[str]):
        self._identificador = identificador
        self._capacidade = capacidade
        self._tipos_carga_aceita = tipos_carga_aceita
        self._status = StatusOperacional.LIVRE
        self._navio_atual = None

    def get_status(self):
        return self._status

    def aceita_navio(self, navio):
        return (self._status == StatusOperacional.LIVRE
                and navio.carga_atual.tipo in self._tipos_carga_aceita
                and navio.tamanho <= self._capacidade)

    def ocupar(self, navio):
        if not self.aceita_navio(navio):
            raise ValueError("Berço não pode receber este navio")
        self._navio_atual = navio
        self._status = StatusOperacional.OCUPADO

    def liberar(self):
        self._navio_atual = None
        self._status = StatusOperacional.LIVRE