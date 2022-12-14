import re
import threading
import copy

from qtpy import QT_VERSION
from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy.QtGui import QPalette
from qtpy.QtWidgets import QStyle

from labelme.logger import logger
import labelme.utils
from labelme.shape import Shape
from labelme.utils import appFont

QT5 = QT_VERSION[0] == "5"


# TODO(unknown):
# - Calculate optimal position so as not to go out of screen area.
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

        thefuckyourshitup_constant = 4
        margin = (option.rect.height() - options.fontMetrics.height()) // 2
        margin = margin - thefuckyourshitup_constant
        textRect.setTop(textRect.top() + margin)

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

class LabelQLineEdit(QtWidgets.QLineEdit):
    def setListWidget(self, list_widget):
        self.list_widget = list_widget


class DlgRowWidgetItem(QtWidgets.QWidget):
    _shape = {}
    _selected = False

    def __init__(self, shape, parent=None):
        super(DlgRowWidgetItem, self).__init__()
        if isinstance(shape, Shape):
            sp = {"grade": shape.grade, "label": shape.label, "label_display": shape.label_display, "color": shape.color}
        else:
            sp = {"grade": shape["grade"], "label": shape["label"], "label_display": shape["label_display"], "color": shape["color"]}

        self._shape = sp
        self._parent = parent

        horizontal_layout = QtWidgets.QHBoxLayout(self)
        horizontal_layout.setSpacing(0)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)

        label = QtWidgets.QLabel(self)
        txt = self._shape["label"]

        label.setText(txt)
        label.setFont(appFont())
        label.setStyleSheet("QLabel {padding-top:2px; padding-bottom: 2px}")

        color_label = QtWidgets.QLabel(self)
        c_txt = self._shape["color"] if self._shape["color"] and self._shape["color"] != "" else "#808000"
        Qc = QtGui.QColor(c_txt)
        r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
        tmpcolor = QtGui.QColor(r, g, b)
        color_txt = tmpcolor.name(QtGui.QColor.HexRgb)
        #color_txt = self._shape["color"] if self._shape["color"] and self._shape["color"] != "" else "yellow"

        color_label.setText("")
        color_label.setStyleSheet("QLabel {border: 1px soild #aaa; background: %s;}" % color_txt)
        color_label.setFixedWidth(8)

        #self.check_box = QtWidgets.QCheckBox(self)
        #self.check_box.stateChanged.connect(self.stateChangeHandle)

        horizontal_layout.addSpacing(6)
        horizontal_layout.addWidget(label, 0, QtCore.Qt.AlignLeft)
        horizontal_layout.addStretch()
        horizontal_layout.addWidget(color_label, 0, QtCore.Qt.AlignRight)
        horizontal_layout.addSpacing(15)
        self.setLayout(horizontal_layout)
        self.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0;}")
        self.setAutoFillBackground(True)

    def mousePressEvent(self, event):
        # print("row click")
        if self._parent is not None:
            self._parent.mousePressEventHandle(event, self._shape)

    def mouseDoubleClickEvent(self, event):
        if self._parent is not None:
            self._parent.mousePressEventHandle(event, self._shape, "duble")

    def changeBackground(self, state):
        if state is True:
            self.setStyleSheet("QWidget { background-color: rgb(204, 232, 255); border: 0;}")
        else:
            self.setStyleSheet("QWidget { background-color: rgb(255, 255, 255); border: 0;}")
        self.setAutoFillBackground(True)

    def checkitem(self, flag):
        if flag is True:
            self.check_box.setCheckState(Qt.Checked)
            self._selected = True
        else:
            self.check_box.setCheckState(Qt.Unchecked)
            self._selected = False

    def stateChangeHandle(self, state):
        if state == Qt.Checked:
            # self.signal.polygon_check_signal.emit(1)
            self._selected = True
        else:
            # self.signal.polygon_check_signal.emit(0)
            self._selected = False


class SearchLabelListWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super(SearchLabelListWidget, self).__init__()
        self._selected_item = None
        self._itemList = []
        self._parent = parent

        self.vContent_layout = QtWidgets.QVBoxLayout(self)
        self.vContent_layout.setContentsMargins(0, 1, 0, 1)
        self.vContent_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        #self.vContent_layout.addSpacing(2)

        # add here vContent_layout

        self.twidget = QtWidgets.QWidget(self)
        self.twidget.setLayout(self.vContent_layout)
        self.twidget.setStyleSheet("QWidget { background-color: rgb(255, 255, 255);}")

        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(self.twidget)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)

        hb_layout = QtWidgets.QHBoxLayout()
        hb_layout.addWidget(scroll)
        hb_layout.setContentsMargins(0, 0, 0, 0)
        hb_layout.setSpacing(0)
        self.setLayout(hb_layout)
        self.setMinimumWidth(300)
        self.setMinimumHeight(200)
        # self.setMaximumWidth(350)
        self.setMaximumHeight(250)

    def addItems(self, items):
        if len(items) < 1:
            return

        self.clear()
        for item in items:
            rowItem = DlgRowWidgetItem(item, self)
            self.vContent_layout.addWidget(rowItem)
            self._itemList.append(rowItem)
            w = rowItem.width()
            self.setMinimumWidth(w / 2 + 20)

    def addItem(self, item):
        if item:
            rowItem = DlgRowWidgetItem(item, self)
            self.vContent_layout.addWidget(rowItem)
            self._itemList.append(rowItem)
            w = rowItem.width()
            self.setMinimumWidth(w / 2 + 20)

    def findItems(self, shape):
        for it in self._itemList:
            #lb = it._shape["label"]
            try:
                if it._shape["label"] == shape.label:
                    return True
            except Exception as e:
                pass

        return False

    def mousePressEventHandle(self, event, shape, mode=None):
        # print("list row click")
        for rowItem in self._itemList:
            if rowItem._shape["label"] == shape["label"]:
                rowItem.changeBackground(True)
                rowItem._selected = True
                self._selected_item = rowItem
            else:
                rowItem.changeBackground(False)
                rowItem._selected = False

        self._parent.labelItemSelected(shape, mode)

    def getSelectedItem(self):
        if self._selected_item is not None:
            return self._selected_item
        return None

    def getShapeSelectedItem(self):
        if self._selected_item is not None:
            return self._selected_item._shape
        return None

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

    def clear(self):
        self._itemList.clear()
        self.clearLayout(self.vContent_layout)


