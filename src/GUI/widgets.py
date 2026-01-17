# widgets.py
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout


class Connection(Widget):
    """Usado apenas como 'tubo' visual"""
    pass


class Reservoir(Image):
    """Reservatório (imagem)"""
    pass


class MotorWidget(FloatLayout):
    """
    Motor clicável ON/OFF
    """
    ligado = BooleanProperty(False)

    def ligar(self):
        self.ligado = True
        self.ids.motor_img.source = "images/motor_on.png"

    def desligar(self):
        self.ligado = False
        self.ids.motor_img.source = "images/motor_off.png"


class ValveWidget(FloatLayout):
    """
    Válvula simples ON/OFF
    """
    aberta = BooleanProperty(False)
    nome = StringProperty("XV")

    def abrir(self):
        self.aberta = True
        self.ids.valve_img.source = "images/valve_on.png"

    def fechar(self):
        self.aberta = False
        self.ids.valve_img.source = "images/valve_off.png"
