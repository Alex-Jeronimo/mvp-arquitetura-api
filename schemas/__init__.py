# Reúne os schemas usados pelas rotas para permitir a importação por `schemas`.
from schemas.atividade import (
    AtividadeDelSchema,
    AtividadeFiltroSchema,
    AtividadePathSchema,
    AtividadeSchema,
    AtividadeUpdateSchema,
    AtividadeViewSchema,
    ListagemAtividadesSchema,
    ResumoAtividadesSchema,
    apresenta_atividade,
    apresenta_atividades,
    calcula_dias_restantes,
)
from schemas.error import ErrorSchema