class LabelSearchDialog(QtWidgets.QDialog):
    def __init__(
        self,
        text="",
        parent=None,
        show_text_field=True,
        fit_to_content=None,
    ):

        if fit_to_content is None:
            fit_to_content = {"row": False, "column": True}
        self._fit_to_content = fit_to_content
        super(LabelSearchDialog, self).__init__(parent)

        self._app = parent  # add ckd
        self.actived = False
        self._list_items = []
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFont(appFont())

        self.edit = LabelQLineEdit()
        self.edit.setFont(appFont())
        #font = self.edit.font()  # lineedit current font
        #font.setPointSize(11)  # change it's size
        #self.edit.setFont(font)  # set font
        self.edit.setPlaceholderText(text)
        self.edit.returnPressed.connect(self.searchProcess)
        #self.edit.setFixedHeight(25)
        self.edit.setStyleSheet("QLineEdit {padding: 2px;}")

        layout = QtWidgets.QVBoxLayout()
        layout_grade = QtWidgets.QHBoxLayout()
        layout.addLayout(layout_grade)
        static_grade = QtWidgets.QLabel("??????:" if self._app._config["local_lang"] == "ko_KR" else "Grade:")
        #static_grade.setStyleSheet("QLabel {font-size: 14px; font-weight: bold}")
        self.dis_grade = QtWidgets.QLabel("??????" if self._app._config["local_lang"] == "ko_KR" else "Grade")
        self.dis_grade.setStyleSheet("QLabel {color: red;font-size: 13px;}")
        #self.dis_grade.setStyleSheet("QLabel {color: red; font-size: 14px; font-weight: bold}")

        self.gradelist = QtWidgets.QComboBox()
        self.gradelist.setFixedHeight(22)
        self.gradelist.currentIndexChanged.connect(self.currentIndexChangedHandle)
        self.gradelist.setStyleSheet("QComboBox {border: 1px solid #aaa; border-radius: 1px; padding: 3px; font-size: 13px;}")
        self.gradelist.setItemDelegate(HTMLDelegate())
        self.gradelist.itemDelegate()
        #self.gradelist.setStyleSheet("QWidget {border: 1px solid #aaa; border-radius: 1px; padding: 3px; font-size: 14px;}")

        layout_grade.addWidget(static_grade)
        layout_grade.addWidget(self.dis_grade)
        layout_grade.addSpacing(20)
        layout_grade.addWidget(self.gradelist, 1)

        if show_text_field:
            layout_edit = QtWidgets.QHBoxLayout()
            layout_edit.addWidget(self.edit, 6)
            layout.addLayout(layout_edit)
        # buttons
        self.buttonBox = bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self,
        )
        bb.button(bb.Ok).setIcon(labelme.utils.newIcon("done"))
        bb.button(bb.Cancel).setIcon(labelme.utils.newIcon("undo"))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)

        layout.addWidget(bb)

        # label_list
        self.labelList = SearchLabelListWidget(self)
        ##self.labelList.itemSelectionChanged.connect(self.labelItemSelected)
        self.edit.setListWidget(self.labelList)
        layout.addWidget(self.labelList)

        self.setLayout(layout)

    def changeGradeDis(self, gradetxt, called=False):
        self.dis_grade.setText(gradetxt)
        cbidx = 0
        for i in range(0, self.gradelist.count()):
            itxt = self.gradelist.itemText(i)
            ml = self.dis_grade.text()
            if itxt == ml:
                cbidx = i
                break
        if self.gradelist.count() > 0:
            self.gradelist.setCurrentIndex(cbidx)

    def currentIndexChangedHandle(self, *args):
        sarg = args[0]
        if self.actived is False:
            return
        txt = self.gradelist.currentText()
        if len(txt) > 0 and txt != "--??????--":
            #self._app.selected_grade = txt
            self._app.grades_widget._selected_item = txt
            self._app.grades_widget._objtag = "grades"
            self._app.grades_widget.itemClickEventHandle()

    # ?????? ????????? ?????? ??????
    def addGrades(self, items):
        if len(items) > 0:
            self.gradelist.clear()
            item_count = len(items)
            self.gradelist.addItem("--??????--", "--??????--")
            for j in range(0, item_count):
                item = items[j]
                grade = item["grade"]
                self.gradelist.addItem(grade, grade)

    def labelItemSelected(self, shape, mode=None):
        #item = self.labelList.currentItem()
        if shape is None:
            return
        try:
            txt = shape["label"]
        except AttributeError:
            txt = ""

        if txt is not None and txt != "":
            self.edit.setText(txt)
        if mode is not None:
            self.validate()

    def validate(self):
        text = self.edit.text()
        text = self.deleteStrip(text)
        if text:
            self.accept()


    def searchProcess(self):
        text = self.edit.text()
        text = self.deleteStrip(text)
        temp = []
        if text == "":
            self.labelList.clear()
            for item in self._list_items:
                temp.append(item)

            if len(temp) > 0:
                self.labelList.addItems(temp)
        else:
            self.labelList.clear()
            for item in self._list_items:
                lbtxt = item["label"]
                lbtxt = self.deleteStrip(lbtxt)
                if lbtxt.find(text) > -1:
                    temp.append(item)
            if len(temp) > 0:
                self.labelList.addItems(temp)
        self.edit.setText("")


    def popUpLabelDlg(self, items, shape=None, mode=None):
        self._list_items.clear()
        self._list_items = items[:]
        #self._curSelectedText = ""
        self.labelList.clear()
        self.labelList.addItems(items)
        if mode and mode == "edit":
            if isinstance(shape, Shape):
                self.edit.setText(shape.label)
            else:
                self.edit.setText(shape["label"])
        self.actived = True

        if self.exec_():
            self.actived = False
            shape = self.labelList.getShapeSelectedItem()
            if shape:
                return shape
            else:
                return None
        else:
            self.actived = False
            return None

    def colorOfitem(self, txt):
        if len(self._list_items) < 1:
            return "#808000"
        txt = self.deleteStrip(txt)
        for pitem in self._list_items:
            lb = pitem["label"]
            dtxt = self.deleteStrip(lb)
            if txt == dtxt:
                return pitem["color"]


    def deleteStrip(self, txt):
        if txt is None or txt == "":
            return ""
        if hasattr(txt, "strip"):
            text = txt.strip()
        else:
            text = txt.trimmed()
        return text

    def addLabelHistory(self, shape):
        if self.labelList.findItems(shape):
            return

        self.labelList.addItem(shape)