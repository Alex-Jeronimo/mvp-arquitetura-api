import io
import json
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from feriados import FalhaConsultaFeriados, consultar_feriados, relacionar_atividades


class TesteIntegracaoFeriados(unittest.TestCase):
    @patch("feriados.urlopen")
    def test_consulta_externa_e_cruza_apenas_atividades_abertas(self, abrir):
        abrir.return_value = io.BytesIO(
            json.dumps([{"date": "2026-09-07", "name": "Independência do Brasil"}]).encode()
        )
        feriados = consultar_feriados(2026)
        atividades = [
            SimpleNamespace(id=1, titulo="Prova", disciplina="Arquitetura", status="Pendente", data_entrega=date(2026, 9, 7)),
            SimpleNamespace(id=2, titulo="Leitura", disciplina="Arquitetura", status="Concluída", data_entrega=date(2026, 9, 7)),
            SimpleNamespace(id=3, titulo="Trabalho", disciplina="DevOps", status="Pendente", data_entrega=date(2026, 9, 8)),
        ]

        resposta = relacionar_atividades(2026, feriados, atividades)

        self.assertEqual(resposta["total_conflitos"], 1)
        self.assertEqual(resposta["feriados"][0]["atividades"][0]["titulo"], "Prova")
        self.assertEqual(len(resposta["feriados"][0]["atividades"]), 1)
        self.assertIn("/api/feriados/v1/2026", abrir.call_args.args[0].full_url)

    @patch("feriados.urlopen", side_effect=TimeoutError())
    def test_falha_externa_gera_erro_controlado(self, _abrir):
        with self.assertRaises(FalhaConsultaFeriados):
            consultar_feriados(2026)

    @patch("feriados.urlopen", return_value=io.BytesIO(b'{"unexpected":true}'))
    def test_resposta_invalida_nao_e_aceita(self, _abrir):
        with self.assertRaises(FalhaConsultaFeriados):
            consultar_feriados(2026)


if __name__ == "__main__":
    unittest.main()
