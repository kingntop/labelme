import threading
import functools
from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtGui import QColor, QColorConstants
from qtpy.QtCore import Qt

from qtpy.QtWidgets import QLayout, QHBoxLayout, QVBoxLayout, \
    QLabel, QLineEdit, QToolButton, QScrollArea, QStyle, QListWidgetItem, QAction
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
                    if txt != self._app.selected_grade:
                        lbObj.setStyleSheet("QLabel { border: 0px solid #aaa; padding:2px}")
                    else:
                        lbObj.setStyleSheet("QLabel { background-color: rgb(204, 232, 255); border: 0; padding:2px}")

        if self._app.labelDialog:
            self._app.labelDialog.changeGradeDis(self._app.selected_grade)


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
        self.clrlabel.setFixedWidth(10)

        self.checkbox = QtWidgets.QCheckBox("")
        self.checkbox.setCheckState(Qt.Checked)  # Qt.Checked
        self.checkbox.stateChanged.connect(self.checkBoxStateChangeHandle)

        # self.row.addWidget(self.label)
        # self.row.addStretch()
        # self.row.addWidget(self.clrlabel)
        # self.row.addSpacing(6)
        # self.row.addWidget(self.checkbox)
        # self.row.addSpacing(33)

        self.row.addWidget(self.checkbox)
        self.row.addSpacing(10)
        self.row.addWidget(self.clrlabel)
        self.row.addSpacing(3)
        self.row.addWidget(self.label)
        self.row.addStretch()
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

            fnd = False
            for i in range(len(self._itemList)):
                itm = self._itemList[i]
                if isinstance(itm, MyCustomWidget):
                    if row._shape == itm._shape:
                        fnd = True
                        break

            if fnd is False:
                self._itemList.append(row)

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
        for i in range(len(self._itemList)):
            itm = self._itemList[i]
            if isinstance(itm, MyCustomWidget):
                if item._shape == itm._shape:
                    del self._itemList[i]
                    break



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

    def getListWidgetItems(self):
        s_items = []
        for i in range(self.count()):
            widgetitem = self.item(i)
            if isinstance(widgetitem, QListWidgetItem):
                s_items.append(widgetitem)
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

    def initUI_(self):
        shortcuts = self._app._config["shortcuts"]

        hbox_layout = QHBoxLayout()
        hbox_layout.setSpacing(0)
        hbox_layout.setContentsMargins(5, 5, 0, 0)

        self.polygon = QToolButton()
        self.polygon.setIcon(utils.newIcon("poly"))
        self.polygon.setIconSize(QtCore.QSize(20, 20))
        self.polygon.clicked.connect(self.polygonClick)
        self.polygon.setEnabled(False)
        #self.polygon.setFixedSize(150, 150)
        self.polygon.setShortcut(shortcuts['create_polygon'])


        self.rect = QToolButton()
        self.rect.setIcon(utils.newIcon("rect"))
        self.rect.setIconSize(QtCore.QSize(20, 20))
        self.rect.clicked.connect(self.rectClick)
        self.rect.setEnabled(False)
        self.rect.setShortcut(shortcuts['create_rectangle'])

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

    def initUI(self):
        shortcuts = self._app._config["shortcuts"]
        # top_create_polygon = action(
        #     self.tr("Create Polygons"),
        #     self.temp_top_create_rectangle,
        #     shortcuts["create_polygon"],
        #     icon="poly",
        #     tip=self.tr("Start drawing polygons"),
        # )

        hbox_layout = QHBoxLayout()
        hbox_layout.setSpacing(0)
        hbox_layout.setContentsMargins(5, 5, 0, 0)

        self.polygon = QToolButton()
        self.polygon.setIcon(utils.newIcon("poly"))
        self.polygon.setIconSize(QtCore.QSize(20, 20))
        self.polygon.clicked.connect(self.polygonClick)
        self.polygon.setEnabled(False)
        self.polygon.setToolTip("폴리곤 그리기" if self._app._config["local_lang"] == "ko_KR" else "Drawing ploygon")

        self.rect = QToolButton()
        self.rect.setIcon(utils.newIcon("rect"))
        self.rect.setIconSize(QtCore.QSize(20, 20))
        self.rect.clicked.connect(self.rectClick)
        self.rect.setEnabled(False)
        self.rect.setToolTip("사각형 그리기" if self._app._config["local_lang"] == "ko_KR" else "Drawing rectangle")

        self.circle = QToolButton()
        self.circle.setIcon(utils.newIcon("circle"))
        self.circle.setIconSize(QtCore.QSize(20, 20))
        self.circle.clicked.connect(self.circleClick)
        self.circle.setEnabled(False)
        self.circle.setToolTip("원 그리기" if self._app._config["local_lang"] == "ko_KR" else "Drawing circle")

        self.line = QToolButton()
        self.line.setIcon(utils.newIcon("line"))
        self.line.setIconSize(QtCore.QSize(20, 20))
        self.line.clicked.connect(self.lineClick)
        self.line.setEnabled(False)
        self.line.setToolTip("선 그리기" if self._app._config["local_lang"] == "ko_KR" else "Drawing line")

        self.arrow = QToolButton()
        self.arrow.setIcon(utils.newIcon("CursorArrow"))
        self.arrow.setIconSize(QtCore.QSize(20, 20))
        self.arrow.clicked.connect(self.arrowClick)
        self.arrow.setEnabled(False)
        self.arrow.setShortcut(shortcuts["cursorArrow"])
        self.arrow.setToolTip("그리기 해제" if self._app._config["local_lang"] == "ko_KR" else "Drawing off")

        self.trans = QToolButton()
        self.trans.setIcon(utils.newIcon("ftrans"))
        self.trans.setIconSize(QtCore.QSize(20, 20))
        self.trans.clicked.connect(self.transClick)
        self.trans.setEnabled(False)
        self.trans.setShortcut(shortcuts["trans"])
        self.trans.setToolTip("투명도 설정" if self._app._config["local_lang"] == "ko_KR" else "Transparency setting")
        
        self.editOrDraw = QLabel("")
        self.editOrDraw.setFont(appFont())
        #self.editOrDraw.setStyleSheet("QLabel { color : white;background-color: %s; font-size: 15px; font-weight: bold;padding:3px 7px;border-radius:3px}" % "#4472c4")  # 해제 #ed7d31
        ##self.editOrDraw.setFixedHeight(18)
        

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
        hbox_layout.addSpacing(40)
        hbox_layout.addWidget(self.editOrDraw, 0, QtCore.Qt.AlignLeft)

        hbox_layout.addStretch()

        self.setLayout(hbox_layout)

    def polygonClick(self, arg):
        self.polygon.setEnabled(False)
        self.rect.setEnabled(True)
        self.circle.setEnabled(True)
        self.line.setEnabled(True)
        self.appActionControll(False, createMode="polygon")

    def rectClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(False)
        self.circle.setEnabled(True)
        self.line.setEnabled(True)
        self.appActionControll(False, createMode="rectangle")

    def circleClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(True)
        self.circle.setEnabled(False)
        self.line.setEnabled(True)
        self.appActionControll(False, createMode="circle")

    def lineClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(True)
        self.circle.setEnabled(True)
        self.line.setEnabled(False)
        self.appActionControll(False, createMode="line")

    def arrowClick(self):
        # if self._app.canvas.current:
        #     self._app.canvas.current = None
        #     self._app.canvas.drawingPolygon.emit(False)
        #     self._app.canvas.update()
        self._app.toggleDrawMode(True)
        self._app.canvas.overrideCursor(QtCore.Qt.ArrowCursor)

    def transClick(self):
        self.trans.setEnabled(False)
        self._app.PolygonAlpha(self.trans)

    def editmodeClick(self, value):
        if self.isEnabled() is False:
            self.setEnabled(True)

        if self._app.canvas.editing() is True:
            self.editOrDraw.setText("해제 모드")
            self.editOrDraw.setStyleSheet("QLabel { color : white;background-color: %s; font-size: 15px; font-weight: bold;padding:3px 7px;border-radius:3px}" % "#ed7d31")  # 해제 #ed7d31

        self.polygon.setEnabled(value)
        self.rect.setEnabled(value)
        self.circle.setEnabled(value)
        self.line.setEnabled(value)
        self.arrow.setEnabled(value)
        self.trans.setEnabled(value)

    def appActionControll(self, edit=False, createMode="polygon"):
        self._app.canvas.setEditing(edit)
        self._app.canvas.createMode = createMode

        if self._app.canvas.editing() is False:
            self.editOrDraw.setText("그리기 모드")
            self.editOrDraw.setStyleSheet("QLabel { color : white;background-color: %s; font-size: 15px; font-weight: bold;padding:3px 7px;border-radius:3px}" % "#4472c4")  # 해제 #ed7d31

        if createMode == "polygon":
            self._app.actions.createMode.setEnabled(False)
            self._app.actions.createRectangleMode.setEnabled(True)
            self._app.actions.createCircleMode.setEnabled(True)
            self._app.actions.createLineMode.setEnabled(True)
            self._app.actions.createPointMode.setEnabled(True)
            # self.actions.createLineStripMode.setEnabled(True)
        elif createMode == "rectangle":
            self._app.actions.createMode.setEnabled(True)
            self._app.actions.createRectangleMode.setEnabled(False)
            self._app.actions.createCircleMode.setEnabled(True)
            self._app.actions.createLineMode.setEnabled(True)
            self._app.actions.createPointMode.setEnabled(True)
            # self.actions.createLineStripMode.setEnabled(True)
        elif createMode == "line":
            self._app.actions.createMode.setEnabled(True)
            self._app.actions.createRectangleMode.setEnabled(True)
            self._app.actions.createCircleMode.setEnabled(True)
            self._app.actions.createLineMode.setEnabled(False)
            self._app.actions.createPointMode.setEnabled(True)
            # self.actions.createLineStripMode.setEnabled(True)
        elif createMode == "circle":
            self._app.actions.createMode.setEnabled(True)
            self._app.actions.createRectangleMode.setEnabled(True)
            self._app.actions.createCircleMode.setEnabled(False)
            self._app.actions.createLineMode.setEnabled(True)
            self._app.actions.createPointMode.setEnabled(True)
            # self.actions.createLineStripMode.setEnabled(True)
        self._app.actions.editMode.setEnabled(not edit)


    def eventFromMenu(self, mode):
        if self.isEnabled() is False:
            self.setEnabled(True)

        if self._app.canvas.editing() is False:
            self.editOrDraw.setText("그리기 모드")
            self.editOrDraw.setStyleSheet("QLabel { color : white;background-color: %s; font-size: 15px; font-weight: bold;padding:3px 7px;border-radius:3px}" % "#4472c4")  # 해제 #ed7d31

        if mode == "polygon":
            self.polygon.setEnabled(False)
            self.rect.setEnabled(True)
            self.circle.setEnabled(True)
            self.line.setEnabled(True)
            if self.arrow.isEnabled() is False:
                self.arrow.setEnabled(True)
                self.trans.setEnabled(True)
        elif mode == "rectangle":
            self.polygon.setEnabled(True)
            self.rect.setEnabled(False)
            self.circle.setEnabled(True)
            self.line.setEnabled(True)
            if self.arrow.isEnabled() is False or self.trans.isEnabled() is False:
                self.arrow.setEnabled(True)
                self.trans.setEnabled(True)
        elif mode == "circle":
            self.polygon.setEnabled(True)
            self.rect.setEnabled(True)
            self.circle.setEnabled(False)
            self.line.setEnabled(True)
            if self.arrow.isEnabled() is False or self.trans.isEnabled() is False:
                self.arrow.setEnabled(True)
                self.trans.setEnabled(True)
        elif mode == "line":
            self.polygon.setEnabled(True)
            self.rect.setEnabled(True)
            self.circle.setEnabled(True)
            self.line.setEnabled(False)
            if self.arrow.isEnabled() is False or self.trans.isEnabled() is False:
                self.arrow.setEnabled(True)
                self.trans.setEnabled(True)
        else:
            self.polygon.setEnabled(True)
            self.rect.setEnabled(True)
            self.circle.setEnabled(True)
            self.line.setEnabled(True)
            if self.arrow.isEnabled() is False or self.trans.isEnabled() is False:
                self.arrow.setEnabled(True)
                self.trans.setEnabled(True)