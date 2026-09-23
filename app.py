import logging
from typing import Dict, Iterable, Optional
from unicodedata import combining, normalize

from flask import redirect
from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI, Tag
from sqlalchemy.exc import SQLAlchemyError

from model import Atividade, Sessao
from feriados import FalhaConsultaFeriados, consultar_feriados, relacionar_atividades
from schemas import (
    AtividadeDelSchema,
    AtividadeFiltroSchema,
    AtividadePathSchema,
    AtividadeSchema,
    AtividadeUpdateSchema,
    AtividadeViewSchema,
    ErrorSchema,
    ListagemAtividadesSchema,
    ResumoAtividadesSchema,
    apresenta_atividade,
    apresenta_atividades,
    calcula_dias_restantes,
)
from schemas.feriados import FeriadosQuerySchema, PlanejamentoFeriadosSchema


DESCRICAO_API = "API para organizar provas, trabalhos, leituras e entregas acadêmicas."

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-4s %(funcName)s() L%(lineno)-4d %(message)s",
)
registrador = logging.getLogger(__name__)

informacoes = Info(
    title="Organizador de Estudos API",
    summary="Cadastro e acompanhamento de atividades de estudo.",
    description=DESCRICAO_API,
    version="1.0.0",
)
app = OpenAPI(__name__, info=informacoes)
CORS(app)

TAG_ATIVIDADES = Tag(
    name="Atividades",
    description="Cadastro, consulta, atualização e remoção de atividades acadêmicas.",
)
TAG_PLANEJAMENTO = Tag(
    name="Planejamento",
    description="Consulta feriados nacionais e identifica entregas na mesma data.",
)

STATUS_VALIDOS = ("Pendente", "Em andamento", "Concluída")
PRIORIDADES_VALIDAS = ("Baixa", "Média", "Alta")
ORDEM_PRIORIDADE = {"Alta": 0, "Média": 1, "Baixa": 2}


def chave_texto(valor: str) -> str:
    # Aceita "media" e "Média" nos formulários, mas grava sempre o valor padronizado.
    texto = str(valor or "")
    sem_acentos = "".join(
        caractere
        for caractere in normalize("NFD", texto)
        if not combining(caractere)
    )
    return sem_acentos.strip().casefold()


STATUS_MAPA = {chave_texto(valor): valor for valor in STATUS_VALIDOS}
PRIORIDADE_MAPA = {chave_texto(valor): valor for valor in PRIORIDADES_VALIDAS}


def normalizar_valor(
    valor: Optional[str],
    opcoes: Dict[str, str],
    campo: str,
) -> Optional[str]:
    chave = chave_texto(valor)
    if not chave:
        return None

    if chave not in opcoes:
        valores_validos = ", ".join(opcoes.values())
        raise ValueError(f"{campo} deve ser um destes valores: {valores_validos}.")

    return opcoes[chave]


def texto_obrigatorio(valor: str, campo: str) -> str:
    texto = str(valor or "").strip()
    if not texto:
        raise ValueError(f"{campo} é obrigatório.")
    return texto


def ordenar_atividades(atividades: Iterable[Atividade]):
    # Em uma mesma data, a prioridade mais alta aparece primeiro; título desempata.
    return sorted(
        atividades,
        key=lambda atividade: (
            atividade.data_entrega,
            ORDEM_PRIORIDADE.get(atividade.prioridade, 3),
            atividade.titulo.lower(),
        ),
    )


def eh_urgente(atividade: Atividade) -> bool:
    # Prazo vencido tem alerta próprio e não entra no filtro de próximos três dias.
    dias_restantes = calcula_dias_restantes(atividade)
    return atividade.status != "Concluída" and 0 <= dias_restantes <= 3


def buscar_por_id(sessao, id_atividade: int) -> Optional[Atividade]:
    return sessao.query(Atividade).filter(Atividade.id == id_atividade).first()


def aplicar_filtros(consulta, filtros: AtividadeFiltroSchema):
    if filtros.status:
        consulta = consulta.filter(
            Atividade.status == normalizar_valor(filtros.status, STATUS_MAPA, "status")
        )

    if filtros.prioridade:
        consulta = consulta.filter(
            Atividade.prioridade
            == normalizar_valor(filtros.prioridade, PRIORIDADE_MAPA, "prioridade")
        )

    if filtros.disciplina:
        consulta = consulta.filter(
            Atividade.disciplina.ilike(f"%{filtros.disciplina.strip()}%")
        )

    return consulta


def preencher_atividade(atividade: Atividade, dados: AtividadeUpdateSchema) -> None:
    if dados.titulo is not None:
        atividade.titulo = texto_obrigatorio(dados.titulo, "titulo")

    if dados.disciplina is not None:
        atividade.disciplina = texto_obrigatorio(dados.disciplina, "disciplina")

    if dados.descricao is not None:
        atividade.descricao = dados.descricao.strip()

    if dados.data_entrega is not None:
        atividade.data_entrega = dados.data_entrega

    if dados.prioridade is not None:
        prioridade = normalizar_valor(dados.prioridade, PRIORIDADE_MAPA, "prioridade")
        if prioridade:
            atividade.prioridade = prioridade

    if dados.status is not None:
        status = normalizar_valor(dados.status, STATUS_MAPA, "status")
        if status:
            atividade.status = status


@app.route("/")
def home():
    return redirect("/openapi/swagger")


