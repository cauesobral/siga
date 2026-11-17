from __future__ import annotations

import json
import os
from typing import Any

from Berco import Berco
from Carga import Carga
from Navio import Navio

_PASTA: str = os.path.dirname(os.path.abspath(__file__))

# _CAMINHO_PADRAO é imutável; CAMINHO pode ser sobrescrito por main.py após login
_CAMINHO_PADRAO: str = os.path.join(_PASTA, "info.json")
CAMINHO: str = _CAMINHO_PADRAO

_ARQUIVOS_POR_PORTO: dict[str, str] = {
    "Porto de Santos":            os.path.join(_PASTA, "info.json"),
    "Porto do Rio de Janeiro":    os.path.join(_PASTA, "info_rio.json"),
    "Porto de Paranaguá":         os.path.join(_PASTA, "info_paranagua.json"),
    "Porto de Suape":             os.path.join(_PASTA, "info_suape.json"),
}


def caminho_por_porto(porto: str) -> str:
    return _ARQUIVOS_POR_PORTO.get(porto, _CAMINHO_PADRAO)

_NAVIOS_PADRAO: list[dict[str, Any]] = [
    # Contêineres
    {"nome": "MSC Aurora",          "calado": 12.5, "tamanho": 300, "carga_tipo": "Contêineres",
     "carga_volume": 4800,  "carga_origem": "Santos",    "carga_destino": "Roterdã",    "capacidade":  6000},
    {"nome": "Atlântico I",         "calado": 10.9, "tamanho": 260, "carga_tipo": "Contêineres",
     "carga_volume": 3000,  "carga_origem": "Santos",    "carga_destino": "Hamburgo",   "capacidade":  4000},
    {"nome": "Holandês Voador",     "calado": 10.0, "tamanho": 400, "carga_tipo": "Contêineres",
     "carga_volume": 2000,  "carga_origem": "Holanda",   "carga_destino": "França",     "capacidade": 10000},
    {"nome": "Maersk Sentosa",      "calado": 13.2, "tamanho": 366, "carga_tipo": "Contêineres",
     "carga_volume": 5500,  "carga_origem": "Singapura", "carga_destino": "Santos",     "capacidade":  7200},
    {"nome": "CMA CGM Marco Polo",  "calado": 13.5, "tamanho": 396, "carga_tipo": "Contêineres",
     "carga_volume": 6200,  "carga_origem": "Xangai",    "carga_destino": "Santos",     "capacidade":  8000},
    {"nome": "Ever Given",          "calado": 14.5, "tamanho": 400, "carga_tipo": "Contêineres",
     "carga_volume": 7200,  "carga_origem": "Hong Kong", "carga_destino": "Roterdã",    "capacidade":  9500},
    {"nome": "CSCL Globe",          "calado": 13.8, "tamanho": 400, "carga_tipo": "Contêineres",
     "carga_volume": 6800,  "carga_origem": "Tianjin",   "carga_destino": "Hamburgo",   "capacidade":  9000},
    {"nome": "MOL Triumph",         "calado": 12.0, "tamanho": 400, "carga_tipo": "Contêineres",
     "carga_volume": 5900,  "carga_origem": "Kobe",      "carga_destino": "Santos",     "capacidade":  7800},
    {"nome": "Hapag-Lloyd Callao",  "calado": 11.5, "tamanho": 335, "carga_tipo": "Contêineres",
     "carga_volume": 4200,  "carga_origem": "Callao",    "carga_destino": "Santos",     "capacidade":  5500},
    {"nome": "NYK Argus",           "calado": 10.8, "tamanho": 290, "carga_tipo": "Contêineres",
     "carga_volume": 3500,  "carga_origem": "Yokohama",  "carga_destino": "Paranaguá",  "capacidade":  4800},
    {"nome": "ZIM Integrated",      "calado": 11.2, "tamanho": 300, "carga_tipo": "Contêineres",
     "carga_volume": 3800,  "carga_origem": "Haifa",     "carga_destino": "Rio de Janeiro", "capacidade": 5000},

    # Petróleo
    {"nome": "Petro Santos",        "calado": 13.8, "tamanho": 250, "carga_tipo": "Petróleo",
     "carga_volume": 90000, "carga_origem": "Santos",    "carga_destino": "Lisboa",     "capacidade": 120000},
    {"nome": "Jahre Viking",        "calado": 24.6, "tamanho": 458, "carga_tipo": "Petróleo",
     "carga_volume": 280000,"carga_origem": "Golfo Pérsico","carga_destino": "Santos",  "capacidade": 320000},
    {"nome": "TI Oceania",          "calado": 22.0, "tamanho": 380, "carga_tipo": "Petróleo",
     "carga_volume": 200000,"carga_origem": "Ras Tanura", "carga_destino": "Itaqui",    "capacidade": 240000},
    {"nome": "Euronav Sienna",      "calado": 20.5, "tamanho": 333, "carga_tipo": "Petróleo",
     "carga_volume": 150000,"carga_origem": "Milford Haven","carga_destino": "Santos",  "capacidade": 180000},
    {"nome": "Crude Equinor",       "calado": 18.0, "tamanho": 310, "carga_tipo": "Petróleo",
     "carga_volume": 100000,"carga_origem": "Bergen",    "carga_destino": "Itajaí",     "capacidade": 130000},
    {"nome": "Teekay Petrolia",     "calado": 15.2, "tamanho": 274, "carga_tipo": "Petróleo",
     "carga_volume":  80000,"carga_origem": "Aberdeen",  "carga_destino": "Paranaguá",  "capacidade": 100000},
    {"nome": "Frontline Nordic",    "calado": 16.8, "tamanho": 290, "carga_tipo": "Petróleo",
     "carga_volume": 110000,"carga_origem": "Oslo",      "carga_destino": "Santos",     "capacidade": 140000},
    {"nome": "BW Odin",             "calado": 14.0, "tamanho": 250, "carga_tipo": "Petróleo",
     "carga_volume":  70000,"carga_origem": "Cingapura", "carga_destino": "Santos",     "capacidade":  90000},

    # Granel
    {"nome": "Graneleiro Sul",      "calado": 11.2, "tamanho": 220, "carga_tipo": "Granel",
     "carga_volume": 50000, "carga_origem": "Santos",    "carga_destino": "Xangai",     "capacidade":  60000},
    {"nome": "Vale Brasil",         "calado": 23.0, "tamanho": 362, "carga_tipo": "Granel",
     "carga_volume": 380000,"carga_origem": "Ponta da Madeira","carga_destino": "Qingdao","capacidade": 400000},
    {"nome": "Berge Stahl",         "calado": 22.5, "tamanho": 342, "carga_tipo": "Granel",
     "carga_volume": 350000,"carga_origem": "Ponta da Madeira","carga_destino": "Rotterdam","capacidade": 380000},
    {"nome": "Pacific Basin Pioneer","calado": 12.5, "tamanho": 229, "carga_tipo": "Granel",
     "carga_volume":  70000,"carga_origem": "Vitória",   "carga_destino": "Xangai",     "capacidade":  82000},
    {"nome": "Star Bulk Polaris",   "calado": 14.0, "tamanho": 245, "carga_tipo": "Granel",
     "carga_volume": 100000,"carga_origem": "Tubarão",   "carga_destino": "Tianjin",    "capacidade": 120000},
    {"nome": "Golden Ocean Balder", "calado": 13.5, "tamanho": 235, "carga_tipo": "Granel",
     "carga_volume":  85000,"carga_origem": "Vitória",   "carga_destino": "Mombasa",    "capacidade": 100000},
    {"nome": "Oldendorff Endeavour","calado": 12.0, "tamanho": 215, "carga_tipo": "Granel",
     "carga_volume":  60000,"carga_origem": "Paranaguá", "carga_destino": "Busan",      "capacidade":  75000},
    {"nome": "Cargill Panamax",     "calado": 11.8, "tamanho": 225, "carga_tipo": "Granel",
     "carga_volume":  65000,"carga_origem": "Santos",    "carga_destino": "Cairo",      "capacidade":  78000},
    {"nome": "BHP Atlantic",        "calado": 15.5, "tamanho": 275, "carga_tipo": "Granel",
     "carga_volume": 150000,"carga_origem": "Ponta da Madeira","carga_destino": "Xangai","capacidade": 175000},
    {"nome": "Rio Tinto Voyager",   "calado": 16.0, "tamanho": 290, "carga_tipo": "Granel",
     "carga_volume": 170000,"carga_origem": "Vitória",   "carga_destino": "Dalian",     "capacidade": 190000},
    {"nome": "Nippon Steel Maru",   "calado": 13.0, "tamanho": 230, "carga_tipo": "Granel",
     "carga_volume":  75000,"carga_origem": "Tubarão",   "carga_destino": "Nagoya",     "capacidade":  90000},
]

