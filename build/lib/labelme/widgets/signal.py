"""
class the signla
"""
import sys
#from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, QObject


class Signal(QObject):
    polygon_check_signal = pyqtSignal(int)

    def signal_run(self):
        self.polygon_check_signal.emit()
