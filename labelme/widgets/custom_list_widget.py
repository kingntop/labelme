import threading
import functools
from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtGui import QColor, QColorConstants
from qtpy.QtCore import Qt
from qtpy.QtGui import QPalette
from qtpy.QtWidgets import QStyle

from qtpy.QtWidgets import QLayout, QHBoxLayout, QVBoxLayout, \
    QLabel, QLineEdit, QToolButton, QScrollArea, QStyle, QListWidgetItem, QAction
from PyQt5.QtCore import pyqtSlot, QTimer
from .. import utils
from labelme.widgets.custom_qlabel import CQLabel
from labelme.widgets.signal import Signal
from labelme.shape import Shape
from labelme.utils import appFont
from labelme.utils.qt import LogPrint

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

class CustomLabelListWidgetItem(QtGui.QStandardItem):
    def __init__(self, text=None, shape=None):
        super(CustomLabelListWidgetItem, self).__init__()
        self.setText(text or "")
        self.setShape(shape)
        self.number = 0

        self.setCheckable(True)
        self.setCheckState(Qt.Checked)
        self.setEditable(False)
        self.setTextAlignment(Qt.AlignBottom)

    def clone(self):
        return CustomLabelListWidgetItem(self.shape())

    def setShape(self, shape):
        self.setData(shape, Qt.UserRole)

    def shape(self):
        return self.data(Qt.UserRole)

    def __hash__(self):
        return id(self)

    def getNumber(self):
        return self.number

    def setNumber(self, num):
        self.number = num

    def __repr__(self):
        return '{}("{}")'.format(self.__class__.__name__, self.text())

# polygon list
# https://stackoverflow.com/a/2039745/4158863
class StandardItemModel(QtGui.QStandardItemModel):

    itemDropped = QtCore.Signal()

    def removeRows(self, *args, **kwargs):
        ret = super().removeRows(*args, **kwargs)
        self.itemDropped.emit()
        return ret


class HTMLDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(HTMLDelegate, self).__init__()
        self.doc = QtGui.QTextDocument(self)

        font = appFont()
        font.setPixelSize(13)
        self.doc.setDefaultFont(font)

    def paint(self, painter, option, index):
        painter.save()

        options = QtWidgets.QStyleOptionViewItem(option)

        self.initStyleOption(options, index)
        self.doc.setHtml(options.text)
        options.text = ""

        style = (
            QtWidgets.QApplication.style()
            if options.widget is None
            else options.widget.style()
        )
        style.drawControl(QStyle.CE_ItemViewItem, options, painter)

        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()

        if option.state & QStyle.State_Selected:
            ctx.palette.setColor(
                QPalette.Text,
                option.palette.color(
                    QPalette.Active, QPalette.HighlightedText
                ),
            )
        else:
            ctx.palette.setColor(
                QPalette.Text,
                option.palette.color(QPalette.Active, QPalette.Text),
            )

        textRect = style.subElementRect(QStyle.SE_ItemViewItemText, options)

        if index.column() != 0:
            textRect.adjust(5, 0, 0, 0)
        '''
        thefuckyourshitup_constant = 4
        margin = (option.rect.height() - options.fontMetrics.height()) // 2
        margin = margin - thefuckyourshitup_constant
        textRect.setTop(textRect.top() - margin)
        '''
        textRect.setTop(textRect.top() - 1)

        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        self.doc.documentLayout().draw(painter, ctx)

        painter.restore()

    def sizeHint(self, option, index):
        thefuckyourshitup_constant = 4
        return QtCore.QSize(
            self.doc.idealWidth(),
            self.doc.size().height() - thefuckyourshitup_constant,
        )

