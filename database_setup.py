# Nome do arquivo: database_setup.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

# Cria o arquivo fisico do banco
db_name = 'compressor_historico.db'
engine = create_engine(f'sqlite:///{db_name}', echo=False)

# Base para os Models
Base = declarative_base()
_Session = sessionmaker(bind=engine)

@contextmanager
def get_session():
    """
    Entrega uma sessao segura para operacoes no banco.
    Faz commit automatico ou rollback em caso de erro.
    """
    session = _Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()