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


class AppVersionDialog(QtWidgets.QDialog):
    def __init__(self, congig=None, parent=None):
        super(AppVersionDialog, self).__init__(parent)
        self._config = congig
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFont(appFont())
        self.setWindowTitle("버전정보" if self._config['local_lang'] == 'ko_KR' else 'Version')
        self._parent = parent
        trans = self._parent.topToolWidget.trans.pos()
        if trans:
            self.move(trans.x() + 300, trans.y() + 50)

        hvox_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel()
        self.label.setMidLineWidth(35)
        entxt = 'The current version is %s' % self._config['app_version']
        kotxt = '현재 버전정보는 %s 입니다.' % self._config['app_version']
        self.label.setText(kotxt if self._config['local_lang'] == 'ko_KR' else entxt)
        hvox_layout.addWidget(self.label)

        formLayout = QtWidgets.QFormLayout()
        formLayout.addRow(hvox_layout)

        self.setLayout(formLayout)
        self.setMinimumWidth(250)


class LoadingLabelProgress(QtWidgets.QWidget):
    def __init__(self, parent=None, config=None, size=None):
        self._config = config
        self._isEnd = False
        self.step = 0
        self.size = size if size is not None else 1
        super(LoadingLabelProgress, self).__init__(parent)
        self.setMinimumWidth(250)
        self.setMinimumHeight(150)
        trans = parent.topToolWidget.trans.pos()
        if trans:
            self.move(trans.x() + 300, trans.y() - 40)
        # qr = self.frameGeometry()
        # cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        # qr.moveCenter(cp)
        # self.move(qr.topLeft())
        self.pbar = QtWidgets.QProgressBar(self)
        self.pbar.setMinimum(0)
        #self.pbar.setMaximum(self.size)
        self.pbar.setMaximum(self.size)
        self.pbar.setValue(0)
        self.pbar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hvox_layout = QtWidgets.QHBoxLayout()
        hvox_layout.addWidget(self.pbar)
        self.setLayout(hvox_layout)

    def doAction(self):
        self.step = self.step + self.size / 100
        if self.step < self.size:
            self.pbar.setValue(self.step)

    def closeEvent(self, event):
        if self._isEnd is False:
            event.ignore()