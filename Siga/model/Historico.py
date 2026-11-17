from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import ClassVar


@dataclass
class RegistroOperacional:
    timestamp: str
    tipo: str
    navio_nome: str
    berco_id: str


class Historico:
    _CAMINHO_PADRAO: ClassVar[str] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "historico.json"
    )

    def __init__(self, caminho: str | None = None) -> None:
        self._caminho = caminho or self._CAMINHO_PADRAO
        self._registros: list[RegistroOperacional] = self._carregar()

    def registrar(self, tipo: str, navio_nome: str, berco_id: str) -> None:
        self._registros.append(RegistroOperacional(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            tipo=tipo,
            navio_nome=navio_nome,
            berco_id=berco_id,
        ))
        self._salvar()

    def get_registros(self) -> list[RegistroOperacional]:
        return list(self._registros)

    def limpar(self) -> None:
        self._registros.clear()
        self._salvar()

    def _carregar(self) -> list[RegistroOperacional]:
        if not os.path.exists(self._caminho):
            return []
        try:
            with open(self._caminho, "r", encoding="utf-8") as f:
                return [RegistroOperacional(**d) for d in json.load(f)]
        except (json.JSONDecodeError, KeyError, TypeError):
            return []

    def _salvar(self) -> None:
        with open(self._caminho, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in self._registros], f,
                      ensure_ascii=False, indent=2)
