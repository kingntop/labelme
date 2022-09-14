import PIL.Image
import PIL.ImageEnhance
from qtpy.QtCore import Qt
from qtpy import QtGui
from qtpy import QtWidgets

from .. import utils
from labelme.utils import appFont


class PolygonTransDialog(QtWidgets.QDialog):
    def __init__(self, callback, parent=None):
        super(PolygonTransDialog, self).__init__(parent)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFont(appFont())
        self.setWindowTitle(self.tr("Transparency"))
        self._parent = parent
        trans = self._parent.topToolWidget.trans.pos()
        if trans:
            self.move(trans.x() + 300, trans.y() + 50)

        self.slider_trans = self._create_slider()

        hvox_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel()
        self.label.setMidLineWidth(35)
        self.label.setText("100%")


        hvox_layout.addWidget(self.slider_trans)
        hvox_layout.addWidget(self.label)

        formLayout = QtWidgets.QFormLayout()
        formLayout.addRow(self.tr("Transparency"), hvox_layout)

        self.setLayout(formLayout)
        self.setMinimumWidth(250)
        self.callback = callback

    def _create_slider(self):
        slider = QtWidgets.QSlider(Qt.Horizontal, self)
        slider.setRange(0, self._parent.polygonTrans_deta_value)
        slider.setValue(0)
        #slider.setTickInterval(10)
        #slider.setSingleStep(3)
        slider.valueChanged.connect(self.onNewValue)
        return slider

    def onNewValue(self, value):
        x = 100 * (self._parent.polygonTrans_deta_value - value) / self._parent.polygonTrans_deta_value
        self.label.setText("{}%".format(int(x)))
        self.callback(value)
