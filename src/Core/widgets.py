"""
Widget principal da interface
VERSÃO FINAL – integrada com Monitoramento e MedicoesPopup
"""

from kivy.clock import Clock
from kivy.properties import NumericProperty, BooleanProperty, StringProperty
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.modalview import ModalView
from kivymd.uix.floatlayout import MDFloatLayout
from Core.medicoes import MedicoesPopup
from Core.RealTimeGraph import RealTimeGraphPopup
from Core.connect import ConnectDialog


# =====================================================
# COMPONENTES AUXILIARES
# =====================================================

class ClickableImage(ButtonBehavior, Image):
    pass


class CommandPopup(ModalView):
    def __init__(self, main_widget=None, **kwargs):
        super().__init__(**kwargs)
        self.main_widget = main_widget


# =====================================================
# WIDGET PRINCIPAL
# =====================================================

class MainWidget(MDFloatLayout):

    # =========================
    # VARIÁVEIS PRINCIPAIS
    # =========================
    rotation   = NumericProperty(0.0)   # co.encoder
    torque     = NumericProperty(0.0)   # co.torque
    pressao    = NumericProperty(0.0)   # co.pressao
    flow_rate  = NumericProperty(0.0)   # co.fit03

    is_connected = BooleanProperty(False)
    motor_ligado = BooleanProperty(False)

    # =========================
    # TEMPERATURAS
    # =========================
    co_temp_carc = NumericProperty(0.0)
    co_temp_r    = NumericProperty(0.0)

    # =========================
    # CORRENTES
    # =========================
    co_corrente_r = NumericProperty(0.0)
    co_corrente_s = NumericProperty(0.0)
    co_corrente_t = NumericProperty(0.0)
    co_corrente_n = NumericProperty(0.0)
    co_corrente_media = NumericProperty(0.0)

    # =========================
    # TENSÕES
    # =========================
    co_tensao_rs = NumericProperty(0.0)
    co_tensao_st = NumericProperty(0.0)
    co_tensao_tr = NumericProperty(0.0)

    # =========================
    # FATOR DE POTÊNCIA
    # =========================
    co_fp_r = NumericProperty(0.0)
    co_fp_s = NumericProperty(0.0)
    co_fp_t = NumericProperty(0.0)
    co_fp_media = NumericProperty(0.0)

    # =========================
    # THD
    # =========================
    co_thd_tensao_rs = NumericProperty(0.0)
    co_thd_tensao_st = NumericProperty(0.0)
    co_thd_tensao_tr = NumericProperty(0.0)
    co_thd_corrente_r = NumericProperty(0.0)
    co_thd_corrente_s = NumericProperty(0.0)
    co_thd_corrente_t = NumericProperty(0.0)
    co_thd_corrente_n = NumericProperty(0.0)

    # =========================
    # CONTROLE
    # =========================
    scan_time = NumericProperty(1.0)
    tipo_partida = StringProperty("Direta")
    velocidade_setpoint = NumericProperty(1800)

    # =====================================================
    # CICLO DE VIDA
    # =====================================================

    def __init__(self, monitoramento, **kwargs):
        super().__init__(**kwargs)

        self.monitoramento = monitoramento
        self.medicoes_popup = None
        self._popup_grafico = None

        # Atualização periódica da UI (lê do monitoramento)
        Clock.schedule_interval(self.atualizar_dados, 0.5)

    # =====================================================
    # ATUALIZAÇÃO DE DADOS (CLP → UI → MEDIÇÕES)
    # =====================================================

    def atualizar_dados(self, dt):
        """Copia os dados reais do monitoramento para o widget"""
        meas = self.monitoramento._meas.get("values", {})

        #muda as imagens
        if meas.get("co.xv2") == 1:
            self.ids.valvula_2.source = "images/valve_on.png"
        else:
            self.ids.valvula_2.source = "images/valve_off.png"
        #
        if meas.get("co.xv3") == 1:
            self.ids.valvula_3.source = "images/valve_on.png"
        else:
            self.ids.valvula_3.source = "images/valve_off.png"
        #
        if meas.get("co.xv4") == 1:
            self.ids.valvula_4.source = "images/valve_on.png"
        else:
            self.ids.valvula_4.source = "images/valve_off.png"
        #
        if meas.get("co.xv5") == 1:
            self.ids.valvula_5.source = "images/valve_on.png"
        else:
            self.ids.valvula_5.source = "images/valve_off.png"
         #
        if meas.get("co.xv6") == 1:
            self.ids.valvula_6.source = "images/valve_on.png"
        else:
            self.ids.valvula_6.source = "images/valve_off.png"
        #
        if meas.get("co.habilita") == 1:
            self.ids. motor_1.source = "images/motor_on.png"
        else:
            self.ids. motor_1.source = "images/motor_off.png"
        

        # Principais
        self.rotation  = meas.get("co.encoder", 0)
        self.torque    = meas.get("co.torque", 0)
        self.pressao   = meas.get("co.pressao", 0)
        self.flow_rate = meas.get("co.fit03", 0)

        # Temperaturas
        self.co_temp_carc = meas.get("co.temp_carc", 0)
        self.co_temp_r    = meas.get("co.temp_r", 0)

        # Correntes
        self.co_corrente_r = meas.get("co.corrente_r", 0)
        self.co_corrente_s = meas.get("co.corrente_s", 0)
        self.co_corrente_t = meas.get("co.corrente_t", 0)
        self.co_corrente_n = meas.get("co.corrente_n", 0)
        self.co_corrente_media = meas.get("co.corrente_media", 0)

        # Tensões
        self.co_tensao_rs = meas.get("co.tensao_rs", 0)
        self.co_tensao_st = meas.get("co.tensao_st", 0)
        self.co_tensao_tr = meas.get("co.tensao_tr", 0)

        # Fator de potência
        self.co_fp_r = meas.get("co.fp_r", 0)
        self.co_fp_s = meas.get("co.fp_s", 0)
        self.co_fp_t = meas.get("co.fp_t", 0)
        self.co_fp_total = meas.get("co.fp_total", 0)

        # THD
        self.co_thd_tensao_rs = meas.get("co.thd_tensao_rs", 0)
        self.co_thd_tensao_st = meas.get("co.thd_tensao_st", 0)
        self.co_thd_tensao_tr = meas.get("co.thd_tensao_tr", 0)
        self.co_thd_corrente_r = meas.get("co.thd_corrente_r", 0)
        self.co_thd_corrente_s = meas.get("co.thd_corrente_s", 0)
        self.co_thd_corrente_t = meas.get("co.thd_corrente_t", 0)
        self.co_thd_corrente_n = meas.get("co.thd_corrente_n", 0)


    # =====================================================
    # ATUAÇÃO
    # =====================================================

    def toggle_motor(self):
        self.monitoramento.ligar_motor()

    def set_tipo_partida(self, tipo):
        mapa = {"Soft-Start": 1, "Inversor": 2, "Direta": 3}
        if tipo in mapa:
            self.tipo_partida = tipo
            self.monitoramento.set_metodo_partida(mapa[tipo])
            print(f" Tipo de partida selecionado: {tipo} ({mapa[tipo]})")

    def enviar_setpoint(self, valor):
        self.velocidade_setpoint = int(valor)
        self.monitoramento.set_velocidade(valor)

    def toggle_valvula(self, numero):
        self.monitoramento.abre_valvula(numero)

    # =====================================================
    # POPUPS
    # =====================================================


    def abrir_medicoes(self):
        if self.medicoes_popup:
            self.medicoes_popup.dismiss()
        self.medicoes_popup = MedicoesPopup(main_widget=self)
        self.medicoes_popup.open()

    def abrir_grafico(self, nome, var, unidade, maximo):
        from Core.RealTimeGraph import RealTimeGraphPopup

        popup = RealTimeGraphPopup(
            main_widget=self,
            name=nome,
            var=var,
            unit=unidade,
            max_value=maximo
        )
        popup.open()

    def abrir_menu_comando(self):
        """Abre o popup de comandos do motor"""
        try:
            popup = CommandPopup(main_widget=self)
            popup.open()
        except Exception as e:
            print(f"Erro ao abrir menu de comando: {e}")
    
    def abrir_popup_conexao(self):
        from Core.connect import ConnectDialog
        ConnectDialog(main_widget=self).open()

    # =====================================================
    # Velocidade
    # =====================================================

    def atualizar_velocidade(self, valor):
        """
        Atualiza o setpoint de velocidade (visual)
        Chamado pelo Slider no popup de comando.
        """
        self.velocidade_setpoint = int(valor)

        print(f"Velocidade ajustada: {int(valor)} RPM")

        # Atualiza label do popup, se existir
        try:
            popup = self.ids.sp_partida.parent.parent.parent
            if hasattr(popup, 'ids') and 'lbl_rpm' in popup.ids:
                popup.ids.lbl_rpm.text = f"{int(valor)} RPM"
        except Exception:
            pass

    def desconectar_clp(self):
        """
        Stub seguro para botão de desconexão.
        Não faz nada por enquanto.
        """
        print("[UI] Desconectar CLP (não implementado ainda)")