@app.get(
    "/planejamento/feriados",
    tags=[TAG_PLANEJAMENTO],
    summary="Listar feriados nacionais e entregas coincidentes",
    responses={"200": PlanejamentoFeriadosSchema, "400": ErrorSchema, "502": ErrorSchema},
)
def listar_feriados(query: FeriadosQuerySchema):
    try:
        feriados = consultar_feriados(query.ano)
    except FalhaConsultaFeriados:
        # Falha externa não deve impedir o cadastro e a consulta das atividades locais.
        registrador.exception("Falha ao consultar a BrasilAPI.")
        return {"message": "Não foi possível consultar os feriados agora."}, 502

    sessao = Sessao()
    try:
        atividades = sessao.query(Atividade).all()
        return relacionar_atividades(query.ano, feriados, atividades), 200
    finally:
        sessao.close()


@app.post(
    "/atividades",
    tags=[TAG_ATIVIDADES],
    summary="Cadastrar uma atividade",
    operation_id="cadastrarAtividade",
    responses={"201": AtividadeViewSchema, "400": ErrorSchema},
)
def cadastrar_atividade(form: AtividadeSchema):
    sessao = Sessao()

    try:
        atividade = Atividade(
            titulo=texto_obrigatorio(form.titulo, "titulo"),
            disciplina=texto_obrigatorio(form.disciplina, "disciplina"),
            descricao=(form.descricao or "").strip(),
            data_entrega=form.data_entrega,
            prioridade=normalizar_valor(form.prioridade, PRIORIDADE_MAPA, "prioridade")
            or "Média",
            status=normalizar_valor(form.status, STATUS_MAPA, "status") or "Pendente",
        )

        sessao.add(atividade)
        sessao.commit()
        sessao.refresh(atividade)

        registrador.debug("Atividade cadastrada: %s", atividade.titulo)
        return apresenta_atividade(atividade), 201

    except ValueError as erro:
        sessao.rollback()
        return {"message": str(erro)}, 400

    except SQLAlchemyError:
        sessao.rollback()
        registrador.exception("Erro ao cadastrar atividade.")
        return {"message": "Não foi possível cadastrar a atividade."}, 400

    finally:
        sessao.close()


@app.get(
    "/atividades",
    tags=[TAG_ATIVIDADES],
    summary="Listar e filtrar atividades",
    operation_id="listarAtividades",
    responses={"200": ListagemAtividadesSchema, "400": ErrorSchema},
)
def listar_atividades(query: AtividadeFiltroSchema):
    sessao = Sessao()

    try:
        consulta = aplicar_filtros(sessao.query(Atividade), query)
        atividades = ordenar_atividades(consulta.all())

        if query.urgente:
            atividades = [atividade for atividade in atividades if eh_urgente(atividade)]

        return apresenta_atividades(atividades), 200

    except ValueError as erro:
        return {"message": str(erro)}, 400

    finally:
        sessao.close()


@app.get(
    "/atividades/resumo",
    tags=[TAG_ATIVIDADES],
    summary="Resumir atividades cadastradas",
    operation_id="resumirAtividades",
    responses={"200": ResumoAtividadesSchema},
)
def resumir_atividades():
    """Informa totais gerais; os filtros da lista não alteram o cabeçalho do painel."""
    sessao = Sessao()
    try:
        atividades = sessao.query(Atividade).all()
        return {
            "total": len(atividades),
            "pendentes": sum(a.status == "Pendente" for a in atividades),
            "em_andamento": sum(a.status == "Em andamento" for a in atividades),
            "concluidas": sum(a.status == "Concluída" for a in atividades),
            "urgentes": sum(eh_urgente(a) for a in atividades),
            "vencidas": sum(
                a.status != "Concluída" and calcula_dias_restantes(a) < 0
                for a in atividades
            ),
        }, 200
    finally:
        sessao.close()


@app.get(
    "/atividades/<int:id>",
    tags=[TAG_ATIVIDADES],
    summary="Buscar atividade por ID",
    operation_id="buscarAtividade",
    responses={"200": AtividadeViewSchema, "404": ErrorSchema},
)
def buscar_atividade(path: AtividadePathSchema):
    sessao = Sessao()

    try:
        atividade = buscar_por_id(sessao, path.id)
        if not atividade:
            return {"message": "Atividade não encontrada."}, 404

        return apresenta_atividade(atividade), 200

    finally:
        sessao.close()


@app.put(
    "/atividades/<int:id>",
    tags=[TAG_ATIVIDADES],
    summary="Atualizar atividade",
    operation_id="atualizarAtividade",
    responses={"200": AtividadeViewSchema, "400": ErrorSchema, "404": ErrorSchema},
)
def atualizar_atividade(path: AtividadePathSchema, form: AtividadeUpdateSchema):
    sessao = Sessao()

    try:
        atividade = buscar_por_id(sessao, path.id)
        if not atividade:
            return {"message": "Atividade não encontrada."}, 404

        preencher_atividade(atividade, form)
        sessao.commit()
        sessao.refresh(atividade)

        return apresenta_atividade(atividade), 200

    except ValueError as erro:
        sessao.rollback()
        return {"message": str(erro)}, 400

    except SQLAlchemyError:
        sessao.rollback()
        registrador.exception("Erro ao atualizar atividade.")
        return {"message": "Não foi possível atualizar a atividade."}, 400

    finally:
        sessao.close()


@app.delete(
    "/atividades/<int:id>",
    tags=[TAG_ATIVIDADES],
    summary="Excluir atividade",
    operation_id="excluirAtividade",
    responses={"200": AtividadeDelSchema, "404": ErrorSchema},
)
def excluir_atividade(path: AtividadePathSchema):
    sessao = Sessao()

    try:
        atividade = buscar_por_id(sessao, path.id)
        if not atividade:
            return {"message": "Atividade não encontrada."}, 404

        sessao.delete(atividade)
        sessao.commit()
        return {"message": "Atividade removida com sucesso.", "id": path.id}, 200

    finally:
        sessao.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
