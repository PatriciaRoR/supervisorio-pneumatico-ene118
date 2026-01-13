import threading
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
    timestamp = Column(DateTime, default=datetime.now)

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


# =========================================================
# BD HANDLER
# =========================================================
class BDHandler:
    def __init__(self, ip="127.0.0.1", port=5020, device_id=0):
        # ---------- BANCO ----------
        self.engine = create_engine(
            "sqlite:///compressor.db",
            connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        # ---------- MODBUS ----------
        self.client = ModbusTcpClient(host=ip, port=port)
        self.client.connect()
        self.device_id = device_id

        # ---------- CONTROLE ----------
        self.lock = threading.Lock()
        self.running = False

    # =====================================================
    # THREAD DE AQUISIÇÃO / INSERÇÃO
    # =====================================================
    def start_insertion_thread(self, interval=1.0):
        self.running = True
        thread = threading.Thread(
            target=self._acquisition_loop,
            args=(interval,),
            daemon=True
        )
        thread.start()

    def stop(self):
        self.running = False
        self.client.close()

    def _acquisition_loop(self, interval):
        """
        Thread secundária:
        - Lê dados via MODBUS
        - Insere no banco usando ORM
        """
        session = self.Session()

        while self.running:
            try:
                rr = self.client.read_holding_registers(
                    address=0,
                    count=10,
                    device_id=self.device_id
                )

                if rr and not rr.isError():
                    r = rr.registers

                    row = CompressorData(
                        temp_enrolamento_r=r[0] / 10.0,
                        temp_carcaca=r[1] / 10.0,
                        velocidade_ar=float(r[2]),
                        pressao_tubo_azul=float(r[3]),
                        torque=float(r[4]),
                        pressao=float(r[5]),
                        vazao=float(r[6]),
                        pressao_reservatorio=float(r[7]),
                        vazao_valvula_01=float(r[8]),
                        torque_medido=float(r[9]),
                    )

                    with self.lock:
                        session.add(row)
                        session.commit()

            except Exception as e:
                print(f"[BDHandler] Erro MODBUS/DB: {e}")

            time.sleep(interval)

        session.close()

    # =====================================================
    # CONSULTA HISTÓRICA (THREAD PRINCIPAL)
    # =====================================================
    def get_history(self, variable_name, t_ini, t_fim):
        """
            Retorna lista de (timestamp, valor)
        """
        session = self.Session()

        with self.lock:
            results = (
                session.query(
                    CompressorData.timestamp,
                    getattr(CompressorData, variable_name)
                )
                .filter(CompressorData.timestamp.between(t_ini, t_fim))
                .all()
            )

        session.close()
        return results