from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from model.atividade import Atividade


class AtividadeSchema(BaseModel):
    """Dados enviados para cadastrar uma atividade de estudo."""

    titulo: str = Field(
        ...,
        min_length=1,
        max_length=180,
        title="Título",
        description="Nome curto da atividade que será exibido nos cards do front-end.",
        example="Prova de Banco de Dados",
    )
    disciplina: str = Field(
        ...,
        min_length=1,
        max_length=120,
        title="Disciplina",
        description="Matéria ou área de estudo relacionada à atividade.",
        example="Banco de Dados",
    )
    descricao: Optional[str] = Field(
        "",
        max_length=1000,
        title="Descrição",
        description="Detalhes livres sobre o que precisa ser estudado ou entregue.",
        example="Revisar SQL, modelagem e normalização.",
    )
    data_entrega: date = Field(
        ...,
        title="Data de entrega",
        description="Prazo final da atividade no formato AAAA-MM-DD.",
        example="2026-07-10",
    )
    prioridade: str = Field(
        "Média",
        max_length=20,
        title="Prioridade",
        description="Nível de prioridade. Aceita Baixa, Média ou Alta.",
        example="Alta",
    )
    status: str = Field(
        "Pendente",
        max_length=30,
        title="Status",
        description="Situação atual. Aceita Pendente, Em andamento ou Concluída.",
        example="Pendente",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "titulo": "Prova de Banco de Dados",
                "disciplina": "Banco de Dados",
                "descricao": "Revisar SQL, modelagem e normalização.",
                "data_entrega": "2026-07-10",
                "prioridade": "Alta",
                "status": "Pendente",
            }
        }
    }


class AtividadeUpdateSchema(BaseModel):
    """Campos aceitos para atualização parcial de uma atividade."""

    @field_validator(
        "titulo",
        "disciplina",
        "data_entrega",
        "prioridade",
        "status",
        mode="before",
    )
    @classmethod
    def campo_vazio_nao_altera(cls, valor):
        """Ignora campos vazios na atualização, exceto a descrição, que pode ser apagada."""
        if isinstance(valor, str) and not valor.strip():
            return None
        return valor

    titulo: Optional[str] = Field(
        None,
        min_length=1,
        max_length=180,
        title="Título",
        description="Novo título da atividade, caso precise ser renomeada. Campo vazio não altera o valor atual.",
        example="Trabalho de Engenharia de Software",
    )
    disciplina: Optional[str] = Field(
        None,
        min_length=1,
        max_length=120,
        title="Disciplina",
        description="Nova disciplina ou área associada à atividade. Campo vazio não altera o valor atual.",
        example="Engenharia de Software",
    )
    descricao: Optional[str] = Field(
        None,
        max_length=1000,
        title="Descrição",
        description="Nova descrição. Envie uma string vazia para apagar; omita o campo para manter o valor atual.",
        example="Finalizar relatório e apresentação.",
    )
    data_entrega: Optional[date] = Field(
        None,
        title="Data de entrega",
        description="Nova data de entrega no formato AAAA-MM-DD. Campo vazio não altera o valor atual.",
        example="2026-07-15",
    )
    prioridade: Optional[str] = Field(
        None,
        max_length=20,
        title="Prioridade",
        description="Nova prioridade: Baixa, Média ou Alta. Campo vazio não altera o valor atual.",
        example="Alta",
    )
    status: Optional[str] = Field(
        None,
        max_length=30,
        title="Status",
        description="Novo status: Pendente, Em andamento ou Concluída. Campo vazio não altera o valor atual.",
        example="Em andamento",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "Concluída",
                "prioridade": "Alta",
            }
        }
    }


class AtividadePathSchema(BaseModel):
    """ID da atividade a consultar, editar ou excluir."""

    id: int = Field(
        ...,
        gt=0,
        title="ID da atividade",
        description="Identificador numérico retornado ao cadastrar ou listar atividades.",
        example=1,
    )


class AtividadeFiltroSchema(BaseModel):
    """Filtros opcionais da listagem de atividades."""

    status: Optional[str] = Field(
        None,
        title="Status",
        description="Filtra por status: Pendente, Em andamento ou Concluída.",
        example="Pendente",
    )
    prioridade: Optional[str] = Field(
        None,
        title="Prioridade",
        description="Filtra por prioridade: Baixa, Média ou Alta.",
        example="Alta",
    )
    disciplina: Optional[str] = Field(
        None,
        title="Disciplina",
        description="Filtra por parte do nome da disciplina, sem diferenciar maiúsculas/minúsculas.",
        example="Banco de Dados",
    )
    urgente: Optional[bool] = Field(
        None,
        title="Somente urgentes",
        description="Quando true, retorna apenas atividades abertas com prazo em até três dias.",
        example=True,
    )


