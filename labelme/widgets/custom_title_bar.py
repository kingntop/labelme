from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtCore import QEvent, Qt
from qtpy.QtWidgets import QGridLayout, QHBoxLayout, \
    QLabel, QLineEdit, QToolButton, QDockWidget, QStyle, QApplication, QCheckBox
from keyboard import press
from labelme.widgets.signal import Signal
from .. import utils
from labelme.utils import appFont


class DockInPutTitleBar(QtWidgets.QWidget):
    def __init__(self, dockWidget, bartype, app):
        super(DockInPutTitleBar, self).__init__(dockWidget)
        self._bartype = bartype
        self._app = app
        self._dockWidget = dockWidget
        self.setFont(appFont())

        boxLayout = QHBoxLayout(self)
        boxLayout.setSpacing(1)
        boxLayout.setContentsMargins(1, 1, 1, 1)

        self.titleLabel = QLabel(self)
        lang = self._app._config["local_lang"]
        if self._bartype == "gradesbar":
            if lang == "ko_KR":
                self.titleLabel.setText("등급 (총 %s)" % 0)
            else:
                self.titleLabel.setText("Grades (Total %s)" % 0)
        if self._bartype == "productsbar":
            if lang == "ko_KR":
                self.titleLabel.setText("대표 품목 (총 %s)" % 0)
            else:
                self.titleLabel.setText("Products (Total %s)" % 0)


        self.hidnBtn = QtWidgets.QPushButton(self)
        self.hidnBtn.setText('.')
        self.hidnBtn.setFixedWidth(10)
        self.hidnBtn.clicked.connect(self.clickProgramicallyBtn)  # must click this button Programically
        self.hidnBtn.hide()

        ninput = "New Input"
        if lang == "ko_KR":
            ninput = "신규 입력"
        if self._bartype == "gradesbar" and self._app._config["grade_yn"] == "Y":
            self.newLabel = QLabel(ninput)
            self.titleEdit = QLineEdit(self)
            #  self.titleEdit.hide()
            #self.titleEdit.editingFinished.connect(self.finishEdit)
            self.titleEdit.returnPressed.connect(self.returnPresshandle)

        elif self._bartype == "productsbar" and self._app._config["product_yn"] == "Y":
            self.newLabel = QLabel(ninput)
            self.titleEdit = QLineEdit(self)
            # self.titleEdit.hide()
            #self.titleEdit.editingFinished.connect(self.finishEdit)
            self.titleEdit.returnPressed.connect(self.returnPresshandle)

        self.dockButton = QToolButton(self)
        #self.dockButton.setIcon(QApplication.style().standardIcon(QStyle.SP_TitleBarNormalButton))
        self.dockButton.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TitleBarNormalButton")))
        self.dockButton.setFixedSize(14, 14)
        #self.dockButton.setMaximumSize(buttonSize)
        self.dockButton.setAutoRaise(True)
        self.dockButton.clicked.connect(self.toggleFloating)

        self.closeButton = QToolButton(self)
        self.closeButton.setFixedSize(14, 14)
        #self.closeButton.setMaximumSize(buttonSize)
        self.closeButton.setAutoRaise(True)
        #self.closeButton.setIcon(QApplication.style().standardIcon(QStyle.SP_DockWidgetCloseButton))
        self.closeButton.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TitleBarCloseButton")))
        self.closeButton.clicked.connect(self.closeParent)

        boxLayout.addSpacing(6)
        boxLayout.addWidget(self.titleLabel, 0, QtCore.Qt.AlignLeft)
        boxLayout.addWidget(self.hidnBtn, 0, QtCore.Qt.AlignLeft)
        boxLayout.addStretch()
        boxLayout.addSpacing(20)

        if self._bartype == "gradesbar" and self._app._config["grade_yn"] == "Y":
            boxLayout.addWidget(self.newLabel, 0, QtCore.Qt.AlignRight)
            boxLayout.addSpacing(6)
            boxLayout.addWidget(self.titleEdit, 0, QtCore.Qt.AlignRight)
            boxLayout.addSpacing(5)

        elif self._bartype == "productsbar" and self._app._config["product_yn"] == "Y":
            boxLayout.addWidget(self.newLabel, 0, QtCore.Qt.AlignRight)
            boxLayout.addSpacing(6)
            boxLayout.addWidget(self.titleEdit, 0, QtCore.Qt.AlignRight)
            boxLayout.addSpacing(5)

        boxLayout.addWidget(self.dockButton, 0, QtCore.Qt.AlignRight)
        boxLayout.addSpacing(5)
        boxLayout.addWidget(self.closeButton, 0, QtCore.Qt.AlignRight)

        dockWidget.featuresChanged.connect(self.onFeaturesChanged)

        self.onFeaturesChanged(dockWidget.features())
        # self.setTitle(dockWidget.windowTitle())

        dockWidget.installEventFilter(self)

    def eventFilter(self, source, event):
        try:
            if event.type() == QEvent.WindowTitleChange:
                pass
            return super(DockInPutTitleBar, self).eventFilter(source, event)
        except Exception as e:
            pass
            #self.setTitle(source.windowTitle())
        return super(DockInPutTitleBar, self).eventFilter(source, event)

    def startEdit(self):
        #print("startEdit")
        #self.titleLabel.hide()
        #self.titleEdit.show()
        #self.titleEdit.setFocus()
        pass

    def finishEdit(self):
        #self.titleEdit.hide()
        #self.titleLabel.show()
        #self.parent().setWindowTitle(self.titleEdit.text())
        #print("finishEdit")
        pass

    def returnPresshandle(self):  # called when it press enter key
        input_str = self.titleEdit.text()
        re_str = input_str.strip()
        if len(re_str) < 1:
            return

        if self._bartype == "gradesbar":
            _customlistwidget = self._dockWidget.widget()
            if _customlistwidget and len(_customlistwidget.items_list) > 0:
                _customlistwidget.addNewGrade(re_str)
                self.titleEdit.setText("")

        if self._bartype == "productsbar":
            # print(self.objectName() + re_str)
            _customlistwidget = self._dockWidget.widget()
            if _customlistwidget and self._app:
                self._app.sendProductToServer(re_str, self._app.addProduct)
                self.titleEdit.setText("")

    def onFeaturesChanged(self, features):
        if not features & QDockWidget.DockWidgetVerticalTitleBar:
            self.closeButton.setVisible(
                features & QDockWidget.DockWidgetClosable)
            self.dockButton.setVisible(
                features &
                QDockWidget.DockWidgetFloatable)
        else:
            raise ValueError('vertical title bar not supported')

    def setTitle(self, title):
        self.titleLabel.setText(title)
        #self.titleEdit.setText(title)

    def toggleFloating(self):
        self.parent().setFloating(not self.parent().isFloating())

    def closeParent(self):
        self.parent().toggleViewAction().setChecked(False)
        self.parent().hide()

    def mouseDoubleClickEvent(self, event):
        if event.pos().x() <= self.titleLabel.width():
            self.startEdit()
        else:
            # this keeps the normal double-click behaviour
            super(DockInPutTitleBar, self).mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        event.ignore()

    def mousePressEvent(self, event):
        event.ignore()

    def mouseMoveEvent(self, event):
        event.ignore()

    # polygon list add event
    def clickProgramicallyBtn(self):
        self._app.receiveGradesFromServer()

    # non using
    def pressEnterKeyForce(self):
        self.titleEdit.setFocus()
        self.titleEdit.setText("")
        press('enter')


