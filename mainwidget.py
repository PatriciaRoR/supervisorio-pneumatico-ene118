from kivy.uix.boxlayout import BoxLayout
from bdhandler import BDHandler
from popups import HistTablePopup

#Parte importante: dicionário de variáveis
VARIABLES = {
    "Temperatura Enrolamento R": ("temp_enrolamento_r", "°C"),
    "Temperatura Carcaça": ("temp_carcaca", "°C"),
    "Velocidade do Ar": ("velocidade_ar", "m/s"),
    "Pressão Tubo Azul": ("pressao_tubo_azul", "bar"),
    "Torque": ("torque", "Nm"),
    "Pressão": ("pressao", "bar"),
    "Vazão": ("vazao", "m³/h"),
    "Pressão Reservatório": ("pressao_reservatorio", "bar"),
    "Vazão Válvula 01": ("vazao_valvula_01", "m³/h"),
    "Torque Medido": ("torque_medido", "Nm"),
}

#Apenas um exemplo de widget principal que abre o popup
class MainWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bd = BDHandler()
        self.bd.start_insertion_thread(interval=1.0)

    def abrir_historico(self):
        popup = HistTablePopup(
            bd=self.bd,
            variables=VARIABLES
        )
        popup.open()