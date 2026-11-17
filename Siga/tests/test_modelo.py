from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import date, datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "model"))

import Repositorio
from ApiMare import ApiMare
from Berco import Berco
from Carga import Carga
from CondicaoClimatica import CondicaoClimatica
from EventoDeRisco import EventoDeRisco, NivelDeImpacto
from Gerenciador import GerenciadorDeAtracacao
from Historico import Historico
from JanelaDeMare import JanelaDeMare
from Navio import Navio
from PoliticaDeAtracacao import PorMare, PorOrdemDeChegada, PorPrioridadeDeCarga
from StatusOperacional import StatusOperacional


def navio(nome: str = "Teste", calado: float = 12.0,
          tipo: str = "Granel", volume: float = 2000) -> Navio:
    return Navio(nome, calado, 200, Carga(tipo, volume, "Santos", "Roterdã"), 50000)


class RespostaFalsa:
    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict[str, object]:
        return {"hourly": {
            "time": ["2026-11-10T11:00", "2026-11-10T12:00", "2026-11-10T13:00"],
            "wave_height": [1.1, 1.4, 1.2], "wave_direction": [180, 185, 190],
            "wave_period": [8, 9, 9], "sea_level_height_msl": [0.2, None, 1.5]}}


class SessaoFalsa:
    def get(self, url: str, params: object, timeout: int) -> RespostaFalsa:
        return RespostaFalsa()


class TestEventoDeRisco(unittest.TestCase):
    def test_classe_abstrata_nao_instancia(self) -> None:
        with self.assertRaises(TypeError):
            EventoDeRisco("x", date(2026, 1, 1), date(2026, 1, 2))  # type: ignore[abstract]

    def test_data_fim_anterior_ao_inicio(self) -> None:
        with self.assertRaises(ValueError):
            JanelaDeMare(datetime(2026, 1, 1), 1.0, 13.5).set_data_fim(date(2025, 12, 31))

    def test_nivel_precisa_ser_enum(self) -> None:
        janela = JanelaDeMare(datetime(2026, 1, 1), 1.0, 13.5)
        with self.assertRaises(TypeError):
            janela.set_nivel_de_impacto("alto")  # type: ignore[arg-type]

    def test_esta_ativo(self) -> None:
        janela = JanelaDeMare(datetime(2026, 1, 1, 10), 1.0, 13.5)
        self.assertTrue(janela.esta_ativo(date(2026, 1, 1)))
        self.assertFalse(janela.esta_ativo(date(2026, 1, 2)))


class TestCondicaoClimatica(unittest.TestCase):
    def test_classificar_vento(self) -> None:
        self.assertEqual(CondicaoClimatica.classificar_vento(3), NivelDeImpacto.BAIXO)
        self.assertEqual(CondicaoClimatica.classificar_vento(5), NivelDeImpacto.BAIXO)
        self.assertEqual(CondicaoClimatica.classificar_vento(6), NivelDeImpacto.MEDIO)
        self.assertEqual(CondicaoClimatica.classificar_vento(8), NivelDeImpacto.ALTO)
        self.assertEqual(CondicaoClimatica.classificar_vento(12), NivelDeImpacto.CRITICO)

    def test_pior_entre_vento_e_chuva(self) -> None:
        c = CondicaoClimatica(datetime(2026, 1, 1, 10), velocidade_vento=2, precipitacao=60)
        self.assertEqual(c.get_nivel_de_impacto(), NivelDeImpacto.CRITICO)

    def test_bloqueio_so_a_partir_de_alto(self) -> None:
        calmo = CondicaoClimatica(datetime(2026, 1, 1, 10), 3)
        ventania = CondicaoClimatica(datetime(2026, 1, 1, 10), 9)
        self.assertFalse(calmo.bloqueia_atracacao(navio()))
        self.assertTrue(ventania.bloqueia_atracacao(navio()))

    def test_de_json(self) -> None:
        c = CondicaoClimatica.de_json({"horario": "2026-11-10T16:00", "wind_speed_10m": 8.0,
                                       "precipitation": 0.5, "precipitation_probability": 20})
        self.assertEqual(c.get_horario(), datetime(2026, 11, 10, 16))
        self.assertTrue(c.bloqueia_atracacao(navio()))


