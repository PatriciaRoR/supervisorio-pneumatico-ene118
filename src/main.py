from __future__ import annotations

import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen

from comunicacao import com
from monitoramento import Monitoramento
from tags import TAGS_PROCESSO, TAGS_ELETRICAS
from widgets import LinearIndicator, ValveStatus


# ================= TELAS =================

class RealTimeScreen(Screen):
    pass


class MeasurementsScreen(Screen):
    pass


class CommandsScreen(Screen):
    pass


class ElectricalScreen(Screen):
    pass


class TrendsScreen(Screen):
    pass


class HistoryScreen(Screen):
    pass


# ================= APP =================

class SupervisoryApp(App):
    is_online = BooleanProperty(False)

    def build(self):
        Builder.load_file("ui.kv")

        sm = ScreenManager()
        sm.add_widget(RealTimeScreen(name="realtime"))
        sm.add_widget(MeasurementsScreen(name="medicoes"))
        sm.add_widget(CommandsScreen(name="comandos"))
        sm.add_widget(ElectricalScreen(name="eletricas"))
        sm.add_widget(TrendsScreen(name="trends"))
        sm.add_widget(HistoryScreen(name="history"))

        self.ind_proc = {}
        self.ind_el = {}
        self.valves = {}

        Clock.schedule_once(self._populate_widgets, 0)
        Clock.schedule_interval(self._update_from_backend, 0.5)

        return sm

    # ---------- INICIA BACKEND NO MESMO PROCESSO ----------
    def on_start(self):
        self.monitor = Monitoramento()

        t = threading.Thread(
            target=self.monitor.executar_monitoramento,
            kwargs={"scan_time": 2},
            daemon=True
        )
        t.start()

    # ---------- NAVEGAÇÃO ----------
    def go_to(self, screen_name: str):
        if self.root:
            self.root.current = screen_name

    # ---------- POPULA WIDGETS ----------
    def _populate_widgets(self, *_):
        md = self.root.get_screen("medicoes")
        el = self.root.get_screen("eletricas")
        cm = self.root.get_screen("comandos")

        for info in TAGS_PROCESSO:
            w = LinearIndicator(
                title=info.label,
                unit=info.unit,
                vmin=info.vmin,
                vmax=info.vmax
            )
            self.ind_proc[info.tag] = w
            md.ids.grid_proc.add_widget(w)

        for info in TAGS_ELETRICAS:
            w = LinearIndicator(
                title=info.label,
                unit=info.unit,
                vmin=info.vmin,
                vmax=info.vmax
            )
            self.ind_el[info.tag] = w
            el.ids.box_el.add_widget(w)

        for n in range(1, 5):
            tag = f"co.xv{n}"
            v = ValveStatus(tag=tag, name=f"XV-{n}")
            self.valves[tag] = v
            cm.ids.box_valves.add_widget(v)

    # ---------- RECEBE DADOS DO BACKEND ----------
    def _update_from_backend(self, *_):
        msg = com.obter_dados()
        if not msg:
            return

        tipo = msg.get("tipo")

        if tipo == "status":
            self.is_online = msg["dados"]["online"]
            return

        if tipo == "dados_monitoramento":
            values = msg["dados"]["values"]

            for tag, val in values.items():
                if tag in self.ind_proc:
                    self.ind_proc[tag].set_value(val)
                elif tag in self.ind_el:
                    self.ind_el[tag].set_value(val)
                elif tag in self.valves:
                    self.valves[tag].set_open(bool(val))

    # ---------- COMANDOS ----------
    def actuate_motor(self, on: bool):
        com.enviar_comando({
            "acao": "motor",
            "valor": 1 if on else 0
        })

    def actuate_valve(self, tag: str, open_: bool):
        numero = int(tag.replace("co.xv", ""))
        com.enviar_comando({
            "acao": "valvula",
            "numero": numero,
            "aberta": open_
        })

    def set_start_method(self, metodo: str):
        mapa = {
            "Soft-Starter": 1,
            "Inversor (VFD)": 2,
            "Direta": 3
        }

        if metodo in mapa:
            com.enviar_comando({
                "acao": "set_driver",
                "valor": mapa[metodo]
            })

    def set_speed_setpoint(self, rpm):
        if str(rpm).isdigit():
            com.enviar_comando({
                "acao": "velocidade",
                "valor": int(rpm)
            })


# ================= MAIN =================

if __name__ == "__main__":
    SupervisoryApp().run()
