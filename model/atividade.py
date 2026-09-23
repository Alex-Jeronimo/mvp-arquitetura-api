from datetime import date, datetime
from typing import Union

from sqlalchemy import Column, Date, DateTime, Integer, String, Text

from model.base import BaseModelo


class Atividade(BaseModelo):
    __tablename__ = "atividades"

    id = Column("pk_atividade", Integer, primary_key=True)
    titulo = Column(String(180), nullable=False)
    disciplina = Column(String(120), nullable=False)
    descricao = Column(Text, nullable=True)
    data_entrega = Column(Date, nullable=False)
    prioridade = Column(String(20), nullable=False, default="Média")
    status = Column(String(30), nullable=False, default="Pendente")
    data_criacao = Column(DateTime, default=datetime.now)

    def __init__(
        self,
        titulo: str,
        disciplina: str,
        descricao: str,
        data_entrega: date,
        prioridade: str,
        status: str = "Pendente",
        data_criacao: Union[datetime, None] = None,
    ):
        self.titulo = titulo
        self.disciplina = disciplina
        self.descricao = descricao
        self.data_entrega = data_entrega
        self.prioridade = prioridade
        self.status = status

        if data_criacao:
            self.data_criacao = data_criacao