class TestJanelaDeMare(unittest.TestCase):
    def test_mare_baixa_bloqueia_navio_fundo(self) -> None:
        baixa = JanelaDeMare(datetime(2026, 1, 1, 6), 0.2, 13.5)
        alta = JanelaDeMare(datetime(2026, 1, 1, 12), 1.5, 13.5)
        fundo = navio(calado=13.5)
        self.assertTrue(baixa.bloqueia_atracacao(fundo))
        self.assertFalse(alta.bloqueia_atracacao(fundo))

    def test_profundidade_disponivel(self) -> None:
        self.assertAlmostEqual(JanelaDeMare(datetime(2026, 1, 1), 1.0, 13.5).profundidade_disponivel(), 14.5)


class TestNavioEBerco(unittest.TestCase):
    def test_tempo_estimado(self) -> None:
        self.assertEqual(navio(tipo="Granel", volume=4000).tempo_estimado_operacao(), 2.0)

    def test_tipo_sem_taxa(self) -> None:
        with self.assertRaises(ValueError):
            navio(tipo="Areia").tempo_estimado_operacao()

    def test_navio_imutavel(self) -> None:
        n = navio()
        with self.assertRaises(Exception):
            n.nome = "Novo"  # type: ignore[misc]

    def test_ocupar_e_liberar(self) -> None:
        berco = Berco("B1", 320, ["Granel"])
        berco.ocupar(navio())
        self.assertEqual(berco.get_status(), StatusOperacional.OCUPADO)
        berco.liberar()
        self.assertEqual(berco.get_status(), StatusOperacional.LIVRE)

    def test_berco_recusa_carga_incompativel_ou_ocupado(self) -> None:
        berco = Berco("B1", 320, ["Granel"])
        with self.assertRaises(ValueError):
            berco.ocupar(navio(tipo="Petróleo"))
        berco.ocupar(navio())
        self.assertFalse(berco.aceita_navio(navio()))


class TestPoliticas(unittest.TestCase):
    def setUp(self) -> None:
        self.graneleiro = navio("G", 11.2, "Granel")
        self.petroleiro = navio("P", 13.8, "Petróleo")
        self.container = navio("C", 12.5, "Contêineres")
        self.fila = [self.graneleiro, self.petroleiro, self.container]
        self.evento = JanelaDeMare(datetime(2026, 1, 1, 10), 1.0, 13.5)

    def nomes(self, lista: list[Navio]) -> list[str]:
        return [n.get_nome() for n in lista]

    def test_ordem_de_chegada_mantem_a_fila(self) -> None:
        self.assertEqual(self.nomes(PorOrdemDeChegada().ordenar_fila(self.fila, [self.evento])), ["G", "P", "C"])

    def test_prioridade_de_carga(self) -> None:
        prioridades = {"petróleo": 1, "granel": 2, "contêineres": 3}
        politica = PorPrioridadeDeCarga(prioridade_por_tipo=prioridades)
        self.assertEqual(self.nomes(politica.ordenar_fila(self.fila, self.evento)), ["P", "G", "C"])

    def test_ordenar_nao_altera_a_fila_original(self) -> None:
        prioridades = {"petróleo": 1, "granel": 2, "contêineres": 3}
        politica = PorPrioridadeDeCarga(prioridade_por_tipo=prioridades)
        politica.ordenar_fila(self.fila, [self.evento])
        self.assertEqual(self.nomes(self.fila), ["G", "P", "C"])

    def test_por_mare_deixa_bloqueados_para_o_fim(self) -> None:
        mare_baixa = JanelaDeMare(datetime.now(), 0.2, 13.5)
        self.assertEqual(self.nomes(PorMare().ordenar_fila(self.fila, [mare_baixa])), ["G", "P", "C"])

    def test_proxima_atracacao_pula_navio_bloqueado(self) -> None:
        mare_baixa = JanelaDeMare(datetime.now(), 0.2, 13.5)
        PRIORIDADE_POR_TIPO = {"petróleo": 0, "granel": 1, "contêineres": 2}
        bercos = [Berco("B1", 320, ["Granel", "Petróleo"])]
        escolhido = PorPrioridadeDeCarga(PRIORIDADE_POR_TIPO).proxima_atracacao(self.fila, bercos, [mare_baixa])
        self.assertIsNotNone(escolhido)
        self.assertEqual(escolhido[0].get_nome(), "G")  # type: ignore[index]

    def test_sem_berco_compativel_devolve_none(self) -> None:
        self.assertIsNone(PorOrdemDeChegada().proxima_atracacao(self.fila, []))


