"""
Módulo de monitoramento em tempo real do sistema pneumático.
Responsável pela leitura e organização das variáveis do processo.
"""

import time
import struct
from pyModbusTCP.client import ModbusClient


class Monitoramento(object):
    """
    Classe responsável pelo monitoramento das variáveis do sistema pneumático.
    """

    def __init__(self, ip='', port=502):
        """
        Inicializa o sistema de monitoramento.
        """

        # 1. DEFINIÇÃO DAS TAGS DO PROCESSO

        self._tags = {

            # VARIÁVEIS PRINCIPAIS
            "bc.torque":        {"addr": None, "type": "FP", "div": 1},
            "bc.pit01":         {"addr": None, "type": "FP", "div": 1},
            "bc.fit01":         {"addr": None, "type": "FP", "div": 1},

            "ve.pit01":         {"addr": 1224, "type": "FP", "div": 10},
            "ve.velocidade":    {"addr": 712,  "type": "FP", "div": 1},

            "co.pressao":       {"addr": 714,  "type": "FP", "div": 1},
            "co.fit03":         {"addr": 718,  "type": "FP", "div": 1},
            "co.torque":        {"addr": 1420, "type": "FP", "div": 1},

            "es.temp_r":        {"addr": None, "type": "FP", "div": 1},
            "es.temp_carc":     {"addr": None, "type": "FP", "div": 1},

            # VARIÁVEIS ELÉTRICAS
            "es.thd_tensao_rn": {"addr": 800, "type": "4X", "div": 10},
            "es.thd_tensao_sn": {"addr": 801, "type": "4X", "div": 10},
            "es.thd_tensao_tn": {"addr": 802, "type": "4X", "div": 10},
            "es.thd_tensao_rs": {"addr": 804, "type": "4X", "div": 10},
            "es.thd_tensao_st": {"addr": 805, "type": "4X", "div": 10},
            "es.thd_tensao_tr": {"addr": 806, "type": "4X", "div": 10},

            # POTÊNCIA ATIVA DO COMPRESSOR
            "ve.ativa_r_co":     {"addr": 735, "type": "4X", "div": 1},
            "ve.ativa_s_co":     {"addr": 736, "type": "4X", "div": 1},
            "ve.ativa_t_co":     {"addr": 737, "type": "4X", "div": 1},
            "ve.ativa_total_co": {"addr": 738, "type": "4X", "div": 1},

            # CORRENTES DO COMPRESSOR 
            "ve.corrente_r_co":     {"addr": 726, "type": "4X", "div": 10},
            "ve.corrente_s_co":     {"addr": 727, "type": "4X", "div": 10},
            "ve.corrente_t_co":     {"addr": 728, "type": "4X", "div": 10},
            "ve.corrente_n_co":     {"addr": 729, "type": "4X", "div": 10},
            "ve.corrente_media_co": {"addr": 731, "type": "4X", "div": 10},
        }

        # 2. ESTRUTURA DE MEDIÇÕES
    
        self._meas = {          #armazena a última leitura realizada
            "timestamp": None,  #instante da leitura 
            "values": {}        #dicionário com as variáveis lidas 
        }

        # Flag de execução do monitoramento
        self.executando = False

        # 3. CLIENTE MODBUS

        """
        Responsável pela comunicação com o CLP via protocolo Modbus TCP.
        """

        self.client = ModbusClient(
            host=ip,
            port=port,
            auto_open=True,
            auto_close=False
        )

    # 4. LEITURA DE VARIÁVEIS FLOAT (FP – 32 BITS)

    def _read_float(self, addr):
        """
        Lê dois registradores Modbus consecutivos (32 bits)
        e converte o valor para float no padrão IEEE 754.
        """
        regs = self.client.read_holding_registers(addr, 2)
        if regs and len(regs) == 2:
            packed = struct.pack(">HH", regs[0], regs[1])
            return struct.unpack(">f", packed)[0]
        return None


    # 5. LEITURA DAS VARIÁVEIS DO PROCESSO

    def readData(self):
        """
        Realiza a leitura de todas as variáveis definidas em _tags
        e atualiza a estrutura de medições (_meas).
        """

        self._meas["timestamp"] = time.time()

        for nome, cfg in self._tags.items():

            # Ignora variáveis ainda sem endereço definido
            if cfg["addr"] is None:
                continue

            try:
                if cfg["type"] == "FP":
                    valor = self._read_float(cfg["addr"])
                    if valor is not None:
                        self._meas["values"][nome] = valor / cfg["div"]

                elif cfg["type"] == "4X":
                    reg = self.client.read_holding_registers(cfg["addr"], 1)
                    if reg:
                        self._meas["values"][nome] = reg[0] / cfg["div"]

            except Exception as e:
                print(f"Erro Modbus ({nome}): {e}")


    # 6. LOOP DE MONITORAMENTO

    def executar_monitoramento(self, scan_time=1):
        """
        Executa o monitoramento contínuo do processo.
        """

        self.executando = True

        while self.executando:
            self.readData()
            time.sleep(scan_time)

    def parar_monitoramento(self):
        """
        Interrompe o ciclo de monitoramento.
        """
        self.executando = False
