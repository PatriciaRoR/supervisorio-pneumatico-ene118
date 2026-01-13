from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import ListProperty
from datetime import datetime


class HistTablePopup(Popup):

    # 👇 ISSO É ESSENCIAL
    var_names = ListProperty([])

    def __init__(self, bd, variables, **kwargs):
        super().__init__(**kwargs)

        self.bd = bd
        self.variables = variables

        # agora o KV consegue acessar
        self.var_names = list(variables.keys())

    def buscar(self):
        table = self.ids.table
        table.clear_widgets()

        var_name = self.ids.spinner_var.text
        if var_name not in self.variables:
            return

        field, unit = self.variables[var_name]

        try:
            t_ini = datetime.strptime(
                self.ids.txt_ini.text, "%d/%m/%Y %H:%M:%S"
            )
            t_fim = datetime.strptime(
                self.ids.txt_fim.text, "%d/%m/%Y %H:%M:%S"
            )
        except ValueError:
            print("Formato de data/hora inválido")
            return

        data = self.bd.get_history(field, t_ini, t_fim)

        for ts, value in data:
            table.add_widget(Label(text=var_name))
            table.add_widget(Label(text=f"{value:.2f} {unit}"))
            table.add_widget(Label(text=ts.strftime("%H:%M:%S")))
            table.add_widget(Label(text=ts.strftime("%d/%m/%Y")))
