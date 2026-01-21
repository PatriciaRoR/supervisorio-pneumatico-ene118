from threading import Thread

from kivymd.app import MDApp
from kivy.lang import Builder
from Core.widgets import MainWidget
from Core.monitoramento import Monitoramento


class SupervisoryApp(MDApp):
    def build(self):
        print("UI iniciada")

        #  Carrega TODOS os KV (sem criar root aqui)
        Builder.load_file("GUI/conexao.kv")
        Builder.load_file("GUI/comando.kv")
        Builder.load_file("GUI/RealTimeGraph.kv")
        Builder.load_file("GUI/medicoes.kv")
        Builder.load_file("GUI/main.kv")   #  IMPORTANTE: carregar o KV do MainWidget

        #  Backend criado UMA ÚNICA VEZ
        self.monitoramento = Monitoramento()

        Thread(
            target=self.monitoramento.executar_monitoramento,
            daemon=True
        ).start()

        #  Root criado PELO PYTHON (não pelo KV)
        root = MainWidget(self.monitoramento)

        return root


if __name__ == "__main__":
    SupervisoryApp().run()
