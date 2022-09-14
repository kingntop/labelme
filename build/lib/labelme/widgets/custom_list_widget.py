import threading
from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtGui import QColor, QColorConstants
from qtpy.QtCore import Qt

from qtpy.QtWidgets import QLayout, QHBoxLayout, QVBoxLayout, \
    QLabel, QLineEdit, QToolButton, QScrollArea, QStyle, QListWidgetItem
from PyQt5.QtCore import pyqtSlot, QTimer
from .. import utils
from labelme.widgets.custom_qlabel import CQLabel
from labelme.widgets.signal import Signal
from labelme.shape import Shape
from labelme.utils import appFont

# grade list
class CustomListWidget(QtWidgets.QWidget):
    def __init__(self, _app=None, objtag=None):
        self.items_list = []
        self._app = _app
        self._selected_item = None
        self._objtag = objtag
        self._items = []
        self._status = False
        super(CustomListWidget, self).__init__()
        #self.setFont(appFont())

        self.initUI()

    def initUI(self):

        self.HB_layout = QHBoxLayout()
        self.HB_layout.setContentsMargins(6, 6, 6, 6)
        self.HB_layout.setSpacing(0)
        self.HB_layout.setSizeConstraint(QLayout.SetMinimumSize)
        #self.HB_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # refer here funtion addItemsToQHBox

        twidget = QtWidgets.QWidget()
        twidget.setLayout(self.HB_layout)
        twidget.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); }")
        scroll = QScrollArea()
        scroll.setWidget(twidget)
        scroll.setWidgetResizable(True)

        hb_layout = QHBoxLayout()
        hb_layout.addWidget(scroll)
        hb_layout.setContentsMargins(0, 0, 0, 0)
        hb_layout.setSpacing(0)
        self.setLayout(hb_layout)

    def set(self, items):
        self._items.clear()
        self._items = items
        self.addItemsToQHBox(self._items)

    def get(self):
        return self._items

    def itemClickEventHandle(self):
        # process ploygon with one selected product
        if self._selected_item is not None and self._objtag == "grades":
            self._app.selected_grade = self._selected_item
            threading.Timer(0.1, self._app.receiveProductsFromServerByGrade).start()
            threading.Timer(0.2, self._app.customLabelTitleBar.hidnBtn.clicked.emit).start()
            # self._app.queueEvent(self._app.receiveProductsFromServerByGrade)
            # self._app.queueEvent(self._app.customLabelTitleBar.hidnBtn.clicked.emit)

        elif self._selected_item is not None and self._objtag == "products":
            pass  # process ploygon with one selected product

        if len(self.items_list) > 0:
            item_count = len(self.items_list)
            for j in range(0, item_count):
                lbObj = self.items_list.__getitem__(j)
                if lbObj is not None:
                    txt = lbObj.text()
                    objname = lbObj.objectName()  # will do using after this val
                    if txt != self._selected_item:
                        lbObj.setStyleSheet("QLabel { border: 0px solid #aaa; padding:2px}")

    def addItemsToQHBox(self, items):
        if len(items) > 0:
            self._status = False
            self.clearLayout(self.HB_layout)

            self.items_list.clear()
            item_count = len(items)
            done = False
            icount = 0
            for j in range(0, item_count):
                vbox = QVBoxLayout()
                vbox.setContentsMargins(0, 0, 1, 0)
                vbox.setSpacing(1)
                for i in range(4):
                    if icount < item_count:
                        item = items[icount]
                        if item is not None:
                            qlb = CQLabel(item["grade"], self)
                            qlb.setStyleSheet("QLabel { border: 0px solid #aaa; padding:2px}")
                            qlb.setFont(appFont())
                            vbox.addWidget(qlb)
                            vbox.sizeHint()
                            self.items_list.append(qlb)
                            icount = icount + 1
                    else:
                        done = True
                        break
                if done is True:
                    vc = vbox.count()
                    if vc > 0:
                        qq = QtWidgets.QWidget()
                        qq.setStyleSheet("QWidget { border-right: 1px solid #aaa;}")
                        qq.setLayout(vbox)
                        #qq.setMaximumWidth(102)
                        self.HB_layout.addWidget(qq)
                    break
                else:
                    qq = QtWidgets.QWidget()
                    qq.setStyleSheet("QWidget { border-right: 1px solid #aaa;}")
                    qq.setLayout(vbox)
                    #qq.setMaximumWidth(102)
                    self.HB_layout.addWidget(qq)

            if self._app.grade_title_bar:
                if self._app._config["local_lang"] == "ko_KR":
                    self._app.grade_title_bar.titleLabel.setText("등급 (총 %s)" % len(self.items_list))
                else:
                    self._app.grade_title_bar.titleLabel.setText("Grades (Total %s)" % len(self.items_list))

            self._status = True

    def addNewGrade(self, new_str):
        nonexist = True
        items = []
        if new_str != "":
            for litem in self.items_list:
                txt = litem.text()
                items.append({"grade": txt})
                if new_str == txt:
                    nonexist = False
            if nonexist is True:
                items.insert(0, {"grade": new_str})
                self._app.sendGradeToServer(new_str, items, self.addItemsToQHBox)
                #self.addItemsToQHBox(items)
            else:
                return QtWidgets.QMessageBox.critical(
                    self, "Error", "<p><b>%s</b></p>%s" % ("Error", "The grade already exists.")
                )
        else:  # delete empty string from grade list
            for litem in self.items_list:
                txt = litem.text()
                if txt:
                    items.append({"grade": txt})
            self.addItemsToQHBox(items)


    def clearLayout(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if isinstance(item, QtWidgets.QWidgetItem):
                #print("widget" + str(item))
                item.widget().close()
                # or
                # item.widget().setParent(None)
            elif isinstance(item, QtWidgets.QSpacerItem):
                #print("spacer " + str(item))
                # no need to do extra stuff
                pass
            else:
                #print("layout " + str(item))
                self.clearLayout(item.layout())
            # remove the item from layout
            layout.removeItem(item)

class MyCustomWidget(QtWidgets.QWidget):
    _shape = None
    _parent = None
    _checked = True

    def __init__(self, shape, parent=None, num=None):
        super(MyCustomWidget, self).__init__(parent)
        self._parent = parent

        if isinstance(shape, Shape):
            self._shape = shape
        else:
            #sp = {"id": shape["id"], "label": shape["label"], "color": shape["color"]}
            sp = Shape()
            sp.label_display = shape["label_display"]
            sp.label = shape["label"]
            sp.grade = shape["grade"]
            sp.color = shape["color"]
            self._shape = sp

        self.row = QtWidgets.QHBoxLayout()
        self.row.setContentsMargins(0, 1, 0, 1)

        if num is not None:
            if num < 10000:
                idx = "%04d" % num
            else:
                idx = "%08d" % num
        else:
            idx = self._parent.count()
            if idx < 10000:
                idx = "%04d" % idx
            else:
                idx = "%08d" % idx

        self._id = idx
        self.label = QtWidgets.QLabel("#{}  {}".format(self._id, self._shape.label_display))
        self.label.setFont(appFont())

        c_txt = self._shape.color
        if not c_txt or "" == c_txt:
            c_txt = "#808000"
        Qc = QtGui.QColor(c_txt)
        r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
        tmpcolor = QtGui.QColor(r, g, b)
        color_txt = tmpcolor.name(QtGui.QColor.HexRgb)

        self.clrlabel = QtWidgets.QLabel()
        self.clrlabel.setStyleSheet(
            "QLabel{border: 1px soild #aaa; background: %s;}" % color_txt)
        self.clrlabel.setFixedWidth(8)

        self.checkbox = QtWidgets.QCheckBox("")
        self.checkbox.setCheckState(Qt.Checked)  # Qt.Checked
        self.checkbox.stateChanged.connect(self.checkBoxStateChangeHandle)

        self.row.addWidget(self.label)
        self.row.addStretch()
        self.row.addWidget(self.clrlabel)
        self.row.addSpacing(6)
        self.row.addWidget(self.checkbox)
        self.row.addSpacing(33)
        self.setLayout(self.row)
        self.setContentsMargins(6, 3, 6, 3)

    def checkBoxStateChangeHandle(self, state):
        if state == Qt.Checked:
            self._checked = True
        else:
            self._checked = False
        self._parent._app.labelItemChanged(self)

    def reDraw(self, idn):
        if idn < 10000:
            idx = "%04d" % idn
        else:
            idx = "%08d" % idn
        self._id = idx
        self.label.setText("#{}  {}".format(self._id, self._shape.label_display))



# polygon list
class CustomLabelListWidget(QtWidgets.QListWidget):
    itemSelectionChanged = QtCore.Signal(list, list)

    def __init__(self, app):
        super(CustomLabelListWidget, self).__init__()
        #self.signal = Signal()
        self._app = app
        self._selected_item = []
        self._itemList = []

        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.selectionModel().selectionChanged.connect(
            self.itemSelectionChangedEvent
        )

    def addShapes(self, shapes):
        if len(shapes) < 1:
            return
        self.clear()
        for shape in shapes:
            rowItem = RowWidgetItem(shape, self)
            self.vContent_layout.addWidget(rowItem)
            #self._itemList.append(rowItem)

        polyT = "Polygon Labels (Total %s)"
        if self._app._config["local_lang"] == "ko_KR":
            polyT = "다각형 레이블 (총 %s)"
        if self._app.shape_dock:
            self._app.shape_dock.titleBarWidget().titleLabel.setText(polyT % len(self._itemList))

    def itemSelectionChangedEvent(self, selected, deselected):
        selected = [self.itemFromIndex(i) for i in selected.indexes()]
        deselected = [self.itemFromIndex(i) for i in deselected.indexes()]
        self.itemSelectionChanged.emit(selected, deselected)


    def addShape(self, shape):
        if shape:
            listitem = QListWidgetItem(self)
            self.addItem(listitem)
            row = MyCustomWidget(shape, self)
            listitem.setSizeHint(row.minimumSizeHint())
            self.setItemWidget(listitem, row)
            #self._itemList.append(row)

    def findItemByShape(self, shape):
        for i in range(self.count()):
            widgetitem = self.item(i)
            if isinstance(widgetitem, QListWidgetItem):
                item = self.itemWidget(widgetitem)
                if item and item._shape == shape:
                    return item

        return None

    def findWidgetItemByItem(self, pitem):
        for i in range(self.count()):
            widgetitem = self.item(i)
            if isinstance(widgetitem, QListWidgetItem):
                item = self.itemWidget(widgetitem)
                if item and item._shape == pitem._shape:
                    return widgetitem, i

        return None, 0

    def selectedItems(self):
        return [self.itemFromIndex(i) for i in self.selectedIndexes()]

    def selectItem(self, pitem):
        wdgitem, x = self.findWidgetItemByItem(pitem)
        if wdgitem is not None:
            self.setCurrentItem(wdgitem, QtCore.QItemSelectionModel.Select)

    def scrollTooItem(self, item):
        wdgitem, x = self.findWidgetItemByItem(item)
        self.scrollToItem(wdgitem)

    def checkStatus(self, flag):
        if flag == 1:
            for i in range(self.count()):
                widgetitem = self.item(i)
                if isinstance(widgetitem, QListWidgetItem):
                    item = self.itemWidget(widgetitem)
                    if item and item.checkbox:
                        item.checkbox.setCheckState(Qt.Checked)
        else:
            for i in range(self.count()):
                widgetitem = self.item(i)
                if isinstance(widgetitem, QListWidgetItem):
                    item = self.itemWidget(widgetitem)
                    if item and item.checkbox:
                        item.checkbox.setCheckState(Qt.Unchecked)

    def removeItem(self, item):
        wg, index = self.findWidgetItemByItem(item)
        #index = self.indexFromItem(item)
        self.takeItem(index)
        #self.removeItemWidget(wg)

    def reSort(self):
        for i in range(self.count()):
            widgetitem = self.item(i)
            if isinstance(widgetitem, QListWidgetItem):
                item = self.itemWidget(widgetitem)
                if item and item.label:
                    item.reDraw(i + 1)

    def getShapeItems(self):
        s_items = []
        for i in range(self.count()):
            widgetitem = self.item(i)
            if isinstance(widgetitem, QListWidgetItem):
                item = self.itemWidget(widgetitem)
                if item and item._shape:
                    s_items.append(item)
        return s_items




class topToolWidget(QtWidgets.QWidget):
    def __init__(self, objname, app=None):
        super(topToolWidget, self).__init__()
        self.setObjectName(objname)
        self.setMaximumHeight(50)
        self.setContentsMargins(0, 0, 0, 0)
        # self.setFixedWidth(500)
        self._app = app
        self.setFont(appFont())

        # setting UI
        self.initUI()

    def initUI(self):
        hbox_layout = QHBoxLayout()
        hbox_layout.setSpacing(0)
        hbox_layout.setContentsMargins(5, 5, 0, 0)

        self.polygon = QToolButton()
        self.polygon.setIcon(utils.newIcon("poly"))
        self.polygon.setIconSize(QtCore.QSize(20, 20))
        self.polygon.clicked.connect(self.polygonClick)
        self.polygon.setEnabled(False)
        #self.polygon.setFixedSize(150, 150)

        self.rect = QToolButton()
        self.rect.setIcon(utils.newIcon("rect"))
        self.rect.setIconSize(QtCore.QSize(20, 20))
        self.rect.clicked.connect(self.rectClick)
        self.rect.setEnabled(False)

        self.circle = QToolButton()
        self.circle.setIcon(utils.newIcon("circle"))
        self.circle.setIconSize(QtCore.QSize(20, 20))
        self.circle.clicked.connect(self.circleClick)
        self.circle.setEnabled(False)

        self.line = QToolButton()
        self.line.setIcon(utils.newIcon("line"))
        self.line.setIconSize(QtCore.QSize(20, 20))
        self.line.clicked.connect(self.lineClick)
        self.line.setEnabled(False)

        self.arrow = QToolButton()
        self.arrow.setIcon(utils.newIcon("CursorArrow"))
        self.arrow.setIconSize(QtCore.QSize(20, 20))
        self.arrow.clicked.connect(self.arrowClick)
        self.arrow.setEnabled(False)

        self.trans = QToolButton()
        self.trans.setIcon(utils.newIcon("ftrans"))
        self.trans.setIconSize(QtCore.QSize(20, 20))
        self.trans.clicked.connect(self.transClick)
        self.trans.setEnabled(False)

        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.polygon, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.rect, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.circle, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.line, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.arrow, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.trans, 0, QtCore.Qt.AlignLeft)

        hbox_layout.addStretch()

        self.setLayout(hbox_layout)

    def polygonClick(self, arg):
        self.polygon.setEnabled(False)
        self.rect.setEnabled(True)
        self.circle.setEnabled(True)
        self.line.setEnabled(True)
        if self._app is not None:
            self._app.selected_shapType = "polygon"
            self._app.toggleDrawMode(False, createMode="polygon")

    def rectClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(False)
        self.circle.setEnabled(True)
        self.line.setEnabled(True)
        if self._app is not None:
            self._app.selected_shapType = "rectangle"
            self._app.toggleDrawMode(False, createMode="rectangle")

    def circleClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(True)
        self.circle.setEnabled(False)
        self.line.setEnabled(True)
        if self._app is not None:
            self._app.selected_shapType = "circle"
            self._app.toggleDrawMode(False, createMode="circle")

    def lineClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(True)
        self.circle.setEnabled(True)
        self.line.setEnabled(False)
        if self._app is not None:
            self._app.selected_shapType = "line"
            self._app.toggleDrawMode(False, createMode="line")

    def arrowClick(self):
        self._app.toggleDrawMode(True)
        #self._app.canvas.setEnabled(False)
        self._app.canvas.overrideCursor(QtCore.Qt.ArrowCursor)

    def transClick(self):
        self.trans.setEnabled(False)
        self._app.PolygonAlpha(self.trans)

    def editmodeClick(self, value):
        self.polygon.setEnabled(value)
        self.rect.setEnabled(value)
        self.circle.setEnabled(value)
        self.line.setEnabled(value)
        self.arrow.setEnabled(value)
        self.trans.setEnabled(value)


    def eventFromMenu(self, mode):
        if mode == "polygon":
            self.polygon.setEnabled(False)
            self.rect.setEnabled(True)
            self.circle.setEnabled(True)
            self.line.setEnabled(True)
        elif mode == "rectangle":
            self.polygon.setEnabled(True)
            self.rect.setEnabled(False)
            self.circle.setEnabled(True)
            self.line.setEnabled(True)
        elif mode == "circle":
            self.polygon.setEnabled(True)
            self.rect.setEnabled(True)
            self.circle.setEnabled(False)
            self.line.setEnabled(True)
        elif mode == "line":
            self.polygon.setEnabled(True)
            self.rect.setEnabled(True)
            self.circle.setEnabled(True)
            self.line.setEnabled(False)
        else:
            self.polygon.setEnabled(True)
            self.rect.setEnabled(True)
            self.circle.setEnabled(True)
            self.line.setEnabled(True)
            self.arrow.setEnabled(True)

