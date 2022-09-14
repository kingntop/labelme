# imports
from qtpy import QtGui
from qtpy.QtWidgets import QLabel


class CQLabel(QLabel):
    def __init__(self, txt, parent):
        super(CQLabel, self).__init__()
        self.setText(txt)
        self.setContentsMargins(1, 1, 1, 1)
        self._parent = parent

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent):
        # print("click " + self.text())
        self.setStyleSheet("QLabel { background-color: rgb(204, 232, 255); border: 0; padding:2px}")
        self._parent._selected_item = self.text()
        self._parent.itemClickEventHandle()
