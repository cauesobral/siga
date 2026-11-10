import os
import sys
import unittest
from datetime import date, datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "model"))

from ApiMare import ApiMare
from Berco import Berco
from Carga import Carga
from CondicaoClimatica import CondicaoClimatica
from EventoDeRisco import EventoDeRisco, NivelDeImpacto
from JanelaDeMare import JanelaDeMare
from Navio import Navio
from PoliticaDeAtracacao import PorMare, PorOrdemDeChegada, PorPrioridadeDeCarga
from StatusOperacional import StatusOperacional


def navio(nome="Teste", calado=12.0, tipo="Granel", volume=2000):
    return Navio(nome, calado, 200, Carga(tipo, volume, "Santos", "Roterdã"), 50000)


class RespostaFalsa:
    def raise_for_status(self):
        pass

    def json(self):
        return {"hourly": {
            "time": ["2026-11-10T11:00", "2026-11-10T12:00", "2026-11-10T13:00"],
            "wave_height": [1.1, 1.4, 1.2], "wave_direction": [180, 185, 190],
            "wave_period": [8, 9, 9], "sea_level_height_msl": [0.2, None, 1.5]}}


class SessaoFalsa:
    def get(self, url, params, timeout):
        return RespostaFalsa()


class TestEventoDeRisco(unittest.TestCase):
    def test_classe_abstrata_nao_instancia(self):
        with self.assertRaises(TypeError):
            EventoDeRisco("x", date(2026, 1, 1), date(2026, 1, 2))

    def test_data_fim_anterior_ao_inicio(self):
        with self.assertRaises(ValueError):
            JanelaDeMare(datetime(2026, 1, 1), 1.0, 13.5).set_data_fim(date(2025, 12, 31))

    def test_nivel_precisa_ser_enum(self):
        janela = JanelaDeMare(datetime(2026, 1, 1), 1.0, 13.5)
        with self.assertRaises(TypeError):
            janela.set_nivel_de_impacto("alto")

    def test_esta_ativo(self):
        janela = JanelaDeMare(datetime(2026, 1, 1, 10), 1.0, 13.5)
        self.assertTrue(janela.esta_ativo(date(2026, 1, 1)))
        self.assertFalse(janela.esta_ativo(date(2026, 1, 2)))


class TestCondicaoClimatica(unittest.TestCase):
    def test_classificar_vento(self):
        self.assertEqual(CondicaoClimatica.classificar_vento(3), NivelDeImpacto.BAIXO)
        self.assertEqual(CondicaoClimatica.classificar_vento(5), NivelDeImpacto.BAIXO)
        self.assertEqual(CondicaoClimatica.classificar_vento(6), NivelDeImpacto.MEDIO)
        self.assertEqual(CondicaoClimatica.classificar_vento(8), NivelDeImpacto.ALTO)
        self.assertEqual(CondicaoClimatica.classificar_vento(12), NivelDeImpacto.CRITICO)

    def test_pior_entre_vento_e_chuva(self):
        c = CondicaoClimatica(datetime(2026, 1, 1, 10), velocidade_vento=2, precipitacao=60)
        self.assertEqual(c.get_nivel_de_impacto(), NivelDeImpacto.CRITICO)

    def test_bloqueio_so_a_partir_de_alto(self):
        calmo = CondicaoClimatica(datetime(2026, 1, 1, 10), 3)
        ventania = CondicaoClimatica(datetime(2026, 1, 1, 10), 9)
        self.assertFalse(calmo.bloqueia_atracacao(navio()))
        self.assertTrue(ventania.bloqueia_atracacao(navio()))

    def test_de_json(self):
        c = CondicaoClimatica.de_json({"horario": "2026-11-10T16:00", "wind_speed_10m": 8.0,
                                       "precipitation": 0.5, "precipitation_probability": 20})
        self.assertEqual(c.get_horario(), datetime(2026, 11, 10, 16))
        self.assertTrue(c.bloqueia_atracacao(navio()))


