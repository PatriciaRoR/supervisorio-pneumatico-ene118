from __future__ import annotations

from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout


class LinearIndicator(BoxLayout):
    title = StringProperty("")
    unit = StringProperty("")
    vmin = NumericProperty(0.0)
    vmax = NumericProperty(1.0)
    value = NumericProperty(0.0)

    def set_value(self, v: float) -> None:
        self.value = float(v)
        if self.vmax <= self.vmin:
            pct = 0.0
        else:
            vv = max(self.vmin, min(self.vmax, self.value))
            pct = 100.0 * (vv - self.vmin) / (self.vmax - self.vmin)
        self.ids.pb.value = pct


class ValveStatus(BoxLayout):
    tag = StringProperty("")
    name = StringProperty("")
    is_open = BooleanProperty(False)

    def set_open(self, opened: bool) -> None:
        self.is_open = bool(opened)
