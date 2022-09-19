import math

import PIL.Image
import PIL.ImageEnhance
import threading
from qtpy.QtCore import Qt
from qtpy import QtGui
from qtpy import QtWidgets

from .. import utils


class BrightnessContrastDialog(QtWidgets.QDialog):
    def __init__(self, img, callback, parent=None):
        super(BrightnessContrastDialog, self).__init__(parent)
        self.setModal(True)
        self.setWindowTitle(self.tr("Brightness/Contrast"))

        self.slider_brightness = self._create_slider()
        self.slider_contrast = self._create_slider()

        formLayout = QtWidgets.QFormLayout()
        formLayout.addRow(self.tr("Brightness"), self.slider_brightness)
        formLayout.addRow(self.tr("Contrast"), self.slider_contrast)
        self.setLayout(formLayout)

        assert isinstance(img, PIL.Image.Image)
        self.img = img
        self.callback = callback
        # self.pre_bright = self.slider_brightness.value()
        # self.pre_cont = self.slider_contrast.value()


    def onNewValue(self, value):
        brightness = self.slider_brightness.value() / 50.0
        contrast = self.slider_contrast.value() / 50.0

        # delta_b = math.fabs(self.slider_brightness.value() - self.pre_bright)
        # delta_c = math.fabs(self.slider_contrast.value() - self.pre_cont)
        #
        # if delta_b < 5 and delta_c < 5:
        #     return

        img = self.img
        img = PIL.ImageEnhance.Brightness(img).enhance(brightness)
        img = PIL.ImageEnhance.Contrast(img).enhance(contrast)

        threading.Timer(0.01, self.startShapeBright, [img]).start()

    def onNewValue_old(self, value):
        brightness = self.slider_brightness.value() / 50.0
        contrast = self.slider_contrast.value() / 50.0

        img = self.img
        img = PIL.ImageEnhance.Brightness(img).enhance(brightness)
        img = PIL.ImageEnhance.Contrast(img).enhance(contrast)

        img_data = utils.img_pil_to_data(img)
        qimage = QtGui.QImage.fromData(img_data)
        self.callback(qimage)

    def _create_slider(self):
        slider = QtWidgets.QSlider(Qt.Horizontal)
        slider.setRange(0, 150)
        slider.setValue(50)
        slider.valueChanged.connect(self.onNewValue)
        return slider

    def startShapeBright(self, *args):
        img = args[0]
        img_data = utils.img_pil_to_data(img)
        qimage = QtGui.QImage.fromData(img_data)
        self.callback(qimage)
        # self.pre_bright = self.slider_brightness.value()
        # self.pre_cont = self.slider_contrast.value()