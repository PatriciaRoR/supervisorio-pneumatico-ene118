import time
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

from pymodbus.client import ModbusTcpClient

# =========================================================
# ORM
# =========================================================
Base = declarative_base()


class CompressorData(Base):
    __tablename__ = "compressor_data"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    temp_enrolamento_r = Column(Float)
    temp_carcaca = Column(Float)
    velocidade_ar = Column(Float)
    pressao_tubo_azul = Column(Float)
    torque = Column(Float)
    pressao = Column(Float)
    vazao = Column(Float)
    pressao_reservatorio = Column(Float)
    vazao_valvula_01 = Column(Float)
    torque_medido = Column(Float)