class CustomLabelListWidget(QtWidgets.QListView):
    itemDoubleClicked = QtCore.Signal(CustomLabelListWidgetItem)
    itemSelectionChanged = QtCore.Signal(list, list)

    def __init__(self):
        super(CustomLabelListWidget, self).__init__()
        #self.signal = Signal()
        self._selectedItems = []

        self.setWindowFlags(Qt.Window)
        self.setModel(StandardItemModel())
        self.model().setItemPrototype(CustomLabelListWidgetItem())
        self.setItemDelegate(HTMLDelegate())
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)

        self.doubleClicked.connect(self.itemDoubleClickedEvent)

        self.selectionModel().selectionChanged.connect(
            self.itemSelectionChangedEvent
        )

    def __len__(self):
        return self.model().rowCount()

    def __getitem__(self, i):
        return self.model().item(i)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    @property
    def itemDropped(self):
        return self.model().itemDropped

    @property
    def itemChanged(self):
        return self.model().itemChanged

    def itemSelectionChangedEvent(self, selected, deselected):
        selected = [self.model().itemFromIndex(i) for i in selected.indexes()]
        deselected = [
            self.model().itemFromIndex(i) for i in deselected.indexes()
        ]
        self.itemSelectionChanged.emit(selected, deselected)

    def itemDoubleClickedEvent(self, index):
        self.itemDoubleClicked.emit(self.model().itemFromIndex(index))

    def selectedItems(self):
        return [self.model().itemFromIndex(i) for i in self.selectedIndexes()]

    def scrollToItem(self, item):
        self.scrollTo(self.model().indexFromItem(item))

    def addItem(self, item):
        if not isinstance(item, CustomLabelListWidgetItem):
            raise TypeError("item must be CustomLabelListWidgetItem")
        self.model().setItem(self.model().rowCount(), 0, item)
        item.setSizeHint(self.itemDelegate().sizeHint(None, None))

    def removeItem(self, item):
        index = self.model().indexFromItem(item)
        self.model().removeRows(index.row(), 1)

    def selectItem(self, item):
        index = self.model().indexFromItem(item)
        self.selectionModel().select(index, QtCore.QItemSelectionModel.Select)

    def findItemByShape(self, shape):
        for row in range(self.model().rowCount()):
            item = self.model().item(row, 0)
            if item.shape() == shape:
                return item
        raise ValueError("cannot find shape: {}".format(shape))

    def clear(self):
        self.model().clear()


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
        """
        self.line = QToolButton()
        self.line.setIcon(utils.newIcon("line"))
        self.line.setIconSize(QtCore.QSize(20, 20))
        self.line.clicked.connect(self.lineClick)
        self.line.setEnabled(False)
        self.line.setToolTip("선 그리기" if self._app._config["local_lang"] == "ko_KR" else "Drawing line")
        """
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
        self.editOrDraw.setText("해제 모드")
        self.editOrDraw.setStyleSheet(
            "QLabel { color : white;background-color: %s; font-size: 15px; font-weight: bold;padding:3px 7px;border-radius:3px}" % "#ed7d31")  # 해제 #ed7d31

        self.moveWeb = QToolButton()
        self.moveWeb.setFont(appFont())
        self.moveWeb.clicked.connect(self.moveWebClick)
        self.moveWeb.setText("웹 이동" if self._app._config["local_lang"] == "ko_KR" else "Move to web")
        self.moveWeb.setStyleSheet(
            "QToolButton { color : white;background-color: %s; font-size: 15px; font-weight: bold;padding:3px 7px;border-radius:3px; cursor: pointer;}" % "#6595ed")

        self.topbarHide = QToolButton()
        self.topbarHide.setFont(appFont())
        self.topbarHide.clicked.connect(self.topbarHideClick)
        self.topbarHide.setText("Top Bar 숨기기" if self._app._config["local_lang"] == "ko_KR" else "Hiden Top Bar")
        self.topbarHide.setStyleSheet(
            "QToolButton { color : white;background-color: %s; font-size: 15px; font-weight: bold;padding:3px 7px;border-radius:3px;  cursor: pointer;}" % "#4472c4")
        

        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.polygon, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.rect, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.circle, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        #hbox_layout.addWidget(self.line, 0, QtCore.Qt.AlignLeft)
        #hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.arrow, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.trans, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.editOrDraw, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.moveWeb, 0, QtCore.Qt.AlignLeft)
        hbox_layout.addSpacing(20)
        hbox_layout.addWidget(self.topbarHide, 0, QtCore.Qt.AlignLeft)

        hbox_layout.addStretch()

        self.setLayout(hbox_layout)

    def moveWebClick(self):
        self._app.tutorial()

    def polygonClick(self, arg):
        self.polygon.setEnabled(False)
        self.rect.setEnabled(True)
        self.circle.setEnabled(True)
        #self.line.setEnabled(True)
        self.appActionControll(False, createmode="polygon")

    def rectClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(False)
        self.circle.setEnabled(True)
        #self.line.setEnabled(True)
        self.appActionControll(False, createmode="rectangle")

    def circleClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(True)
        self.circle.setEnabled(False)
        #self.line.setEnabled(True)
        self.appActionControll(False, createmode="circle")

    def lineClick(self):
        self.polygon.setEnabled(True)
        self.rect.setEnabled(True)
        self.circle.setEnabled(True)
        #self.line.setEnabled(False)
        self.appActionControll(False, createmode="line")

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

    def topbarHideClick(self):
        if self.isEnabled() is False:
            self.setEnabled(True)
        self._app.topToolbar_dockAction()

    def editmodeClick(self, value):
        if self.isEnabled() is False:
            self.setEnabled(True)

        if self._app.canvas.editing() is True:
            self.editOrDraw.setText("해제 모드")
            self.editOrDraw.setStyleSheet("QLabel { color : white;background-color: %s; font-size: 15px; font-weight: bold;padding:3px 7px;border-radius:3px}" % "#ed7d31")  # 해제 #ed7d31

        self.polygon.setEnabled(value)
        self.rect.setEnabled(value)
        self.circle.setEnabled(value)
        #self.line.setEnabled(value)
        self.arrow.setEnabled(value)
        self.trans.setEnabled(value)

    def appActionControll(self, edit=False, createmode="polygon"):
        try:
            self._app.canvas.setEditing(edit)
            self._app.canvas.createMode = createmode

            if self._app.canvas.editing() is False:
                self.editOrDraw.setText("그리기 모드")
                self.editOrDraw.setStyleSheet("QLabel { color : white;background-color: %s; font-size: 15px; font-weight: bold;padding:3px 7px;border-radius:3px}" % "#4472c4")  # 해제 #ed7d31

            if createmode == "polygon":
                self._app.actions.createMode.setEnabled(False)
                self._app.actions.createRectangleMode.setEnabled(True)
                self._app.actions.createCircleMode.setEnabled(True)
                #self._app.actions.createLineMode.setEnabled(True)
                #self._app.actions.createPointMode.setEnabled(True)
                # self.actions.createLineStripMode.setEnabled(True)
            elif createmode == "rectangle":
                self._app.actions.createMode.setEnabled(True)
                self._app.actions.createRectangleMode.setEnabled(False)
                self._app.actions.createCircleMode.setEnabled(True)
                #self._app.actions.createLineMode.setEnabled(True)
                #self._app.actions.createPointMode.setEnabled(True)
                # self.actions.createLineStripMode.setEnabled(True)
            elif createmode == "line":
                self._app.actions.createMode.setEnabled(True)
                self._app.actions.createRectangleMode.setEnabled(True)
                self._app.actions.createCircleMode.setEnabled(True)
                #self._app.actions.createLineMode.setEnabled(False)
                #self._app.actions.createPointMode.setEnabled(True)
                # self.actions.createLineStripMode.setEnabled(True)
            elif createmode == "circle":
                self._app.actions.createMode.setEnabled(True)
                self._app.actions.createRectangleMode.setEnabled(True)
                self._app.actions.createCircleMode.setEnabled(False)
                #self._app.actions.createLineMode.setEnabled(True)
                #self._app.actions.createPointMode.setEnabled(True)
                # self.actions.createLineStripMode.setEnabled(True)
            self._app.actions.editMode.setEnabled(not edit)
        except Exception as e:
            LogPrint("Error in appActionControll %s" % e)
            pass


    def eventFromMenu(self, mode):
        try:
            if self.isEnabled() is False:
                self.setEnabled(True)

            if self._app.canvas.editing() is False:
                self.editOrDraw.setText("그리기 모드")
                self.editOrDraw.setStyleSheet("QLabel { color : white;background-color: %s; font-size: 15px; font-weight: bold;padding:3px 7px;border-radius:3px}" % "#4472c4")  # 해제 #ed7d31

            if mode == "polygon":
                self.polygon.setEnabled(False)
                self.rect.setEnabled(True)
                self.circle.setEnabled(True)
                #self.line.setEnabled(True)
                if self.arrow.isEnabled() is False:
                    self.arrow.setEnabled(True)
                    self.trans.setEnabled(True)
            elif mode == "rectangle":
                self.polygon.setEnabled(True)
                self.rect.setEnabled(False)
                self.circle.setEnabled(True)
                #self.line.setEnabled(True)
                if self.arrow.isEnabled() is False or self.trans.isEnabled() is False:
                    self.arrow.setEnabled(True)
                    self.trans.setEnabled(True)
            elif mode == "circle":
                self.polygon.setEnabled(True)
                self.rect.setEnabled(True)
                self.circle.setEnabled(False)
                #self.line.setEnabled(True)
                if self.arrow.isEnabled() is False or self.trans.isEnabled() is False:
                    self.arrow.setEnabled(True)
                    self.trans.setEnabled(True)
            elif mode == "line":
                self.polygon.setEnabled(True)
                self.rect.setEnabled(True)
                self.circle.setEnabled(True)
                #self.line.setEnabled(False)
                if self.arrow.isEnabled() is False or self.trans.isEnabled() is False:
                    self.arrow.setEnabled(True)
                    self.trans.setEnabled(True)
            else:
                self.polygon.setEnabled(True)
                self.rect.setEnabled(True)
                self.circle.setEnabled(True)
                #self.line.setEnabled(True)
                if self.arrow.isEnabled() is False or self.trans.isEnabled() is False:
                    self.arrow.setEnabled(True)
                    self.trans.setEnabled(True)
        except Exception as e:
            LogPrint("Error in eventFromMenu %s" % e)
            pass