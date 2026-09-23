import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists

from model.base import BaseModelo
from model.atividade import Atividade


# No Docker, DATABASE_PATH aponta para o volume persistente. Fora dele, usamos
# um arquivo local para facilitar a execução e os testes sem Compose.
ARQUIVO_BANCO = Path(os.environ.get("DATABASE_PATH", "database/db.sqlite3")).resolve()
ARQUIVO_BANCO.parent.mkdir(parents=True, exist_ok=True)

URL_BANCO = f"sqlite:///{ARQUIVO_BANCO.as_posix()}"
motor = create_engine(URL_BANCO, echo=False)
Sessao = sessionmaker(bind=motor)

if not database_exists(motor.url):
    create_database(motor.url)

BaseModelo.metadata.create_all(motor)