class TestJanelaDeMare(unittest.TestCase):
    def test_mare_baixa_bloqueia_navio_fundo(self):
        baixa = JanelaDeMare(datetime(2026, 1, 1, 6), 0.2, 13.5)
        alta = JanelaDeMare(datetime(2026, 1, 1, 12), 1.5, 13.5)
        fundo = navio(calado=13.5)
        self.assertTrue(baixa.bloqueia_atracacao(fundo))
        self.assertFalse(alta.bloqueia_atracacao(fundo))

    def test_profundidade_disponivel(self):
        self.assertAlmostEqual(JanelaDeMare(datetime(2026, 1, 1), 1.0, 13.5).profundidade_disponivel(), 14.5)

    def test_da_api_com_sessao_falsa(self):
        api = ApiMare(sessao=SessaoFalsa())
        janela = JanelaDeMare.da_api(datetime(2026, 11, 10, 13, 20), 13.5, api)
        self.assertAlmostEqual(janela.get_altura_da_mare(), 1.5)

    def test_da_api_hora_sem_dado(self):
        api = ApiMare(sessao=SessaoFalsa())
        self.assertIsNone(JanelaDeMare.da_api(datetime(2026, 11, 10, 12), 13.5, api))
        self.assertEqual(len(JanelaDeMare.lista_da_api(13.5, api)), 2)


class TestNavioEBerco(unittest.TestCase):
    def test_tempo_estimado(self):
        self.assertEqual(navio(tipo="Granel", volume=4000).tempoEstimadoOperacao(), 2.0)

    def test_tipo_sem_taxa(self):
        with self.assertRaises(ValueError):
            navio(tipo="Areia").tempoEstimadoOperacao()

    def test_ocupar_e_liberar(self):
        berco = Berco("B1", 320, ["Granel"])
        berco.ocupar(navio())
        self.assertEqual(berco.get_status(), StatusOperacional.OCUPADO)
        berco.liberar()
        self.assertEqual(berco.get_status(), StatusOperacional.LIVRE)

    def test_berco_recusa_carga_incompativel_ou_ocupado(self):
        berco = Berco("B1", 320, ["Granel"])
        with self.assertRaises(ValueError):
            berco.ocupar(navio(tipo="Petróleo"))
        berco.ocupar(navio())
        self.assertFalse(berco.aceita_navio(navio()))


class TestPoliticas(unittest.TestCase):
    def setUp(self):
        self.graneleiro = navio("G", 11.2, "Granel")
        self.petroleiro = navio("P", 13.8, "Petróleo")
        self.container = navio("C", 12.5, "Contêineres")
        self.fila = [self.graneleiro, self.petroleiro, self.container]

    def nomes(self, lista):
        return [n.get_nome() for n in lista]

    def test_ordem_de_chegada_mantem_a_fila(self):
        self.assertEqual(self.nomes(PorOrdemDeChegada().ordenar_fila(self.fila)), ["G", "P", "C"])

    def test_prioridade_de_carga(self):
        self.assertEqual(self.nomes(PorPrioridadeDeCarga().ordenar_fila(self.fila)), ["P", "G", "C"])

    def test_ordenar_nao_altera_a_fila_original(self):
        PorPrioridadeDeCarga().ordenar_fila(self.fila)
        self.assertEqual(self.nomes(self.fila), ["G", "P", "C"])

    def test_por_mare_deixa_bloqueados_para_o_fim(self):
        mare_baixa = JanelaDeMare(datetime.now(), 0.2, 13.5)
        self.assertEqual(self.nomes(PorMare().ordenar_fila(self.fila, [mare_baixa])), ["G", "P", "C"])

    def test_proxima_atracacao_pula_navio_bloqueado(self):
        mare_baixa = JanelaDeMare(datetime.now(), 0.2, 13.5)
        bercos = [Berco("B1", 320, ["Granel", "Petróleo"])]
        escolhido = PorPrioridadeDeCarga().proxima_atracacao(self.fila, bercos, [mare_baixa])
        self.assertEqual(escolhido[0].get_nome(), "G")

    def test_sem_berco_compativel_devolve_none(self):
        self.assertIsNone(PorOrdemDeChegada().proxima_atracacao(self.fila, []))


if __name__ == "__main__":
    unittest.main()
