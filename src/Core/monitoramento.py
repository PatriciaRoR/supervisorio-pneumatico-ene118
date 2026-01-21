"""
Módulo de monitoramento e controle do sistema pneumático (compressor).

Responsabilidades deste módulo:
- Comunicação MODBUS TCP com o CLP da planta
- Leitura contínua das variáveis do processo (monitoramento)
- Escrita de comandos no CLP (atuação e controle)
- Comunicação com a interface gráfica (Kivy) e com o banco de dados
"""

import time
import struct
from pyModbusTCP.client import ModbusClient
from pymodbus.client import ModbusTcpClient
import logging
from threading import Lock


logging.getLogger("pyModbusTCP").setLevel(logging.WARNING)

# Ponte de comunicação entre módulos (Thread-safe)


class Monitoramento:
    """
    Classe responsável pela comunicação direta com o CLP.

    Esta classe abstrai o acesso MODBUS, oferecendo métodos de:
    - Leitura das variáveis do processo
    - Escrita de comandos de controle
    """

    def __init__(self):
        """
        Construtor da classe.

        Aqui são definidos:
        - O mapa de memória do CLP (tags)
        - As variáveis de controle
        - O cliente Modbus
        """
        self.ip = "10.15.30.182"
        self.port = 502

        self._lock = Lock()

        # 1. MAPA DE MEMÓRIA DO CLP (TAGS DE MONITORAMENTO)

        # Campos utilizados:
        #   addr -> endereço Modbus
        #   type -> tipo da variável:
        #           FP  = float IEEE 754 (32 bits, ocupa 2 registradores)
        #           4X  = holding register (inteiro)
        #           BIT = bit dentro de um holding register
        #   div  -> fator de escala aplicado ao valor lido

        self._tags = {

            # ESTADOS GERAIS E PARTIDA
            "co.sel_driver":  {"addr": 1324, "type": "4X", "div": 1},
            "co.indica_driver":  {"addr": 1324, "type": "4X", "div": 1},
            "co.habilita":    {"addr": 1328, "type": "4X", "div": 1},
            "co.seg_manauto": {"addr": 1330, "type": "4X", "div": 1},

            # VÁLVULAS XV (BITS NO REGISTRADOR 712)

            # Todas as válvulas estão compactadas em um único registrador
            # Cada bit representa o estado de uma válvula
            "co.xv2": {"addr": 712, "bit": 1, "type": "BIT"},
            "co.xv3": {"addr": 712, "bit": 2, "type": "BIT"},
            "co.xv4": {"addr": 712, "bit": 3, "type": "BIT"},
            "co.xv5": {"addr": 712, "bit": 4, "type": "BIT"},
            "co.xv6": {"addr": 712, "bit": 5, "type": "BIT"},

            # VARIÁVEIS DE PROCESSO
            "co.pressao": {"addr": 714, "type": "FP", "div": 1},
            "co.fit03":   {"addr": 716, "type": "FP", "div": 1},

            # PID
            # PV = variável de processo
            # MV = variável manipulada
            "co.sel_pid": {"addr": 1332, "type": "4X", "div": 1},
            "co.pv_pid":  {"addr": 1314, "type": "FP", "div": 1},
            "co.mv_pid":  {"addr": 814,  "type": "FP", "div": 1},

            # TEMPERATURAS DO MOTOR
            "co.temp_r":    {"addr": 700, "type": "FP", "div": 10},
            "co.temp_s":    {"addr": 702, "type": "FP", "div": 10},
            "co.temp_t":    {"addr": 704, "type": "FP", "div": 10},
            "co.temp_carc": {"addr": 706, "type": "FP", "div": 10},

            # GRANDEZAS MECÂNICAS
            "co.encoder": {"addr": 884,  "type": "FP", "div": 1},
            "co.torque":  {"addr": 1420, "type": "FP", "div": 1},

            # CORRENTES
            "co.corrente_r": {"addr": 840, "type": "4X", "div": 10},
            "co.corrente_s": {"addr": 841, "type": "4X", "div": 10},
            "co.corrente_t": {"addr": 842, "type": "4X", "div": 10},
            "co.corrente_n": {"addr": 843, "type": "4X", "div": 10},
            "co.corrente_media": {"addr": 845, "type": "4X", "div": 10},

            # TENSÕES
            "co.tensao_rs": {"addr": 847, "type": "4X", "div": 10},
            "co.tensao_st": {"addr": 848, "type": "4X", "div": 10},
            "co.tensao_tr": {"addr": 849, "type": "4X", "div": 10},
            "co.ativa_total": {"addr": 855, "type": "4X", "div": 1},

            # FATOR DE POTÊNCIA
            "co.fp_r": {"addr": 868, "type": "4X", "div": 1000},
            "co.fp_s": {"addr": 869, "type": "4X", "div": 1000},
            "co.fp_t": {"addr": 870, "type": "4X", "div": 1000},
            "co.fp_total": {"addr": 871, "type": "4X", "div": 1000},
            # THD
            "co.thd_tensao_rs": {"addr": 804, "type": "4X", "div": 10},
            "co.thd_tensao_st": {"addr": 805, "type": "4X", "div": 10},
            "co.thd_tensao_tr": {"addr": 806, "type": "4X", "div": 10},
            "co.thd_corrente_r": {"addr": 874, "type": "4X", "div": 10},
            "co.thd_corrente_s": {"addr": 875, "type": "4X", "div": 10},
            "co.thd_corrente_t": {"addr": 876, "type": "4X", "div": 10},
            "co.thd_corrente_n": {"addr": 877, "type": "4X", "div": 10},

        }

        # 2. MAPA DE ATUAÇÃO (COMANDOS DE ESCRITA NO CLP)

        # Estes registradores NÃO são monitorados continuamente,
        # apenas escritos quando o operador realiza uma ação.

        self._controls = {

            # Seleção do método de partida
            "sel_driver": {"addr": 1324},  # 1=Soft | 2=Inversor | 3=Direta

            # Comandos de partida
            # 1 = Liga | 0 = Desliga | 2 = Reset
            "soft":     {"addr": 1316},
            "inversor": {"addr": 1312},
            "direta":   {"addr": 1319},

            # Velocidade do motor (quando em modo inversor)
            "vel": {"addr": 1313},

            # Parâmetros do PID
            "sel_pid": {"addr": 1332},
            "p":       {"addr": 1304},
            "i":       {"addr": 1306},
            "d":       {"addr": 1308},
            "sp":      {"addr": 1302},
            "mv":      {"addr": 1310},
        }

        # Guarda o último método de partida selecionado
        # Necessário para saber qual registrador acionar
        self._ultimo_driver = 3  # Direta por padrão

        # Estrutura interna de medições
        self._meas = {
            # Reserva um espaço para guardar o instante da última leitura.
            "timestamp": None,
            # Começa vazio porque ainda não realizou leitura.
            "values": {}
        }

        # 3. INICIALIZAÇÃO DO CLIENTE MODBUS

        self.client = ModbusClient(
            host=self.ip,
            port=self.port,
            auto_open=False, #Você controla quando a conexão é aberta
            auto_close=False, #A conexão permanece aberta
        )
        self.client.open()

    # 5. FUNÇÕES DE LEITURA MODBUS

    def _read_float(self, addr):
        """
        Lê dois registradores consecutivos e converte
        para float IEEE 754 (32 bits).
        """
        regs = self.client.read_holding_registers(addr, 2)  #Função Modbus padrão
        val = ModbusTcpClient.convert_from_registers(   #Recebe registradores Modbus
            regs, ModbusTcpClient.DATATYPE.FLOAT32, word_order='little')  ## Interpreta como tipo numérico
        return val  #retorna valor python

    def _read_bit(self, addr, bit):
        """
        Lê um bit específico dentro de um registrador.
        Utilizado para leitura do estado das válvulas.
        """
        reg = self.client.read_holding_registers(addr)
        if reg:  # Antes de acessar o valor, eu verifico se a leitura foi bem-sucedida.
            return (reg[0] >> bit) & 1 #desloco um bit ate a posição menos significativa e garanto retorno 0 ou 1
        return None #Evita confundir erro com 0 (válvula fechada)

    # 6. LEITURA DAS VARIÁVEIS DO PROCESSO

    def readData(self):
        """
        Realiza a leitura de TODAS as variáveis configuradas
        no mapa de memória do CLP.

        Esta função é chamada periodicamente
        por uma thread externa.
        """

        self._meas["timestamp"] = time.time() #Cada ciclo de leitura é associado a um timestamp.
        self._meas["values"] = {} #Cada ciclo reflita somente valores atuais
        with self._lock: #O Lock garante integridade da comunicação Modbus durante o ciclo de leitura.
            for nome, cfg in self._tags.items(): #Percorre todo o mapa de memória
                try:
                    # Leitura conforme o tipo
                    if cfg["type"] == "FP":
                        valor = self._read_float(cfg["addr"])
                    elif cfg["type"] == "BIT":
                        valor = self._read_bit(cfg["addr"], cfg["bit"])

                    else:  # 4X
                        reg = self.client.read_holding_registers(cfg["addr"], 1)
                        valor = reg[0] if reg else None

                    # Aplica fator de escala
                    if valor is not None:
                        self._meas["values"][nome] = valor / cfg.get("div", 1)  #Converte valor bruto para unidade de engenharia.

                except Exception as e:
                    print(f"⚠️ Erro Modbus ({nome}): {e}")


    # 7. ATUAÇÃO E CONTROLE DO PROCESSO

    def set_metodo_partida(self, metodo):
        """
        Seleciona o tipo de partida do motor.
        """
        with self._lock: # O Lock garante que a escrita no CLP não conflite com leituras simultâneas.
            self.client.write_single_register(self._controls["sel_driver"]["addr"], metodo ) #Busca o endereço configurado no mapa de controle


    def ligar_motor(self):
        with self._lock:

            try: 
                tipo_partida = self._meas["values"].get("co.indica_driver") #O comando se baseia no estado real informado pelo CLP.

                if tipo_partida == 1:  # Soft-Start
                    is_active = self.client.read_holding_registers(886, 1)[0]
                    if is_active:
                        self.client.write_single_register( 1316, 0)
                    else:
                        self.client.write_single_register( 1316, 1)

                elif tipo_partida == 2:  # Inversor
                    is_active = self.client.read_holding_registers(888, 1)[0]
                    if is_active:
                        self.client.write_single_register( 1312, 0)
                    else:
                        self.client.write_single_register( 1312, 1)

                elif tipo_partida == 3:  # Direta
                    is_active = self.client.read_holding_registers(890, 1)[0]
                    if is_active:
                        self.client.write_single_register( 1319, 0)
                    else:
                        self.client.write_single_register( 1319, 1)
                else:
                    print("vaor lido errado")
            except Exception as e:
                print("Erro de liga_motor:", e.args)
            
    def abre_valvula(self, numero):
        """
        Aciona uma válvula XV individualmente (toggle).
        """
        if numero < 1 or numero > 6:
            return
        with self._lock:
            reg = self.client.read_holding_registers(712, 1)
        if not reg:
            return
        valor = reg[0]
        bit = numero - 1

        # Toggle: se estiver fechada abre, se estiver aberta fecha
    
        if (valor >> bit) & 1 == 0:
            valor |= (1 << bit)
        else:
            valor &= ~(1 << bit)

        with self._lock:
            self.client.write_single_register(712, valor)
        
    def set_velocidade(self, valor):
        """
        Define a velocidade do motor
        quando o sistema estiver operando
        em modo inversor.
        """
        with self._lock:
            self.client.write_single_register(
                self._controls["vel"]["addr"], int(valor)
            )

    def _write_float(self, addr, valor):
        """
        Escreve um valor float IEEE 754 (32 bits)
        em dois registradores consecutivos do CLP.
        """
        # regs = struct.unpack(">HH", struct.pack(">f", float(valor)))
        with self._lock:
            regs = ModbusTcpClient.convert_to_registers(
                float(valor), ModbusTcpClient.DATATYPE.FLOAT32, word_order='little')
            self.client.write_multiple_registers(addr, list(regs))

    def set_pid(self, p=None, i=None, d=None, sp=None, mv=None):
        """
        Atualiza os parâmetros do controlador PID.
        """
        if p is not None:
            self._write_float(self._controls["p"]["addr"], p)
        if i is not None:
            self._write_float(self._controls["i"]["addr"], i)
        if d is not None:
            self._write_float(self._controls["d"]["addr"], d)
        if sp is not None:
            self._write_float(self._controls["sp"]["addr"], sp)
        if mv is not None:
            self._write_float(self._controls["mv"]["addr"], mv)

    # 8. PROCESSAMENTO DE COMANDOS DA INTERFACE

    def executar_monitoramento(self, scan_time=2):
        """
        Loop principal de monitoramento.
        Executa a leitura periódica do CLP.
        """

        while True:
            try:
                if self.client.is_open:
                    self.readData()
                else:
                    print("cliente fechado")
            except Exception as e:
                print(f"⚠️ Erro no monitoramento: {e}")
            time.sleep(scan_time)