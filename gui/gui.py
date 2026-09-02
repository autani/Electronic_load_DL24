import matplotlib
import matplotlib.ticker as ticker

matplotlib.use('Qt5Agg')

from PyQt5 import QtWidgets, uic

from PyQt5.QtCore import (
    QSettings,
    Qt,
    QSize,
    QPoint,
    QTimer,
)

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QScrollBar,
    QLabel,
    QComboBox,
    QCheckBox,
    QWidget,
    QSizePolicy,
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar

from matplotlib.figure import Figure
from datetime import time, datetime

from instruments.instrument import Instrument
from instruments import resource_label
from gui.swcccv import SwCCCV
from gui.internal_r import InternalR
from gui.log_control import LogControl
from sys import argv


TIME_SCALES = [
    ('30 s', 30),
    ('1 min', 60),
    ('2 min', 2 * 60),
    ('5 min', 5 * 60),
    ('15 min', 15 * 60),
    ('30 min', 30 * 60),
    ('1 h', 60 * 60),
    ('2 h', 2 * 60 * 60),
    ('4 h', 4 * 60 * 60),
    ('All', None),
]

LOAD_ON_ACTIVE = """
QPushButton {
    background-color: #d32f2f;
    color: white;
    font-weight: bold;
    border: 2px solid #9a0007;
    border-radius: 4px;
    padding: 4px 10px;
}
QPushButton:disabled { background-color: #ef9a9a; color: #fff8f8; border: 1px solid #e57373; }
"""
LOAD_ON_IDLE = """
QPushButton {
    background-color: #ffcdd2;
    color: #9a0007;
    border: 1px solid #e57373;
    border-radius: 4px;
    padding: 4px 10px;
}
QPushButton:disabled { background-color: #ffebee; color: #ef9a9a; border: 1px solid #ffcdd2; }
"""
LOAD_OFF_ACTIVE = """
QPushButton {
    background-color: #1976d2;
    color: white;
    font-weight: bold;
    border: 2px solid #0d47a1;
    border-radius: 4px;
    padding: 4px 10px;
}
QPushButton:disabled { background-color: #90caf9; color: #fff8f8; border: 1px solid #64b5f6; }
"""
LOAD_OFF_IDLE = """
QPushButton {
    background-color: #bbdefb;
    color: #0d47a1;
    border: 1px solid #64b5f6;
    border-radius: 4px;
    padding: 4px 10px;
}
QPushButton:disabled { background-color: #e3f2fd; color: #90caf9; border: 1px solid #bbdefb; }
"""


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        uic.loadUi('gui/main.ui', self)
        self.load_settings()

        self.plot_placeholder.setLayout(self.plot_layout())
        self.map_controls()
        self.tab2 = uic.loadUi("gui/settings.ui")
        self.logControl = LogControl()
        self.swCCCV = SwCCCV()
        self.internal_r = InternalR()
        self.controlsLayout.insertWidget(4, self.internal_r)
        self.tab2.layout().addWidget(self.logControl, 0, 0)
        self.tab2.layout().addWidget(self.swCCCV, 1, 0)
        self.tabs.addTab(self.tab2, "Settings")
        self.show()

    def plot_layout(self):
        self.canvas = MplCanvas(self, width=8, height=4, dpi=100)

        self.ax = self.canvas.axes
        self.ax.tick_params(axis='y', colors='blue')

        self.twinaxCurrent = self.ax.twinx()
        self.twinaxCurrent.tick_params(axis='y', colors='red')

        self.twinaxPower = self.ax.twinx()
        self.twinaxPower.tick_params(axis='y', colors='green')
        
        self.twinaxTemp = self.ax.twinx()
        self.twinaxTemp.tick_params(axis='y', colors='grey')
        self.twinaxTemp.yaxis.tick_left()

        toolbar = NavigationToolbar(self.canvas, self)
        toolbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.timeScaleCombo = QComboBox()
        self.timeScaleCombo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.followLatest = QCheckBox("Follow latest")
        self.followLatest.setChecked(True)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        top.addWidget(toolbar, 1)
        top.addWidget(QLabel("Range"))
        top.addWidget(self.timeScaleCombo)
        top.addWidget(self.followLatest)
        top_bar = QWidget()
        top_bar.setLayout(top)
        top_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.timeScrollBar = QScrollBar(Qt.Horizontal)
        self.timeScrollBar.setEnabled(False)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(top_bar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.timeScrollBar)
        return layout

    def map_controls(self):
        self.device_connected = False
        self.openButton.clicked.connect(self.open_clicked)
        self.refreshPortsButton.clicked.connect(self.refresh_ports_clicked)
        self.loadOnButton.clicked.connect(self.load_on_clicked)
        self.loadOffButton.clicked.connect(self.load_off_clicked)
        self.set_load_ui(False)
        self.set_voltage.valueChanged.connect(self.voltage_changed)
        self.set_current.valueChanged.connect(self.current_changed)
        self.set_timer.timeChanged.connect(self.timer_changed)
        self.resetButton.clicked.connect(self.reset_dev)

        self.set_voltage_timer = QTimer(singleShot=True,
                                        timeout=self.voltage_set)
        self.set_current_timer = QTimer(singleShot=True,
                                        timeout=self.current_set)
        self.set_timer_timer = QTimer(singleShot=True, timeout=self.timer_set)
        self.set_device_controls_enabled(False)
        self._plot_data = None
        self._updating_scroll = False
        for label, seconds in TIME_SCALES:
            self.timeScaleCombo.addItem(label,
                                        -1 if seconds is None else seconds)
        self.timeScaleCombo.setCurrentIndex(self.timeScaleCombo.count() - 1)
        self.timeScaleCombo.currentIndexChanged.connect(self.on_time_scale_changed)
        self.followLatest.toggled.connect(self.on_follow_latest_changed)
        self.timeScrollBar.valueChanged.connect(self.on_time_scroll)
        self.checkbox_p.stateChanged.connect(self.refresh_plot)
        self.checkbox_t.stateChanged.connect(self.refresh_plot)
        self._sync_time_axis_controls()

    def data_row(self, data, row):
        if data:
            set_voltage = data.lastval('set_voltage')
            if not self.set_voltage.hasFocus():
                self.set_voltage.setValue(set_voltage)

            set_current = data.lastval('set_current')
            if not self.set_current.hasFocus():
                self.set_current.setValue(set_current)

            is_on = data.lastval('is_on')
            self.set_load_ui(bool(is_on))

            voltage = data.lastval('voltage')
            current = data.lastval('current')
            power = round(voltage * current, 3)
            data.setlastval('power', power)
            self.setWindowTitle("Battery tester {:4.2f}V {:4.2f}A ".format(
                voltage, current))
            self.readVoltage.setText("<pre>{:5.3f} V</pre>".format(voltage))
            self.readCurrent.setText("<pre>{:5.3f} A</pre>".format(current))
            self.readCapAH.setText("<pre>{:5.3f} Ah</pre>".format(data.lastval('cap_ah')))
            self.readCapWH.setText("<pre>{:5.3f} Wh</pre>".format(data.lastval('cap_wh')))
            self.readTemp.setText("<pre>" + str(int(data.lastval('temp'))) + "°C / " + str(int(data.lastval('temp') * 1.8 + 32)) + "°F</pre>")
            self.Wattage.setText("<pre>{:5.3f} W</pre>".format(power))
            self.readTime.setText("<pre>" + data.lastval('time').strftime("%H:%M:%S") + "</pre>")

            self._plot_data = data
            self.render_plot()

    def status_update(self, status):
        self.statusBar().showMessage(status)

    def time_window_seconds(self):
        value = self.timeScaleCombo.currentData()
        if value is None or int(value) < 0:
            return None
        return int(value)

    def _sync_time_axis_controls(self):
        window = self.time_window_seconds()
        windowed = window is not None
        self.followLatest.setEnabled(windowed)
        if not windowed:
            self.timeScrollBar.setEnabled(False)
            self.timeScrollBar.setValue(0)

    def on_time_scale_changed(self):
        self._sync_time_axis_controls()
        self.refresh_plot()

    def on_follow_latest_changed(self, _checked):
        self.refresh_plot()

    def on_time_scroll(self, _value):
        if self._updating_scroll:
            return
        if self.followLatest.isChecked():
            self.followLatest.blockSignals(True)
            self.followLatest.setChecked(False)
            self.followLatest.blockSignals(False)
        self.refresh_plot()

    def refresh_plot(self):
        if self._plot_data:
            self.render_plot()

    def _elapsed_limits(self, data):
        elapsed = data.data['t_elapsed']
        t_min = float(elapsed.min())
        t_max = float(elapsed.max())
        window = self.time_window_seconds()
        if window is None:
            span = max(t_max - t_min, 1.0)
            return t_min, t_min + span, False

        follow = self.followLatest.isChecked()
        t_start = 0.0
        t_end = max(t_max, window)
        max_start = max(0.0, t_end - window)
        if follow:
            start = max_start
        else:
            start = min(float(self.timeScrollBar.value()), max_start)
        return start, start + window, True

    def _update_time_scrollbar(self, start, window, t_end):
        max_start = max(0, int(round(max(0.0, t_end - window))))
        self._updating_scroll = True
        self.timeScrollBar.setEnabled(max_start > 0)
        self.timeScrollBar.setRange(0, max_start)
        self.timeScrollBar.setPageStep(max(1, int(window)))
        self.timeScrollBar.setSingleStep(max(1, int(window) // 20))
        self.timeScrollBar.setValue(int(round(start)))
        self._updating_scroll = False

    def render_plot(self):
        data = self._plot_data
        if data is None or data.data.empty or 't_elapsed' not in data.data:
            return

        set_voltage = data.lastval('set_voltage')
        start, end, windowed = self._elapsed_limits(data)
        xlim = (start, end)
        if windowed:
            t_max = float(data.data['t_elapsed'].max())
            self._update_time_scrollbar(start, end - start, t_max)
        else:
            self._updating_scroll = True
            self.timeScrollBar.setEnabled(False)
            self.timeScrollBar.setValue(0)
            self._updating_scroll = False

        self.ax.cla()
        self.twinaxCurrent.cla()
        self.twinaxPower.cla()
        self.twinaxTemp.cla()
        self.ax.set_title(self.cellLabel.text() + " (" + datetime.today().strftime('%Y-%m-%d') + ")")

        data.plot(ax=self.ax, x='t_elapsed', y=['voltage'], color='blue', xlim=xlim)
        self.ax.set_ylim(bottom=set_voltage)
        self.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1fV'))
        self.ax.xaxis.set_major_formatter(ticker.FuncFormatter(self._format_elapsed))
        self.ax.set_xlabel('Time')

        data.plot(ax=self.twinaxCurrent, x='t_elapsed', y=['current'], style='r')
        self.twinaxCurrent.set_ylim(bottom=0)
        self.twinaxCurrent.get_legend().remove()
        self.twinaxCurrent.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1fA'))

        if self.checkbox_p.isChecked():
            self.twinaxPower.spines.right.set_position(("axes", 1.1))
            data.plot(ax=self.twinaxPower, x='t_elapsed', y=['power'], color='green')
            self.twinaxPower.set_ylim(bottom=0)
            self.twinaxPower.get_legend().remove()
            self.twinaxPower.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f W'))
        else:
            self.twinaxPower.get_yaxis().set_visible(False)

        if self.checkbox_t.isChecked():
            self.twinaxTemp.spines.left.set_position(("axes", -0.1))
            data.plot(ax=self.twinaxTemp, x='t_elapsed', y=['temp'], color='grey')
            self.twinaxTemp.set_ylim(bottom=20)
            self.twinaxTemp.get_legend().remove()
            self.twinaxTemp.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f°'))
        else:
            self.twinaxTemp.get_yaxis().set_visible(False)

        lines1, labels1 = self.ax.get_legend_handles_labels()
        lines2, labels2 = self.twinaxCurrent.get_legend_handles_labels()
        lines3, labels3 = self.twinaxPower.get_legend_handles_labels()
        lines4, labels4 = self.twinaxTemp.get_legend_handles_labels()
        self.ax.legend(lines1 + lines2 + lines3 + lines4,
                       labels1 + labels2 + labels3 + labels4,
                       loc='lower left')
        self.ax.set_xlim(start, end)

        self.canvas.fig.tight_layout()
        self.canvas.draw()

    @staticmethod
    def _format_elapsed(value, _pos):
        total = int(max(0, round(value)))
        hours, rem = divmod(total, 3600)
        minutes, seconds = divmod(rem, 60)
        if hours:
            return '{:d}:{:02d}:{:02d}'.format(hours, minutes, seconds)
        return '{:d}:{:02d}'.format(minutes, seconds)

    def set_backend(self, backend):
        self.backend = backend
        backend.subscribe(self)
        self.swCCCV.set_backend(backend)
        self.internal_r.set_backend(backend)
        signals = backend.instr_worker.signals
        signals.ports_listed.connect(self.on_ports_listed)
        signals.connected.connect(self.on_device_connected)
        signals.disconnected.connect(self.on_device_disconnected)
        self.statusBar().showMessage("Disconnected")
        backend.request_port_list()

    def set_device_controls_enabled(self, enabled):
        self.set_voltage.setEnabled(enabled)
        self.set_current.setEnabled(enabled)
        self.set_timer.setEnabled(enabled)
        self.loadOnButton.setEnabled(enabled)
        self.loadOffButton.setEnabled(enabled)
        self.resetButton.setEnabled(enabled)

    def refresh_ports_clicked(self):
        self.backend.request_port_list()

    def open_clicked(self):
        if self.device_connected:
            self.openButton.setEnabled(False)
            self.backend.disconnect_port()
            return
        resource = self.portCombo.currentData()
        if not resource:
            self.statusBar().showMessage("No serial port selected")
            return
        self.openButton.setEnabled(False)
        self.portCombo.setEnabled(False)
        self.refreshPortsButton.setEnabled(False)
        self.backend.connect_port(resource)

    def on_ports_listed(self, ports):
        current = self.portCombo.currentData()
        self.portCombo.clear()
        for resource in ports:
            self.portCombo.addItem(resource_label(resource), resource)
        if self.portCombo.count() == 0:
            self.portCombo.addItem("(no ports found)", None)
        index = self.portCombo.findData(current)
        if index >= 0:
            self.portCombo.setCurrentIndex(index)

    def on_device_connected(self, resource):
        self.device_connected = True
        index = self.portCombo.findData(resource)
        if index >= 0:
            self.portCombo.setCurrentIndex(index)
        self.portCombo.setEnabled(False)
        self.refreshPortsButton.setEnabled(False)
        self.openButton.setText("CLOSE")
        self.openButton.setEnabled(True)
        self.set_device_controls_enabled(True)

    def on_device_disconnected(self):
        self.device_connected = False
        self.portCombo.setEnabled(True)
        self.refreshPortsButton.setEnabled(True)
        self.openButton.setText("OPEN")
        self.openButton.setEnabled(True)
        self.set_device_controls_enabled(False)
        self.set_load_ui(False)

    def closeEvent(self, event):
        self.logControl.save_settings()
        self.swCCCV.save_settings()
        self.internal_r.save_settings()
        self.save_settings()
        self.write_logs()

        self.backend.at_exit()
        event.accept()

    def set_load_ui(self, is_on):
        self._load_on = bool(is_on)
        if self._load_on:
            self.loadOnButton.setStyleSheet(LOAD_ON_ACTIVE)
            self.loadOffButton.setStyleSheet(LOAD_OFF_IDLE)
        else:
            self.loadOnButton.setStyleSheet(LOAD_ON_IDLE)
            self.loadOffButton.setStyleSheet(LOAD_OFF_ACTIVE)

    def load_on_clicked(self):
        if not self.device_connected:
            return
        self.backend.send_command({Instrument.COMMAND_ENABLE: True})

    def load_off_clicked(self):
        if not self.device_connected:
            return
        self.backend.send_command({Instrument.COMMAND_ENABLE: False})


    def voltage_changed(self):
        if self.set_voltage.hasFocus():
            self.set_voltage_timer.start(1000)

    def voltage_set(self):
        if not self.device_connected:
            return
        value = round(self.set_voltage.value(), 2)
        self.set_voltage.clearFocus()
        self.backend.send_command({Instrument.COMMAND_SET_VOLTAGE: value})

    def current_changed(self):
        if self.set_current.hasFocus():
            self.set_current_timer.start(1000)

    def current_set(self):
        if not self.device_connected:
            return
        value = round(self.set_current.value(), 2)
        self.set_current.clearFocus()
        self.backend.send_command({Instrument.COMMAND_SET_CURRENT: value})

    def timer_changed(self):
        if self.set_timer.hasFocus():
            self.set_timer_timer.start(1000)

    def timer_set(self):
        if not self.device_connected:
            return
        set_time = self.set_timer.time()
        value = time(set_time.hour(), set_time.minute(), set_time.second())
        self.set_timer.clearFocus()
        self.backend.send_command({Instrument.COMMAND_SET_TIMER: value})


    def reset_dev(self, s):
        if not self.device_connected:
            return
        self.resetButton.clearFocus()
        self.write_logs()
        self.swCCCV.reset()
        self.internal_r.reset()
        self.backend.datastore.reset()
        self._plot_data = None
        self.backend.send_command({Instrument.COMMAND_RESET: 0.0})

    def load_settings(self):
        settings = QSettings()

        self.resize(settings.value("MainWindow/size", QSize(1024, 600)))
        self.move(settings.value("MainWindow/pos", QPoint(0, 0)))
        self.cellLabel.setText(settings.value("MainWindow/cellLabel", 'Cell x'))
        self.checkbox_t.setCheckState(Qt.Checked if settings.value("MainWindow/checkbox_t", True) == 'true'  else Qt.Unchecked)
        self.checkbox_p.setCheckState(Qt.Checked if settings.value("MainWindow/checkbox_p", True) == 'true'  else Qt.Unchecked)


    def write_logs(self):
        if self.logControl.isChecked():
            self.internal_r.write(self.logControl.full_path,
                                  self.cellLabel.text())
            self.backend.datastore.write(self.logControl.full_path,
                                         self.cellLabel.text())

    def save_settings(self):
        settings = QSettings()

        settings.setValue("MainWindow/size", self.size())
        settings.setValue("MainWindow/pos", self.pos())
        settings.setValue("MainWindow/cellLabel", self.cellLabel.text())
        settings.setValue("MainWindow/checkbox_t", self.checkbox_t.isChecked())
        settings.setValue("MainWindow/checkbox_p", self.checkbox_p.isChecked())
        settings.sync()


class GUI:
    def __init__(self, backend):
        app = QtWidgets.QApplication(argv)
        self.window = MainWindow()
        self.window.set_backend(backend)
        app.exec_()
