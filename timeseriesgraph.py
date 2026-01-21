from kivy_garden.graph import Graph
from kivy.clock import Clock


class TimeSeriesGraph(Graph):
    """
    Classe derivada que implementa gráficos temporais
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._trigger_time_label = Clock.create_trigger(self._addTimeLabels)
        self._timestamps = []
        self._max_points = kwargs.get('max_points', 20)
        self._numMeds = -1

    def update_x_labels(self, timestamps=None):
        if timestamps is not None:
            self._timestamps = timestamps
            if len(timestamps) >= 100:
                self.x_ticks_major = int(len(timestamps) / 10)
            else:
                self.x_ticks_major = 5
        self._trigger_time_label()

    def clearLabel(self, *args):
        for lb in self._x_grid_label:
            lb.text = ''

    def clearPlots(self):
        try:
            while len(self.plots) != 0:
                self.remove_plot(self.plots[0])
        except Exception as e:
            print(e.args)

    def _addTimeLabels(self, *args):
        try:
            labels = self._timestamps[0:len(self._timestamps):self.x_ticks_major]
            for i in range(min(len(self._x_grid_label), len(labels))):
                self._x_grid_label[i].text = labels[i].strftime("%H:%M:%S")
        except Exception as e:
            print('Error:', e.args)

    def setMaxPoints(self, mp, plot_number):
        try:
            self._max_points = mp
            self.x_ticks_major = 10 if mp == 100 else 5

            if len(self.plots[plot_number].points) < self._max_points:
                self.xmax = min(self.plots[plot_number].points)[0] + self._max_points - 1

            self.plots[plot_number].points = self.plots[plot_number].points[-self._max_points:]
            self._timestamps = self._timestamps[-self._max_points:]

        except Exception as e:
            print(e.args)

    def updateGraph(self, meas, plot_number):
        try:
            if len(self._timestamps) == 0 or meas[0] != self._timestamps[-1]:
                self._timestamps.append(meas[0])
                self._timestamps = self._timestamps[-self._max_points:]
                self._numMeds += 1

                self.plots[plot_number].points.append(
                    (self._numMeds, meas[1])
                )
                self.plots[plot_number].points = self.plots[plot_number].points[-self._max_points:]

                self.xmin = min(self.plots[plot_number].points)[0]

                if len(self.plots[plot_number].points) >= self._max_points:
                    self.xmax = max(self.plots[plot_number].points)[0]
                else:
                    Clock.schedule_once(self.clearLabel)

                self.update_x_labels()
            else:
                self.plots[plot_number].points.append(
                    (self._numMeds, meas[1])
                )
                self.plots[plot_number].points = self.plots[plot_number].points[-self._max_points:]

        except Exception as e:
            print(e.args)
