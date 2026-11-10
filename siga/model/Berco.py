from StatusOperacional import StatusOperacional

class Berco:
    def __init__(self, identificador: str, capacidade: float, tipos_carga_aceita: list[str]):
        self._identificador = identificador
        self._capacidade = capacidade
        self._tipos_carga_aceita = tipos_carga_aceita
        self._status = StatusOperacional.LIVRE
        self._navio_atual = None

    def get_identificador(self):
        return self._identificador

    def get_capacidade(self):
        return self._capacidade

    def get_tipos_carga_aceita(self):
        return self._tipos_carga_aceita

    def get_status(self):
        return self._status

    def get_navio_atual(self):
        return self._navio_atual

    def aceita_navio(self, navio):
        return (self._status == StatusOperacional.LIVRE
                and navio.get_carga_atual().get_tipo().lower()
                in [t.lower() for t in self._tipos_carga_aceita]
                and navio.get_tamanho() <= self._capacidade)

    def ocupar(self, navio):
        if not self.aceita_navio(navio):
            raise ValueError("Berço não pode receber este navio")
        self._navio_atual = navio
        self._status = StatusOperacional.OCUPADO

    def liberar(self):
        self._navio_atual = None
        self._status = StatusOperacional.LIVRE