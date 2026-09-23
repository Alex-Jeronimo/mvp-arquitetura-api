"""Integração com feriados nacionais da BrasilAPI e cruzamento com entregas."""

import json
import os
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class FalhaConsultaFeriados(Exception):
    """A consulta externa falhou ou devolveu dados inesperados."""


def consultar_feriados(ano: int):
    origem = os.environ.get("BRASILAPI_URL", "https://brasilapi.com.br").rstrip("/")
    requisicao = Request(
        f"{origem}/api/feriados/v1/{ano}",
        headers={"Accept": "application/json", "User-Agent": "organizador-estudos-mvp/2.0"},
    )

    try:
        with urlopen(requisicao, timeout=5) as resposta:
            dados = json.load(resposta)
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as erro:
        raise FalhaConsultaFeriados("Falha na resposta da BrasilAPI.") from erro

    if not isinstance(dados, list):
        raise FalhaConsultaFeriados("A BrasilAPI devolveu um formato inesperado.")

    # Não repassamos a resposta externa diretamente: validamos os campos usados
    # pelo projeto e mantemos só os feriados do ano solicitado.
    feriados = []
    for item in dados:
        try:
            data_feriado = date.fromisoformat(item["date"])
            nome = str(item["name"]).strip()
        except (KeyError, TypeError, ValueError) as erro:
            raise FalhaConsultaFeriados("Feriado com campos inválidos.") from erro
        if data_feriado.year == ano and nome:
            feriados.append({"data": data_feriado.isoformat(), "nome": nome})

    return sorted(feriados, key=lambda feriado: feriado["data"])


def relacionar_atividades(ano, feriados, atividades):
    # A coincidência considera a data de entrega; tarefas concluídas já não
    # precisam aparecer como pendências no painel de planejamento.
    por_data = {}
    for atividade in atividades:
        if atividade.data_entrega.year != ano or atividade.status == "Concluída":
            continue
        por_data.setdefault(atividade.data_entrega.isoformat(), []).append(
            {
                "id": atividade.id,
                "titulo": atividade.titulo,
                "disciplina": atividade.disciplina,
                "status": atividade.status,
            }
        )

    resultado = [
        {**feriado, "atividades": por_data.get(feriado["data"], [])}
        for feriado in feriados
    ]
    return {
        "ano": ano,
        "fonte": "BrasilAPI",
        "rota_externa": f"/api/feriados/v1/{ano}",
        "total_conflitos": sum(len(item["atividades"]) for item in resultado),
        "feriados": resultado,
    }
