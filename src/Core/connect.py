from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout

# Carrega o KV do popup
Builder.load_file("GUI/conexao.kv")


class ConnectContent(MDBoxLayout):
    """
    Conteúdo do popup de conexão.
    """

    def __init__(self, main_widget=None, **kwargs):
        super().__init__(**kwargs)
        self.main_widget = main_widget

    def connect_to_server(self, _btn):
        """
        Ação do botão CONECTAR.
        (stub – não faz nada por enquanto)
        """
        ip = self.ids.ip_input.text
        port = self.ids.port_input.text


class ConnectDialog:
    """
    Classe responsável por ABRIR o popup.
    """

    def __init__(self, main_widget=None):
        self.main_widget = main_widget
        self.dialog = None

    def open(self):
        if self.dialog:
            return

        content = ConnectContent(main_widget=self.main_widget)

        self.dialog = MDDialog(
            title="Conexão com o Servidor",
            type="custom",
            content_cls=content,
            size_hint=(0.6, None),
            height=dp(320),
            auto_dismiss=True,
        )

        self.dialog.open()