class TestRepositorio(unittest.TestCase):
    def setUp(self) -> None:
        fd, self._tmppath = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.unlink(self._tmppath)
        self._orig_caminho = Repositorio.CAMINHO
        Repositorio.CAMINHO = self._tmppath

    def tearDown(self) -> None:
        Repositorio.CAMINHO = self._orig_caminho
        if os.path.exists(self._tmppath):
            os.unlink(self._tmppath)

    def test_salvar_e_carregar_roundtrip(self) -> None:
        navios = [navio()]
        bercos = [Berco("TX", 200, ["Granel"])]
        Repositorio.salvar(navios, bercos)
        navios2, bercos2 = Repositorio.carregar()
        self.assertEqual(navios2[0].get_nome(), "Teste")
        self.assertEqual(bercos2[0].get_identificador(), "TX")

    def test_arquivo_inexistente_usa_padrao(self) -> None:
        navios, bercos = Repositorio.carregar()
        self.assertGreater(len(navios), 0)
        self.assertGreater(len(bercos), 0)

    def test_arquivo_invalido_usa_padrao(self) -> None:
        with open(self._tmppath, "w") as f:
            f.write("not valid json")
        navios, bercos = Repositorio.carregar()
        self.assertGreater(len(navios), 0)
        self.assertGreater(len(bercos), 0)


class TestGerenciador(unittest.TestCase):
    def setUp(self) -> None:
        fd, self._tmppath = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        self.historico = Historico(self._tmppath)
        self.gerenciador = GerenciadorDeAtracacao(self.historico)
        self.berco = Berco("B1", 320, ["Granel"])
        self.nav = navio()
        self.fila: list[Navio] = [self.nav]

    def tearDown(self) -> None:
        os.unlink(self._tmppath)

    def test_status_normal_sem_eventos(self) -> None:
        self.assertEqual(self.gerenciador.status_navio(self.nav, []), "Normal")

    def test_status_risco_alto_com_bloqueio(self) -> None:
        nav_fundo = navio(calado=14.0)
        mare_baixa = JanelaDeMare(datetime.now(), 0.2, 13.5)
        self.assertEqual(self.gerenciador.status_navio(nav_fundo, [mare_baixa]), "Risco Alto")

    def test_atracar_ocupa_berco_e_remove_da_fila(self) -> None:
        self.gerenciador.atracar(self.nav, self.berco, self.fila)
        self.assertEqual(self.berco.get_status(), StatusOperacional.OCUPADO)
        self.assertNotIn(self.nav, self.fila)

    def test_liberar_libera_berco(self) -> None:
        self.berco.ocupar(self.nav)
        self.gerenciador.liberar(self.berco)
        self.assertEqual(self.berco.get_status(), StatusOperacional.LIVRE)

    def test_avancar_turno_libera_ocupados(self) -> None:
        self.berco.ocupar(self.nav)
        n = self.gerenciador.avancar_turno([self.berco])
        self.assertEqual(n, 1)
        self.assertEqual(self.berco.get_status(), StatusOperacional.LIVRE)


if __name__ == "__main__":
    unittest.main()
