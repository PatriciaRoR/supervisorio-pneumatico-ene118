"""
Módulo de monitoramento em tempo real do sistema pneumático.
Responsável pela leitura e organização das variáveis do processo.
"""

import time
from pyModbusTCP.client import ModbusClient


class Monitoramento(object):
    """
    Classe responsável pelo monitoramento das variáveis do sistema pneumático.
    """

    def __init__(self, ip='', port=502):
        """
        Inicializa variáveis, tags, medições e cliente Modbus.
        """

        # Dicionário de variáveis
        self.variaveis = {
            "pressao_ar": {
                "endereco": 0,
                "tipo": "input",
                "valor": 0.0
            },
            "valvula_principal": {
                "endereco": 1,
                "tipo": "coil",
                "valor": False
            }
        }

        # Tags do processo
        self._tags = []
        for nome, var in self.variaveis.items():
            self._tags.append({
                "name": nome,
                "address": var["endereco"],
                "type": var["tipo"]
            })

        # Estrutura de medições
        self._meas = {
            "timestamp": None,
            "values": {}
        }

        self.executando = False

        # Cliente Modbus 
        self.client = ModbusClient(
            host=ip,
            port=port,
            auto_open=True,
            auto_close=False
        )

    def atualizar_variavel(self, nome, valor):
        timestamp = time.time()

        if nome in self.variaveis:
            self.variaveis[nome]["valor"] = valor
            self._meas["timestamp"] = timestamp
            self._meas["values"][nome] = valor

    def obter_variaveis(self):
        return self.variaveis

    def obter_medicoes(self):
        return self._meas

    # Leitura Modbus

    def readData(self):
        for tag in self._tags:
            try:
                if tag["type"] == "input":
                    val = self.client.read_input_registers(tag["address"], 1)
                    if val:
                        self.atualizar_variavel(tag["name"], val[0])

                elif tag["type"] == "coil":
                    val = self.client.read_coils(tag["address"], 1)
                    if val:
                        self.atualizar_variavel(tag["name"], bool(val[0]))

            except Exception as e:
                print(f"Erro Modbus ({tag['name']}): {e}")

    def executar_monitoramento(self, scan_time=1):
        self.executando = True

        while self.executando:
            # leitura real via Modbus
            self.readData()
            time.sleep(scan_time)

    def parar_monitoramento(self):
        self.executando = False
