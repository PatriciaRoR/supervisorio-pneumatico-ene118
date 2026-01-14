"""
Módulo de monitoramento em tempo real do sistema pneumático (compressor).

"""

import time
import struct
from pyModbusTCP.client import ModbusClient

# Comunicação entre módulos (Kivy / BD / Backend)
from comunicacao import com, Mensagem


class Monitoramento(object):
    """
    Classe responsável pelo monitoramento e controle
    do sistema pneumático (compressor).
    """

    def __init__(self, ip="127.0.0.1", port=502):
        """
        Inicializa o sistema de monitoramento e controle.

        """

        # 1. TAGS DE MONITORAMENTO (≥ 25 VARIÁVEIS REAIS)
        
        self._tags = {

            # Processo Pneumático 
            "co.pressao":        {"addr": 714, "type": "FP", "div": 1},
            "co.fit03":          {"addr": 718, "type": "FP", "div": 1},
            "co.torque":         {"addr": 1420, "type": "FP", "div": 1},
            "co.velocidade":     {"addr": 712, "type": "FP", "div": 1},

            # Temperaturas
            "co.temp_r":         {"addr": 720, "type": "FP", "div": 1},
            "co.temp_s":         {"addr": 721, "type": "FP", "div": 1},
            "co.temp_t":         {"addr": 722, "type": "FP", "div": 1},
            "co.temp_carc":      {"addr": 723, "type": "FP", "div": 1},

            # Correntes 
            "co.corrente_r":     {"addr": 726, "type": "4X", "div": 10},
            "co.corrente_s":     {"addr": 727, "type": "4X", "div": 10},
            "co.corrente_t":     {"addr": 728, "type": "4X", "div": 10},
            "co.corrente_n":     {"addr": 729, "type": "4X", "div": 10},
            "co.corrente_media": {"addr": 731, "type": "4X", "div": 10},

            # Potências
            "co.ativa_r":        {"addr": 735, "type": "4X", "div": 1},
            "co.ativa_s":        {"addr": 736, "type": "4X", "div": 1},
            "co.ativa_t":        {"addr": 737, "type": "4X", "div": 1},
            "co.ativa_total":    {"addr": 738, "type": "4X", "div": 1},
            "co.reativa_total":  {"addr": 859, "type": "4X", "div": 1},
            "co.aparente_total": {"addr": 863, "type": "4X", "div": 1},

            # Tensões 
            "co.tensao_r":       {"addr": 820, "type": "4X", "div": 10},
            "co.tensao_s":       {"addr": 821, "type": "4X", "div": 10},
            "co.tensao_t":       {"addr": 822, "type": "4X", "div": 10},

            # Qualidade de Energia 
            "co.thd_r":          {"addr": 800, "type": "4X", "div": 10},
            "co.thd_s":          {"addr": 801, "type": "4X", "div": 10},
            "co.thd_t":          {"addr": 802, "type": "4X", "div": 10},
        }

        # 2. TAGS DE ATUAÇÃO E CONTROLE
       
        self._controls = {
            "liga_motor":     {"addr": 2,    "type": "coil"},
            "valvula_01":     {"addr": 3,    "type": "coil"},
            "vel_motor":      {"addr": 1313, "type": "4X"},   # 0–100 %
            "metodo_partida": {"addr": 1324, "type": "4X"}    # 0=direta | 1=soft | 2=inversor
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

        # 5. COMUNICAÇÃO COM KIVY / BD
        
        # Recebe comandos enviados pela interface
        com.receber("comando_kivy", self._processar_comando_kivy)
  
        # 6. LEITURA DE FLOAT (32 BITS)

    def _read_float(self, addr):
        """
        Lê dois registradores Modbus consecutivos
        e converte para float IEEE 754.
        """
        regs = self.client.read_holding_registers(addr, 2)
        if regs and len(regs) == 2:
            packed = struct.pack(">HH", regs[0], regs[1])
            return struct.unpack(">f", packed)[0]
        return None
 
        # 7. LEITURA DAS VARIÁVEIS DO PROCESSO

    def readData(self):
        """
        Realiza a leitura de todas as variáveis do processo
        e atualiza a estrutura interna de medições.
        """

        self._meas["timestamp"] = time.time()
        self._meas["values"] = {}

        for nome, cfg in self._tags.items():
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

        # Envia dados lidos para Kivy e Banco
        self._enviar_dados_para_kivy()
   
       # 8. ENVIO DE DADOS PARA KIVY / BD

    def _enviar_dados_para_kivy(self):
        """
        Envia as medições atuais para a interface gráfica
        e para o Banco de Dados.
        """
        mensagem = Mensagem(
            tipo="dados_monitoramento",
            dados=self._meas.copy(),
            origem="monitoramento"
        )
        com.enviar(mensagem)
    
        # 9. PROCESSAMENTO DE COMANDOS DO KIVY   

    def _processar_comando_kivy(self, comando):
        """
        Recebe e executa comandos enviados pela interface Kivy.
        """
        acao = comando.get("acao")

        if acao == "ligar_motor":
            self.ligar_motor(comando.get("ligar", True))

        elif acao == "set_velocidade":
            self.set_velocidade(comando.get("valor", 0))

        elif acao == "set_metodo_partida":
            self.set_metodo_partida(comando.get("valor", 0))

        elif acao == "acionar_valvula":
            self.acionar_valvula(
                comando.get("numero", 1),
                comando.get("aberta", True)
            )

        # 10. ATUAÇÃO E CONTROLE  

    def ligar_motor(self, ligar=True):
        """
        Liga ou desliga o motor do compressor.
        """
        self.client.write_single_coil(
            self._controls["liga_motor"]["addr"], ligar
        )

    def acionar_valvula(self, numero, aberta):
        """
        Aciona válvula do sistema pneumático.
        """
        if numero == 1:
            self.client.write_single_coil(
                self._controls["valvula_01"]["addr"], aberta
            )

    def set_velocidade(self, percentual):
        """
        Define a velocidade do motor (0 a 100 %).
        """
        percentual = int(min(max(percentual, 0), 100))
        self.client.write_single_register(
            self._controls["vel_motor"]["addr"], percentual
        )

    def set_metodo_partida(self, metodo):
        """
        Define o método de partida do motor.
        0 = direta | 1 = soft-starter | 2 = inversor
        """
        self.client.write_single_register(
            self._controls["metodo_partida"]["addr"], metodo
        )

        # 11. LOOP PRINCIPAL
     
    def executar_monitoramento(self, scan_time=1):
        """
        Executa o monitoramento contínuo do sistema.
        """
        self.executando = True

        while self.executando:
            self.readData()
            time.sleep(scan_time)

    def parar_monitoramento(self):
        """
        Interrompe o monitoramento do sistema.
        """
        self.executando = False
