from collections import deque
from datetime import datetime

from kivy.uix.modalview import ModalView
from kivy.clock import Clock
from kivymd.uix.boxlayout import MDBoxLayout
from kivy_garden.graph import LinePlot


class RealTimeGraphContent(MDBoxLayout):
    pass


class RealTimeGraphPopup(ModalView):
    
    def __init__(self, main_widget, name, var, unit, max_value=1, **kwargs):
        super().__init__(
            size_hint=(None, None),
            size=(940, 680),
            auto_dismiss=False,
            **kwargs   #Evita fechamento acidental
        )

        # parâmetros
        self.main_widget = main_widget
        self.var_attr = var
        self.unit = unit
        self.name = name
        self.max_value = max_value

        #  tempo e dados
        self.start_time = datetime.now()
        self.max_points = 20
        self.plot_points = deque(maxlen=self.max_points)

        # conteúdo visual (KV)
        self.content = RealTimeGraphContent()
        self.add_widget(self.content)

        # inicialização tardia (IMPORTANTE)
        self.graph = None
        self.plot = None

        self._clock_event = None

    # =====================================================
    # LIFECYCLE — só monta o gráfico quando o popup ABRE
    # =====================================================
    def on_open(self):
        # garante que o KV já está 100% carregado
        self.graph = self.content.ids.graph_widget

        self.graph.ylabel = f"{self.name} ({self.unit})"
        self.graph.xlabel = "Tempo (s)"
        self.graph.ymin = 0
        self.graph.ymax = max(self.max_value, 1)
        self.graph.y_ticks_major = self.graph.ymax / 5

        self.plot = LinePlot(color=[0.2, 0.6, 1, 1], line_width=2)
        self.graph.add_plot(self.plot)

        # evita múltiplos schedules
        if self._clock_event:
            Clock.unschedule(self._clock_event)

        self._clock_event = Clock.schedule_interval(
            self.update_plot,
            self.main_widget.scan_time
        )

    # =====================================================
    # ATUALIZAÇÃO DO GRÁFICO
    # =====================================================
    def update_plot(self, dt):
        value = getattr(self.main_widget, self.var_attr, 0)
        print(f"[DEBUG] {self.var_attr} = {value}")

        elapsed = (datetime.now() - self.start_time).total_seconds()

        self.plot_points.append((elapsed, value))
        self.plot.points = list(self.plot_points)

        # nunca corta valor real
        if value >= self.graph.ymax:
            self.graph.ymax = value * 1.2
            self.graph.y_ticks_major = max(self.graph.ymax / 5, 1)

        # eixo X acompanha o tempo
        if elapsed >= self.graph.xmax:
            self.graph.xmax = elapsed + self.main_widget.scan_time * 5
            self.graph.x_ticks_major = self.graph.xmax / 5

    # =====================================================
    # CONTROLES
    # =====================================================
    def set_points(self, amount):
        self.max_points = amount
        self.plot_points = deque(self.plot_points, maxlen=amount)

        self.graph.xmax = amount * self.main_widget.scan_time
        self.graph.x_ticks_major = self.graph.xmax / 5

    def on_dismiss(self):
        if self._clock_event:
            Clock.unschedule(self._clock_event)
            self._clock_event = None
