from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.modalview import ModalView
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import NumericProperty
from kivy.clock import Clock
from comunicacao import com
import random


# =====================================================
# COMPONENTES VISUAIS
# =====================================================

class ClickableImage(ButtonBehavior, Image):
    pass


class CommandPopup(ModalView):
    pass


class MainWidget(MDFloatLayout):
    """
    Widget raiz da interface.
    """
    water_level = NumericProperty(0)
    pressao = NumericProperty(0.0)  # Propriedade para a pressão
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Inicializa variáveis para válvulas
        self._valvula_2 = False
        self._valvula_3 = False
        self._valvula_4 = False

    def on_kv_post(self, base_widget):
        # Inicia a simulação
        Clock.schedule_interval(self.simular, 1)

    def simular(self, dt):
        # Simula dados aleatórios
        self.pressao = random.uniform(0.5, 5.0)
        # Atualiza o texto do sensor
        if hasattr(self.ids, 'pit_01'):
            self.ids.pit_01.value_text = f"{self.pressao:.2f} bar"
        
        # Atualiza o ponteiro do gauge (se existir)
        if hasattr(self.ids, 'pressao_gauge'):
            # Calcula posição do ponteiro baseado na pressão
            min_val = 0.0
            max_val = 10.0
            normalized = (self.pressao - min_val) / (max_val - min_val)
            # Limita entre 0 e 1
            normalized = max(0.0, min(1.0, normalized))
            # Atualiza propriedade do gauge
            self.ids.pressao_gauge.value = normalized

    def abrir_menu_comando(self):
        MDApp.get_running_app().abrir_comando()

    def abrir_grafico(self):
        print("📈 Abrir gráfico")

    def abrir_medicoes(self):
        print("📊 Abrir medições")

    def abrir_temperaturas(self):
        print("🌡️ Abrir temperaturas")

    def abrir_banco_dados(self):
        print("🗄️ Abrir banco de dados")

    def abrir_pid(self):
        print("🎛️ Abrir PID")

    def conectar_clp(self):
        print("🔌 Conectando ao CLP...")
        # Nota: No seu .kv, não tem status_conexao, então removi essas linhas
        # self.ids.status_conexao.text = "ONLINE"
        # self.ids.status_conexao.theme_text_color = "Custom"
        # self.ids.status_conexao.text_color = (0.12, 0.62, 0.22, 1)
        self.ids.connection_image.source = "images/server_connected.png"

    def desconectar_clp(self):
        print("❌ Desconectando do CLP...")
        # Nota: No seu .kv, não tem status_conexao, então removi essas linhas
        # self.ids.status_conexao.text = "DESCONECTADO"
        # self.ids.status_conexao.theme_text_color = "Error"
        self.ids.connection_image.source = "images/server_disconnected.png"


# =====================================================
# APLICAÇÃO PRINCIPAL
# =====================================================

class SupervisoryApp(MDApp):

    motor_ligado = False

    def build(self):
        print("✅ UI iniciada")
        
        # ORDEM IMPORTA - carrega primeiro o sensor_state.kv
        try:
            Builder.load_file("GUI/sensor_state.kv")
            Builder.load_file("GUI/ui.kv")
            print("✅ Arquivos .kv carregados com sucesso")
        except Exception as e:
            print(f"❌ Erro ao carregar arquivos .kv: {e}")
            # Cria um widget básico em caso de erro
            return MainWidget()
        
        return MainWidget()

    def abrir_comando(self):
        print("🪟 Abrindo popup de comando")
        popup = CommandPopup()
        popup.open()

    # ================= MOTOR =================

    def toggle_motor(self):
        motor_img = self.root.ids.motor_1

        if not self.motor_ligado:
            print("🔁 LIGAR MOTOR")
            self._enviar_motor(1)
            motor_img.source = "images/motor_on.png"
            self.motor_ligado = True
        else:
            print("🔁 DESLIGAR MOTOR")
            self._enviar_motor(0)
            motor_img.source = "images/motor_off.png"
            self.motor_ligado = False

    def resetar_motor(self):
        print("🔄 RESET MOTOR")
        self._enviar_motor(2)

    def _enviar_motor(self, valor):
        # Verifica se o módulo de comunicação existe
        try:
            com.enviar_comando({
                "acao": "motor",
                "valor": valor
            })
        except Exception as e:
            print(f"⚠️ Erro ao enviar comando do motor: {e}")

    # ================= PARTIDA =================

    def set_tipo_partida(self, tipo):
        mapa = {"Soft-Start": 1, "Inversor": 2, "Direta": 3}
        valor = mapa.get(tipo)

        if valor:
            try:
                com.enviar_comando({
                    "acao": "set_driver",
                    "valor": valor
                })
            except Exception as e:
                print(f"⚠️ Erro ao definir tipo de partida: {e}")

    def atualizar_velocidade(self, valor):
        # Método chamado pelo slider no popup
        print(f"🎚️ Velocidade atualizada: {valor} RPM")
        # Atualiza o label no menu lateral em tempo real
        self.root.ids.lbl_vel.text = f"{int(valor)} RPM"

    # ================= VELOCIDADE =================

    def enviar_setpoint(self, rpm):
        rpm = int(rpm)
        try:
            com.enviar_comando({
                "acao": "velocidade",
                "valor": rpm
            })
            print(f"✅ Setpoint enviado: {rpm} RPM")
            self.root.ids.lbl_vel.text = f"{rpm} RPM"
        except Exception as e:
            print(f"⚠️ Erro ao enviar setpoint: {e}")

    # ================= VÁLVULAS =================

    def toggle_valvula(self, nome):
        try:
            numero = int(nome.split("_")[1])
            # Obtém o estado atual da válvula
            estado_atual = getattr(self, f"_valvula_{numero}", False)
            novo_estado = not estado_atual
            
            # Atualiza o estado
            setattr(self, f"_valvula_{numero}", novo_estado)
            
            # Envia comando
            com.enviar_comando({
                "acao": "valvula",
                "numero": numero,
                "aberta": novo_estado
            })
            
            # Atualiza a imagem
            img = self.root.ids[nome]
            if novo_estado:
                img.source = "images/valve_on.png"
                print(f"✅ Válvula {numero} ABERTA")
            else:
                img.source = "images/valve_off.png"
                print(f"✅ Válvula {numero} FECHADA")
                
        except Exception as e:
            print(f"⚠️ Erro ao alternar válvula: {e}")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    SupervisoryApp().run()