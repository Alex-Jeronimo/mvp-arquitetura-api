import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TesteFluxoDaAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta = tempfile.TemporaryDirectory()
        cls.banco_anterior = os.environ.get("DATABASE_PATH")
        os.environ["DATABASE_PATH"] = str(Path(cls.pasta.name) / "atividades.sqlite3")
        cls.modulo = importlib.import_module("app")
        cls.cliente = cls.modulo.app.test_client()

    @classmethod
    def tearDownClass(cls):
        import model

        model.motor.dispose()
        if cls.banco_anterior is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = cls.banco_anterior
        cls.pasta.cleanup()

    def test_crud_e_integracao_com_feriados(self):
        criado = self.cliente.post(
            "/atividades",
            data={
                "titulo": "Trabalho final",
                "disciplina": "Arquitetura",
                "descricao": "Entregar relatório",
                "data_entrega": "2026-09-07",
                "prioridade": "Alta",
                "status": "Pendente",
            },
        )
        self.assertEqual(criado.status_code, 201, criado.get_json())
        identificador = criado.get_json()["id"]

        listado = self.cliente.get("/atividades")
        self.assertEqual(listado.status_code, 200)
        self.assertEqual(len(listado.get_json()["atividades"]), 1)
        self.assertEqual(self.cliente.get(f"/atividades/{identificador}").status_code, 200)

        resumo = self.cliente.get("/atividades/resumo")
        self.assertEqual(resumo.status_code, 200)
        self.assertEqual(resumo.get_json()["total"], 1)
        self.assertEqual(resumo.get_json()["pendentes"], 1)

        with patch.object(
            self.modulo,
            "consultar_feriados",
            return_value=[{"data": "2026-09-07", "nome": "Independência do Brasil"}],
        ):
            planejamento = self.cliente.get("/planejamento/feriados?ano=2026")
        self.assertEqual(planejamento.status_code, 200, planejamento.get_json())
        self.assertEqual(planejamento.get_json()["total_conflitos"], 1)

        alterado = self.cliente.put(
            f"/atividades/{identificador}", data={"status": "Concluída"}
        )
        self.assertEqual(alterado.status_code, 200, alterado.get_json())
        self.assertEqual(self.cliente.get("/atividades/resumo").get_json()["concluidas"], 1)

        with patch.object(
            self.modulo,
            "consultar_feriados",
            return_value=[{"data": "2026-09-07", "nome": "Independência do Brasil"}],
        ):
            planejamento = self.cliente.get("/planejamento/feriados?ano=2026")
        self.assertEqual(planejamento.get_json()["total_conflitos"], 0)

        excluido = self.cliente.delete(f"/atividades/{identificador}")
        self.assertEqual(excluido.status_code, 200)
        self.assertEqual(self.cliente.get("/atividades").get_json()["atividades"], [])
        self.assertEqual(self.cliente.get("/openapi/swagger").status_code, 200)
        caminhos = self.cliente.get("/openapi/openapi.json").get_json()["paths"]
        self.assertGreaterEqual(len(caminhos), 4)
        self.assertIn("/atividades/resumo", caminhos)

    def test_descricao_omitida_preserva_e_vazia_apaga(self):
        criado = self.cliente.post("/atividades", data={
            "titulo": "Teste de edição", "disciplina": "Arquitetura",
            "descricao": "Texto original", "data_entrega": "2026-10-12",
            "prioridade": "Alta", "status": "Pendente",
        })
        self.assertEqual(criado.status_code, 201, criado.get_json())
        rota = f"/atividades/{criado.get_json()['id']}"
        try:
            resposta = self.cliente.put(rota, data={"status": "Em andamento"})
            self.assertEqual(resposta.status_code, 200, resposta.get_json())
            self.assertEqual(self.cliente.get(rota).get_json()["descricao"], "Texto original")
            resposta = self.cliente.put(rota, data={"descricao": ""})
            self.assertEqual(resposta.status_code, 200, resposta.get_json())
            self.assertEqual(self.cliente.get(rota).get_json()["descricao"], "")
        finally:
            self.cliente.delete(rota)

    def test_falha_externa_nao_bloqueia_o_crud(self):
        from feriados import FalhaConsultaFeriados

        with patch.object(self.modulo, "consultar_feriados", side_effect=FalhaConsultaFeriados()):
            resposta = self.cliente.get("/planejamento/feriados?ano=2026")
        self.assertEqual(resposta.status_code, 502)
        self.assertEqual(self.cliente.get("/atividades").status_code, 200)


if __name__ == "__main__":
    unittest.main()
