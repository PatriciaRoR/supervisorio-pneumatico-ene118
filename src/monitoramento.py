"""
Módulo de monitoramento em tempo real do sistema pneumático.
Responsável pela leitura, organização das variáveis do processo
e atuação básica no sistema.
"""

import time
import struct
from pyModbusTCP.client import ModbusClient


class Monitoramento(object):
    """
    Classe responsável pelo monitoramento e controle
    do sistema pneumático.
    """

    def __init__(self, ip='', port=502):
        """
        Inicializa o sistema de monitoramento e controle.
        """

        # 1. DEFINIÇÃO DAS TAGS DO PROCESSO (MONITORAMENTO)

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

            # POTÊNCIA ATIVA
            "ve.ativa_r_co":     {"addr": 735, "type": "4X", "div": 1},
            "ve.ativa_s_co":     {"addr": 736, "type": "4X", "div": 1},
            "ve.ativa_t_co":     {"addr": 737, "type": "4X", "div": 1},
            "ve.ativa_total_co": {"addr": 738, "type": "4X", "div": 1},

            # CORRENTES
            "ve.corrente_r_co":     {"addr": 726, "type": "4X", "div": 10},
            "ve.corrente_s_co":     {"addr": 727, "type": "4X", "div": 10},
            "ve.corrente_t_co":     {"addr": 728, "type": "4X", "div": 10},
            "ve.corrente_n_co":     {"addr": 729, "type": "4X", "div": 10},
            "ve.corrente_media_co": {"addr": 731, "type": "4X", "div": 10},
        }

        # 2. TAGS DE ATUAÇÃO E CONTROLE

        self._controls = {
            "liga_motor":     {"addr": 2,    "type": "coil"},
            "valvula_01":     {"addr": 3,    "type": "coil"},
            "vel_motor":      {"addr": 1313, "type": "4X"},
            "metodo_partida": {"addr": 1324, "type": "4X"}  # 0=direta | 1=soft | 2=inversor
        }

        # 3. ESTRUTURA DE MEDIÇÕES

        self._meas = {
            "timestamp": None,
            "values": {}
        }

        self.executando = False

        # 4. CLIENTE MODBUS

        self.client = ModbusClient(
            host=ip,
            port=port,
            auto_open=True,
            auto_close=False
        )

    # 5. LEITURA FLOAT (FP – 32 BITS)

    def _read_float(self, addr):
        regs = self.client.read_holding_registers(addr, 2)
        if regs and len(regs) == 2:
            packed = struct.pack(">HH", regs[0], regs[1])
            return struct.unpack(">f", packed)[0]
        return None

    # 6. LEITURA DAS VARIÁVEIS DO PROCESSO

    def readData(self):
        self._meas["timestamp"] = time.time()

        # limpa valores antigos para não reaproveitar dados
        self._meas["values"] = {}

        for nome, cfg in self._tags.items():

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

    # 7. LÓGICA DE ATUAÇÃO E CONTROLE

    def controle(self):
        """
        Executa ações de controle simples baseadas nas variáveis do processo.
        """

        pressao = self._meas["values"].get("co.pressao")

        # controle de liga/desliga do motor
        if pressao is not None:
            if pressao < 5:
                self.client.write_single_coil(
                    self._controls["liga_motor"]["addr"], True
                )
            elif pressao > 8:
                self.client.write_single_coil(
                    self._controls["liga_motor"]["addr"], False
                )

            # controle da válvula
            self.client.write_single_coil(
                self._controls["valvula_01"]["addr"],
                pressao > 6
            )

            # ajuste simples de velocidade do motor
            velocidade = int(min(max(pressao * 10, 0), 100))
            self.client.write_single_register(
                self._controls["vel_motor"]["addr"], velocidade
            )

    # 8. MÉTODO DE PARTIDA

    def set_metodo_partida(self, metodo):
        """
        Define o método de partida do motor.
        0 = direta | 1 = soft-starter | 2 = inversor
        """
        self.client.write_single_register(
            self._controls["metodo_partida"]["addr"], metodo
        )

    # 9. LOOP PRINCIPAL

    def executar_monitoramento(self, scan_time=1):
        self.executando = True

        while self.executando:
            self.readData()
            self.controle()
            time.sleep(scan_time)

    def parar_monitoramento(self):
        self.executando = False
