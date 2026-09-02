from time import sleep

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
import logging

from instruments import Instruments

log = logging.getLogger(__name__)


class InstrumentSignals(QObject):
    exit = pyqtSignal()
    start = pyqtSignal()
    stop = pyqtSignal()
    data_row = pyqtSignal(dict)
    status_update = pyqtSignal(str)
    command = pyqtSignal(dict)
    request_port_list = pyqtSignal()
    ports_listed = pyqtSignal(list)
    connect_requested = pyqtSignal(str)
    disconnect_requested = pyqtSignal()
    connected = pyqtSignal(str)
    disconnected = pyqtSignal()


class InstrumentWorker(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = InstrumentSignals()
        self.signals.command.connect(self.add_command)
        self.signals.exit.connect(self.handle_exit)
        self.signals.start.connect(self.handle_start)
        self.signals.stop.connect(self.handle_stop)
        self.signals.request_port_list.connect(self.handle_request_port_list)
        self.signals.connect_requested.connect(self.handle_connect_requested)
        self.signals.disconnect_requested.connect(
            self.handle_disconnect_requested)

        self.loop = True
        self.running = False
        self.commands = []
        self.instr = None
        self.pending_port_list = False
        self.pending_connect = None
        self.pending_disconnect = False

    @pyqtSlot()
    def run(self):
        instruments = Instruments()
        self.signals.status_update.emit("Disconnected")

        while self.loop:
            if self.pending_port_list:
                self.pending_port_list = False
                self.signals.ports_listed.emit(
                    instruments.list_serial_resources())

            if self.pending_disconnect:
                self.pending_disconnect = False
                self._close_instr()
                self.running = False
                self.signals.status_update.emit("Disconnected")
                self.signals.disconnected.emit()

            if self.pending_connect:
                resource = self.pending_connect
                self.pending_connect = None
                self._close_instr()
                self.running = False
                self.signals.status_update.emit(
                    "Connecting to {}...".format(resource))
                driver = instruments.open(resource)
                if driver:
                    self.instr = driver
                    self.running = True
                    self.signals.connected.emit(resource)
                    self.signals.status_update.emit(
                        "Connected to {} on port {}".format(
                            self.instr.name, self.instr.port))
                else:
                    self.signals.status_update.emit(
                        "Failed to open {}".format(resource))
                    self.signals.disconnected.emit()

            if self.instr:
                if len(self.commands) > 0:
                    self.handle_command(self.commands.pop(0))
                if self.running:
                    self.signals.data_row.emit(self.instr.readAll())
            else:
                self.commands.clear()

            sleep(.5 if self.running else .05)

        self._close_instr()

    def _close_instr(self):
        if not self.instr:
            return
        try:
            self.instr.close()
        except Exception as err:
            log.debug('%s', err)
        self.instr = None

    def handle_command(self, command):
        if not self.instr:
            return
        for k, v in command.items():
            self.instr.command(k, v)

    def handle_start(self):
        if self.instr:
            self.running = True

    def handle_stop(self):
        self.running = False

    def handle_exit(self):
        self.loop = False

    def handle_request_port_list(self):
        self.pending_port_list = True

    def handle_connect_requested(self, resource):
        self.pending_connect = resource

    def handle_disconnect_requested(self):
        self.pending_disconnect = True

    def add_command(self, cmd):
        self.commands.append(cmd)