class AtividadeViewSchema(BaseModel):
    """Atividade retornada pela API com dados salvos e calculados."""

    id: int = Field(1, description="Identificador único da atividade.", example=1)
    titulo: str = Field("Prova de Banco de Dados", description="Título cadastrado.", example="Prova de Banco de Dados")
    disciplina: str = Field("Banco de Dados", description="Disciplina cadastrada.", example="Banco de Dados")
    descricao: str = Field(
        "Revisar SQL, modelagem e normalização.",
        description="Descrição cadastrada ou string vazia.",
        example="Revisar SQL, modelagem e normalização.",
    )
    data_entrega: str = Field("2026-07-10", description="Data de entrega em AAAA-MM-DD.", example="2026-07-10")
    prioridade: str = Field("Alta", description="Prioridade normalizada.", example="Alta")
    status: str = Field("Pendente", description="Status normalizado.", example="Pendente")
    data_criacao: str = Field(
        "2026-06-29T10:00:00",
        description="Data e hora em que a atividade foi cadastrada.",
        example="2026-06-29T10:00:00",
    )
    dias_restantes: int = Field(11, description="Quantidade de dias até o prazo.", example=11)
    vencida: bool = Field(False, description="Indica se o prazo já passou e a atividade não foi concluída.")
    proxima_do_prazo: bool = Field(
        False,
        description="Indica se a atividade aberta vence nos próximos três dias.",
    )

    model_config = {
        "openapi_extra": {
            "description": "Atividade retornada com campos calculados para apoiar o front-end.",
            "example": {
                "id": 1,
                "titulo": "Prova de Banco de Dados",
                "disciplina": "Banco de Dados",
                "descricao": "Revisar SQL, modelagem e normalização.",
                "data_entrega": "2026-07-10",
                "prioridade": "Alta",
                "status": "Pendente",
                "data_criacao": "2026-06-29T10:00:00",
                "dias_restantes": 11,
                "vencida": False,
                "proxima_do_prazo": False,
            },
        }
    }


class ListagemAtividadesSchema(BaseModel):
    """Lista de atividades retornada pela consulta."""

    atividades: List[AtividadeViewSchema] = Field(
        description="Lista de atividades encontradas para os filtros informados."
    )

    model_config = {
        "openapi_extra": {
            "description": "Resultado da listagem de atividades.",
            "example": {
                "atividades": [
                    {
                        "id": 1,
                        "titulo": "Prova de Banco de Dados",
                        "disciplina": "Banco de Dados",
                        "descricao": "Revisar SQL, modelagem e normalização.",
                        "data_entrega": "2026-07-10",
                        "prioridade": "Alta",
                        "status": "Pendente",
                        "data_criacao": "2026-06-29T10:00:00",
                        "dias_restantes": 11,
                        "vencida": False,
                        "proxima_do_prazo": False,
                    }
                ]
            },
        }
    }


class ResumoAtividadesSchema(BaseModel):
    """Totais das atividades cadastradas, independentemente dos filtros da interface."""

    total: int
    pendentes: int
    em_andamento: int
    concluidas: int
    urgentes: int
    vencidas: int


class AtividadeDelSchema(BaseModel):
    """Confirmação da exclusão de uma atividade."""

    message: str = Field(
        "Atividade removida com sucesso.",
        description="Mensagem de confirmação da exclusão.",
        example="Atividade removida com sucesso.",
    )
    id: int = Field(1, description="ID removido.", example=1)

    model_config = {
        "openapi_extra": {
            "description": "Confirmação de exclusão de atividade.",
            "example": {
                "message": "Atividade removida com sucesso.",
                "id": 1,
            },
        }
    }


def calcula_dias_restantes(atividade: Atividade) -> int:
    """Calcula quantos dias faltam até a data de entrega da atividade."""
    return (atividade.data_entrega - date.today()).days


def apresenta_atividade(atividade: Atividade):
    """Converte uma atividade do banco para o dicionário retornado na API."""
    dias_restantes = calcula_dias_restantes(atividade)
    concluida = atividade.status == "Concluída"

    return {
        "id": atividade.id,
        "titulo": atividade.titulo,
        "disciplina": atividade.disciplina,
        "descricao": atividade.descricao or "",
        "data_entrega": atividade.data_entrega.isoformat(),
        "prioridade": atividade.prioridade,
        "status": atividade.status,
        "data_criacao": atividade.data_criacao.isoformat() if atividade.data_criacao else "",
        "dias_restantes": dias_restantes,
        "vencida": dias_restantes < 0 and not concluida,
        "proxima_do_prazo": 0 <= dias_restantes <= 3 and not concluida,
    }


def apresenta_atividades(atividades: List[Atividade]):
    """Converte uma lista de atividades para o formato esperado pelo front-end."""
    return {"atividades": [apresenta_atividade(atividade) for atividade in atividades]}
