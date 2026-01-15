"""
Módulo de Banco de Dados do Sistema Supervisório

Responsável por:
- Receber dados do monitoramento via comunicação
- Armazenar dados históricos usando ORM (SQLAlchemy)
- Disponibilizar consultas históricas

Não acessa Modbus diretamente.
"""

import threading
import time
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# Comunicação com o backend
from comunicacao import com

# =========================================================
# ORM
# =========================================================
Base = declarative_base()


class CompressorData(Base):
    """
    Tabela de histórico do compressor
    """
    __tablename__ = "compressor_data"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)

    # ---- Processo ----
    pressao = Column(Float)
    vazao = Column(Float)

    # ---- Temperaturas ----
    temp_r = Column(Float)
    temp_s = Column(Float)
    temp_t = Column(Float)
    temp_carcaca = Column(Float)

    # ---- Mecânicas ----
    torque = Column(Float)
    encoder = Column(Float)

    # ---- Elétricas ----
    corrente_r = Column(Float)
    corrente_s = Column(Float)
    corrente_t = Column(Float)
    tensao_rs = Column(Float)
    ativa_total = Column(Float)


# =========================================================
# HANDLER DO BANCO
# =========================================================
class BDHandler:
    """
    Thread de armazenamento histórico.
    Consome dados do monitoramento via comunicação.
    """

    def __init__(self, db_path="sqlite:///compressor.db"):
        # Banco SQLite
        self.engine = create_engine(
            db_path,
            connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        self.running = False
        self.lock = threading.Lock()

    # =====================================================
    # THREAD DE ARMAZENAMENTO
    # =====================================================
    def start(self, interval=1.0):
        """
        Inicia a thread de armazenamento
        """
        self.running = True
        self.thread = threading.Thread(
            target=self._storage_loop,
            args=(interval,),
            daemon=True
        )
        self.thread.start()

    def stop(self):
        self.running = False

    def _storage_loop(self, interval):
        """
        Loop secundário:
        - Obtém dados do monitoramento
        - Insere no banco via ORM
        """
        session = self.Session()

        while self.running:
            try:
                dados = com.obter_dados()

                if dados and "values" in dados:
                    valores = dados["values"]

                    row = CompressorData(
                        timestamp=datetime.fromtimestamp(dados["timestamp"]),

                        # Processo
                        pressao=valores.get("co.pressao"),
                        vazao=valores.get("co.fit03"),

                        # Temperaturas
                        temp_r=valores.get("co.temp_r"),
                        temp_s=valores.get("co.temp_s"),
                        temp_t=valores.get("co.temp_t"),
                        temp_carcaca=valores.get("co.temp_carc"),

                        # Mecânicas
                        torque=valores.get("co.torque"),
                        encoder=valores.get("co.encoder"),

                        # Elétricas
                        corrente_r=valores.get("co.corrente_r"),
                        corrente_s=valores.get("co.corrente_s"),
                        corrente_t=valores.get("co.corrente_t"),
                        tensao_rs=valores.get("co.tensao_rs"),
                        ativa_total=valores.get("co.ativa_total"),
                    )

                    with self.lock:
                        session.add(row)
                        session.commit()

            except Exception as e:
                print(f"[BDHandler] Erro ao salvar dados: {e}")

            time.sleep(interval)

        session.close()

    # =====================================================
    # CONSULTA HISTÓRICA
    # =====================================================
    def get_history(self, campo, t_ini, t_fim):
        """
        Retorna lista de (timestamp, valor) para gráficos históricos
        """
        session = self.Session()

        with self.lock:
            results = (
                session.query(
                    CompressorData.timestamp,
                    getattr(CompressorData, campo)
                )
                .filter(CompressorData.timestamp.between(t_ini, t_fim))
                .all()
            )

        session.close()
        return results