_BERCOS_PADRAO: list[dict[str, Any]] = [
    {"identificador": f"B{i}", "capacidade": 320.0,
     "tipos_carga_aceita": ["Contêineres", "Granel", "Petróleo"]}
    for i in range(1, 10)
]


def _navio_para_dict(n: Navio) -> dict[str, Any]:
    c = n.get_carga_atual()
    return {
        "nome": n.get_nome(), "calado": n.get_calado(), "tamanho": n.get_tamanho(),
        "carga_tipo": c.get_tipo(), "carga_volume": c.get_volume(),
        "carga_origem": c.get_origem(), "carga_destino": c.get_destino(),
        "capacidade": n.get_capacidade(),
    }


def _berco_para_dict(b: Berco) -> dict[str, Any]:
    return {
        "identificador": b.get_identificador(),
        "capacidade": b.get_capacidade(),
        "tipos_carga_aceita": b.get_tipos_carga_aceita(),
    }


def _dict_para_navio(d: dict[str, Any]) -> Navio:
    return Navio(
        str(d["nome"]), float(d["calado"]), float(d["tamanho"]),
        Carga(str(d["carga_tipo"]), float(d["carga_volume"]),
              str(d["carga_origem"]), str(d["carga_destino"])),
        float(d["capacidade"]),
    )


