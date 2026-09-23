from datetime import date

from typing import List

from pydantic import BaseModel, Field


class FeriadosQuerySchema(BaseModel):
    ano: int = Field(
        default_factory=lambda: date.today().year,
        ge=1900,
        le=2199,
        description="Ano dos feriados nacionais consultados na BrasilAPI.",
        example=2026,
    )


class AtividadeCoincidenteSchema(BaseModel):
    id: int
    titulo: str
    disciplina: str
    status: str


class FeriadoViewSchema(BaseModel):
    data: str
    nome: str
    atividades: List[AtividadeCoincidenteSchema]


class PlanejamentoFeriadosSchema(BaseModel):
    ano: int
    fonte: str
    rota_externa: str
    total_conflitos: int
    feriados: List[FeriadoViewSchema]
