from signal import signal, SIGTERM, SIGINT
from sys import argv, exit
import argparse
import logging

from PyQt5.QtCore import QCoreApplication, QThreadPool

from data_store import DataStore
from gui.gui import GUI
from instr_thread import InstrumentWorker


def parse_args():
    parser = argparse.ArgumentParser(
        description='Control software for the Atorch DL24 electronic load.')
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='print debug messages to the console')
    args, remaining = parser.parse_known_args()
    argv[:] = [argv[0]] + remaining
    return args


def setup_logging(verbose):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format='%(message)s',
    )


class Main:
    def __init__(self):
        QCoreApplication.setOrganizationName('github.com/misdoro')
        QCoreApplication.setApplicationName('Battery tester')
        self.threadpool = QThreadPool()
        self.instr_thread()
        self.datastore = DataStore()
        signal(SIGTERM, self.terminate_process)
        signal(SIGINT, self.terminate_process)
        self.data_receivers = set()
        GUI(self)

    def instr_thread(self):
        self.instr_worker = InstrumentWorker()
        self.instr_worker.signals.data_row.connect(self.data_callback)
        self.instr_worker.signals.status_update.connect(self.status_callback)
        self.threadpool.start(self.instr_worker)

    def subscribe(self, receiver):
        self.data_receivers.add(receiver)

    def data_callback(self, data):
        self.datastore.append(data)
        for r in self.data_receivers:
            r.data_row(self.datastore, data)

    def status_callback(self, status):
        for r in self.data_receivers:
            if hasattr(r, 'status_update'):
                r.status_update(status)

    def send_command(self, command):
        self.instr_worker.signals.command.emit(command)

    def request_port_list(self):
        self.instr_worker.signals.request_port_list.emit()

    def connect_port(self, resource):
        self.instr_worker.signals.connect_requested.emit(resource)

    def disconnect_port(self):
        self.instr_worker.signals.disconnect_requested.emit()

    def at_exit(self):
        self.instr_worker.signals.exit.emit()
        self.threadpool.waitForDone()

    def terminate_process(self, signal, _stack):
        self.at_exit()
        exit()


if __name__ == "__main__":
    setup_logging(parse_args().verbose)
    Main()
