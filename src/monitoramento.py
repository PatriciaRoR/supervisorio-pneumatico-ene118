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

# Ponte de comunicação entre módulos (Thread-safe)
from comunicacao import com, Mensagem


class Monitoramento:
    """
    Classe responsável pela comunicação direta com o CLP.

    Esta classe abstrai o acesso MODBUS, oferecendo métodos de:
    - Leitura das variáveis do processo
    - Escrita de comandos de controle
    """

    def __init__(self, ip="127.0.0.1", port=502):
        """
        Construtor da classe.

        Aqui são definidos:
        - O mapa de memória do CLP (tags)
        - As variáveis de controle
        - O cliente Modbus
        - O registro de callbacks de comandos
        """

        # 1. MAPA DE MEMÓRIA DO CLP (TAGS DE MONITORAMENTO)

        # Campos utilizados:
        #   addr -> endereço Modbus
        #   type -> tipo da variável:
        #           FP  = float IEEE 754 (32 bits, ocupa 2 registradores)
        #           4X  = holding register (inteiro)
        #           BIT = bit dentro de um holding register
        #   div  -> fator de escala aplicado ao valor lido
  
        self._tags = {

            #ESTADOS GERAIS E PARTIDA 
            "co.sel_driver":  {"addr": 1324, "type": "4X", "div": 1},
            "co.habilita":    {"addr": 1328, "type": "4X", "div": 1},
            "co.seg_manauto": {"addr": 1330, "type": "4X", "div": 1},

            # VÁLVULAS XV (BITS NO REGISTRADOR 712) 

            # Todas as válvulas estão compactadas em um único registrador
            # Cada bit representa o estado de uma válvula
            "co.xv1": {"addr": 712, "bit": 0, "type": "BIT"},
            "co.xv2": {"addr": 712, "bit": 1, "type": "BIT"},
            "co.xv3": {"addr": 712, "bit": 2, "type": "BIT"},
            "co.xv4": {"addr": 712, "bit": 3, "type": "BIT"},
            "co.xv5": {"addr": 712, "bit": 4, "type": "BIT"},
            "co.xv6": {"addr": 712, "bit": 5, "type": "BIT"},

            # VARIÁVEIS DE PROCESSO 
            "co.pressao": {"addr": 714, "type": "FP", "div": 1},
            "co.fit02":   {"addr": 716, "type": "FP", "div": 1},
            "co.fit03":   {"addr": 718, "type": "FP", "div": 1},

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

            # GRANDEZAS ELÉTRICAS 
            "co.corrente_r": {"addr": 840, "type": "4X", "div": 10},
            "co.corrente_s": {"addr": 841, "type": "4X", "div": 10},
            "co.corrente_t": {"addr": 842, "type": "4X", "div": 10},

            "co.tensao_rs": {"addr": 847, "type": "4X", "div": 10},
            "co.tensao_st": {"addr": 848, "type": "4X", "div": 10},
            "co.tensao_tr": {"addr": 849, "type": "4X", "div": 10},

            "co.ativa_total": {"addr": 855, "type": "4X", "div": 1},
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
            "timestamp": None,  #Reserva um espaço para guardar o instante da última leitura.
            "values": {}        #Começa com none porque ainda não realizou leitura.
        }

    
        # 3. INICIALIZAÇÃO DO CLIENTE MODBUS
        
        self.client = ModbusClient(
            host=ip,
            port=port,
            auto_open=True,
            auto_close=False
        )

        
        # 4. REGISTRO DE COMANDOS DA INTERFACE
        
        # A interface gráfica envia comandos através da ponte de comunicação.
        # Aqui registramos o callback.

        com.receber("comando_kivy", self._processar_comando_kivy)

    
    # 5. FUNÇÕES DE LEITURA MODBUS
    
    def _read_float(self, addr):
        """
        Lê dois registradores consecutivos e converte
        para float IEEE 754 (32 bits).
        """
        regs = self.client.read_holding_registers(addr, 2)
        if regs and len(regs) == 2:
            return struct.unpack(">f", struct.pack(">HH", regs[0], regs[1]))[0]
        return None

    def _read_bit(self, addr, bit):
        """
        Lê um bit específico dentro de um registrador.
        Utilizado para leitura do estado das válvulas.
        """
        reg = self.client.read_holding_registers(addr, 1)
        if reg:
            return (reg[0] >> bit) & 1
        return None

    
    # 6. LEITURA DAS VARIÁVEIS DO PROCESSO
    
    def readData(self):
        """
        Realiza a leitura de TODAS as variáveis configuradas
        no mapa de memória do CLP.

        Esta função é chamada periodicamente
        por uma thread externa (Thread 2).
        """
        # Gráficos em função do tempo, histórico no banco, verificar se os dados estão atualizados.

        self._meas["timestamp"] = time.time()  #horário atual do sistema 
        self._meas["values"] = {}  #Cria um dicionário vazio


        for nome, cfg in self._tags.items():
            try:
                # Identifica o tipo da variável e faz a leitura adequada
                if cfg["type"] == "FP":
                    valor = self._read_float(cfg["addr"])
                elif cfg["type"] == "BIT":
                    valor = self._read_bit(cfg["addr"], cfg["bit"])
                else:  # 4X padrão
                    reg = self.client.read_holding_registers(cfg["addr"], 1)
                    valor = reg[0] if reg else None

                # Aplica fator de escala, se existir
                if valor is not None:
                    self._meas["values"][nome] = valor / cfg.get("div", 1)

            except Exception as e:
                print(f"Erro Modbus ({nome}): {e}")

        # Envia os dados para a ponte de comunicação
        com.enviar(Mensagem(
            tipo="dados_monitoramento",
            dados=self._meas.copy(),
            origem="monitoramento"
        ))

    
    # 7. ATUAÇÃO E CONTROLE DO PROCESSO
    
    def set_metodo_partida(self, metodo):
        """
        Seleciona o tipo de partida do motor.

        Parâmetro:
        - metodo:
            1 = Soft-starter
            2 = Inversor de frequência
            3 = Partida direta
        """
        self._ultimo_driver = metodo
        self.client.write_single_register(
            self._controls["sel_driver"]["addr"], metodo
        )

    def ligar_motor(self, comando):
        """
        Envia comando de atuação ao motor.

        Parâmetro:
        - comando:
            1 = Liga
            0 = Desliga
            2 = Reset
        """
        if self._ultimo_driver == 1:
            self.client.write_single_register(
                self._controls["soft"]["addr"], comando
            )
        elif self._ultimo_driver == 2:
            self.client.write_single_register(
                self._controls["inversor"]["addr"], comando
            )
        elif self._ultimo_driver == 3:
            self.client.write_single_register(
                self._controls["direta"]["addr"], comando
            )

    def set_velocidade(self, valor):
        """
        Define a velocidade do motor
        quando o sistema estiver operando
        em modo inversor.
        """
        self.client.write_single_register(
            self._controls["vel"]["addr"], int(valor)
        )

    def set_valvula(self, numero, aberta):
        """
        Aciona uma válvula XV individualmente.

        Parâmetros:
        - numero : número da válvula (1 a 6)
        - aberta : True  -> abre a válvula
                   False -> fecha a válvula
        """
        if numero < 1 or numero > 6:
            return

        # Lê o estado atual do registrador de válvulas
        reg = self.client.read_holding_registers(712, 1)

        if not reg:          #Lê o registrador 712, que contém o estado de todas as válvulas.
            return

        # Extrai o valor inteiro do registrador

        valor = reg[0]     # É o valor inteiro
        bit = numero - 1   # converte XV1–XV6 para bits 0–5

        # Atualiza apenas o bit correspondente
        if aberta:
            valor |= (1 << bit)    #abre valvula
        else:
            valor &= ~(1 << bit)   #fecha valvula

        # Envia o novo estado de todas as válvulas para o CLP
        self.client.write_single_register(712, valor)

    def _write_float(self, addr, valor):
        """
        Escreve um valor float IEEE 754 (32 bits)
        em dois registradores consecutivos do CLP.
        """
        regs = struct.unpack(">HH", struct.pack(">f", float(valor)))
        self.client.write_multiple_registers(addr, list(regs))

    def set_pid(self, p=None, i=None, d=None, sp=None, mv=None):
        """
        Atualiza os parâmetros do controlador PID.

        Os parâmetros que forem None NÃO são alterados.
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
    
    def _processar_comando_kivy(self, comando):
        """
        Recebe comandos enviados pela interface gráfica
        e executa a ação correspondente no CLP.

        O formato do comando é um dicionário com a chave "acao".
        """
        acao = comando.get("acao")

        if acao == "set_driver":
            self.set_metodo_partida(comando["valor"])

        elif acao == "motor":
            self.ligar_motor(comando["valor"])

        elif acao == "velocidade":
            self.set_velocidade(comando["valor"])

        elif acao == "valvula":
            self.set_valvula(
                comando["numero"],
                comando["aberta"]
            )

        elif acao == "pid":
            self.set_pid(**comando["parametros"])
