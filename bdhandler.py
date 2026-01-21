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
    Tabela de histórico do compressor - Conforme tags.py
    """
    __tablename__ = "compressor_data"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)

    # ---- TAGS DE PROCESSO ----
    temp_enrol_r = Column(Float)        # co.temp_enrol_r: Temperatura Enrolamento R
    temp_carcaca = Column(Float)        # co.temp_carcaca: Temperatura Carcaça
    vel_saida_ar = Column(Float)        # co.vel_saida_ar: Velocidade de saída de ar
    press_tubo_azul = Column(Float)     # co.press_tubo_azul: Pressão Tubo azul
    torque = Column(Float)              # co.torque: Torque
    pressao = Column(Float)             # co.pressao: Pressão
    vazao = Column(Float)               # co.vazao: Vazão
    press_reservatorio = Column(Float)  # co.press_reservatorio: Pressão no Reservatório
    vazao_ramo_v01 = Column(Float)      # co.vazao_ramo_v01: Vazão no Ramo da Válvula 01
    med_torque = Column(Float)          # co.med_torque: Medida do Torque
    
    # ---- TAGS ELÉTRICAS - TENSÕES FASE-NEUTRO ----
    v_rn = Column(Float)                # co.v_rn: Tensão Fase R e Neutro
    v_sn = Column(Float)                # co.v_sn: Tensão Fase S e Neutro
    v_tn = Column(Float)                # co.v_tn: Tensão Fase T e Neutro
    
    # ---- TENSÕES FASE-FASE ----
    v_rs = Column(Float)                # co.v_rs: Tensão R-S
    v_st = Column(Float)                # co.v_st: Tensão S-T
    v_tr = Column(Float)                # co.v_tr: Tensão T-R
    
    # ---- POTÊNCIAS ATIVA POR FASE ----
    p_kw_r = Column(Float)              # co.p_kw_r: Potência Fase R
    p_kw_s = Column(Float)              # co.p_kw_s: Potência Fase S
    p_kw_t = Column(Float)              # co.p_kw_t: Potência Fase T
    p_kw_total = Column(Float)          # co.p_kw_total: Potência Total
    
    # ---- CORRENTES POR FASE ----
    i_r = Column(Float)                 # co.i_r: Corrente Fase R
    i_s = Column(Float)                 # co.i_s: Corrente Fase S
    i_t = Column(Float)                 # co.i_t: Corrente Fase T
    i_n = Column(Float)                 # co.i_n: Corrente Neutro
    i_media = Column(Float)             # co.i_media: Corrente Média


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

                # Verificar se é uma mensagem de monitoramento válida
                if dados and dados.get("tipo") == "dados_monitoramento":
                    dados_payload = dados.get("dados", {})
                    valores = dados_payload.get("values", {})
                    timestamp = dados_payload.get("timestamp")
                    
                    def _get(*keys):
                        for k in keys:
                            if k in valores and valores.get(k) is not None:
                                return valores.get(k)
                        return None

                    if timestamp and valores:
                        row = CompressorData(
                            timestamp=datetime.fromtimestamp(timestamp),
                            
                            # TAGS DE PROCESSO
                            temp_enrol_r=_get("co.temp_enrol_r", "co.temp_r"),
                            temp_carcaca=_get("co.temp_carcaca", "co.temp_carc"),
                            vel_saida_ar=_get("co.vel_saida_ar", "co.encoder"),
                            press_tubo_azul=_get("co.press_tubo_azul"),
                            torque=_get("co.torque"),
                            pressao=_get("co.pressao"),
                            vazao=_get("co.vazao", "co.fit03", "co.fit02"),
                            press_reservatorio=_get("co.press_reservatorio"),
                            vazao_ramo_v01=_get("co.vazao_ramo_v01"),
                            med_torque=_get("co.med_torque"),
                            
                            # TAGS ELÉTRICAS - TENSÕES FASE-NEUTRO
                            v_rn=_get("co.v_rn"),
                            v_sn=_get("co.v_sn"),
                            v_tn=_get("co.v_tn"),
                            
                            # TENSÕES FASE-FASE
                            v_rs=_get("co.v_rs", "co.tensao_rs"),
                            v_st=_get("co.v_st", "co.tensao_st"),
                            v_tr=_get("co.v_tr", "co.tensao_tr"),
                            
                            # POTÊNCIAS ATIVA POR FASE
                            p_kw_r=_get("co.p_kw_r"),
                            p_kw_s=_get("co.p_kw_s"),
                            p_kw_t=_get("co.p_kw_t"),
                            p_kw_total=_get("co.p_kw_total", "co.ativa_total"),
                            
                            # CORRENTES POR FASE
                            i_r=_get("co.i_r", "co.corrente_r"),
                            i_s=_get("co.i_s", "co.corrente_s"),
                            i_t=_get("co.i_t", "co.corrente_t"),
                            i_n=_get("co.i_n"),
                            i_media=_get("co.i_media", "co.i_media"),
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
        Ordenado por timestamp
        """
        session = self.Session()

        with self.lock:
            results = (
                session.query(
                    CompressorData.timestamp,
                    getattr(CompressorData, campo)
                )
                .filter(CompressorData.timestamp.between(t_ini, t_fim))
                .order_by(CompressorData.timestamp)  # IMPORTANTE: ordenar por tempo
                .all()
            )

        session.close()
        return results