def _dict_para_berco(d: dict[str, Any]) -> Berco:
    return Berco(str(d["identificador"]), float(d["capacidade"]),
                 [str(t) for t in d["tipos_carga_aceita"]])


def salvar(navios: list[Navio], bercos: list[Berco],
           caminho: str | None = None) -> None:
    _c = caminho or CAMINHO
    dados: dict[str, Any] = {
        "navios": [_navio_para_dict(n) for n in navios],
        "bercos": [_berco_para_dict(b) for b in bercos],
    }
    with open(_c, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def carregar(caminho: str | None = None) -> tuple[list[Navio], list[Berco]]:
    _c = caminho or CAMINHO
    if not os.path.exists(_c):
        navios = [_dict_para_navio(d) for d in _NAVIOS_PADRAO]
        bercos = [_dict_para_berco(d) for d in _BERCOS_PADRAO]
        salvar(navios, bercos, _c)
        return navios, bercos
    try:
        with open(_c, "r", encoding="utf-8") as f:
            dados: dict[str, Any] = json.load(f)
        return (
            [_dict_para_navio(d) for d in dados.get("navios", [])],
            [_dict_para_berco(d) for d in dados.get("bercos", [])],
        )
    except (json.JSONDecodeError, KeyError, ValueError):
        navios = [_dict_para_navio(d) for d in _NAVIOS_PADRAO]
        bercos = [_dict_para_berco(d) for d in _BERCOS_PADRAO]
        salvar(navios, bercos, _c)
        return navios, bercos