class DockCheckBoxTitleBar(QtWidgets.QWidget):
    def __init__(self, app, dockWidget):
        super(DockCheckBoxTitleBar, self).__init__(dockWidget)
        self._app = app
        self.setFont(appFont())
        #self.signal = Signal()
        #self.signal.polygon_check_signal.connect(self.polygon_label_status)
        boxLayout = QHBoxLayout(self)
        boxLayout.setSpacing(1)
        boxLayout.setContentsMargins(1, 1, 1, 1)

        self.titleLabel = QLabel(self)
        polyT = "Polygon Labels (Total %s)"
        if self._app._config["local_lang"] == "ko_KR":
            polyT = "다각형 레이블 (총 %s)"
        self.titleLabel.setText(polyT % 0)

        self.hidnBtn = QtWidgets.QPushButton(self)
        self.hidnBtn.setText('')
        self.hidnBtn.setFixedWidth(10)
        self.hidnBtn.clicked.connect(self.clickProgramicallyBtn)  # must click this button Programically
        self.hidnBtn.hide()

        self.checkbox = QCheckBox(self)
        self.checkbox.stateChanged.connect(self.stateChangeHandle)
        self.checkbox.setCheckState(Qt.Checked)

        self.dockButton = QToolButton(self)
        #self.dockButton.setIcon(QApplication.style().standardIcon(QStyle.SP_TitleBarNormalButton))
        self.dockButton.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TitleBarNormalButton")))
        self.dockButton.setFixedSize(14, 14)
        #self.dockButton.setMaximumSize(buttonSize)
        self.dockButton.setAutoRaise(True)
        self.dockButton.clicked.connect(self.toggleFloating)

        self.closeButton = QToolButton(self)
        self.closeButton.setFixedSize(14, 14)
        #self.closeButton.setMaximumSize(buttonSize)
        self.closeButton.setAutoRaise(True)
        #self.closeButton.setIcon(QApplication.style().standardIcon(QStyle.SP_DockWidgetCloseButton))
        self.closeButton.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TitleBarCloseButton")))
        self.closeButton.clicked.connect(self.closeParent)

        boxLayout.addSpacing(6)
        boxLayout.addWidget(self.titleLabel, 0, QtCore.Qt.AlignLeft)
        boxLayout.addWidget(self.hidnBtn, 0, QtCore.Qt.AlignLeft)
        boxLayout.addStretch()
        boxLayout.addWidget(self.checkbox, 0, QtCore.Qt.AlignRight)
        boxLayout.addSpacing(5)
        boxLayout.addWidget(self.dockButton, 0, QtCore.Qt.AlignRight)
        boxLayout.addSpacing(5)
        boxLayout.addWidget(self.closeButton, 0, QtCore.Qt.AlignRight)

        dockWidget.featuresChanged.connect(self.onFeaturesChanged)

        self.onFeaturesChanged(dockWidget.features())
        #self.setTitle(dockWidget.windowTitle())

        dockWidget.installEventFilter(self)
        self.setContentsMargins(0, 3, 0, 5)
        # self.setStyleSheet("QWidget { background: rgb(222, 222, 222); }")

    def eventFilter(self, source, event):
        #if event.type() == QEvent.WindowTitleChange:
        #    self.setTitle(source.windowTitle())
        return super(DockCheckBoxTitleBar, self).eventFilter(source, event)


    def onFeaturesChanged(self, features):
        if not features & QDockWidget.DockWidgetVerticalTitleBar:
            self.closeButton.setVisible(
                features & QDockWidget.DockWidgetClosable)
            self.dockButton.setVisible(
                features &
                QDockWidget.DockWidgetFloatable)
        else:
            raise ValueError('vertical title bar not supported')

    def setTitle(self, title):
        self.titleLabel.setText(title)

    def stateChangeHandle(self, state):
        if state == Qt.Checked:
            self._app.labelList.checkStatus(True)
        else:
            self._app.labelList.checkStatus(False)

    # receiver function signal
    def polygon_label_status(self, arg):
        print(arg)

    def toggleFloating(self):
        self.parent().setFloating(not self.parent().isFloating())

    def closeParent(self):
        self.parent().toggleViewAction().setChecked(False)
        self.parent().hide()

    # polygon list add event
    def clickProgramicallyBtn(self):
        self._app.receiveLabelsFromServerByGrade()