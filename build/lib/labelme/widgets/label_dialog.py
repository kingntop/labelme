import re

from qtpy import QT_VERSION
from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy import QtGui
from qtpy import QtWidgets

from labelme.logger import logger
import labelme.utils
from labelme.shape import Shape
from labelme.utils import appFont

QT5 = QT_VERSION[0] == "5"


# TODO(unknown):
# - Calculate optimal position so as not to go out of screen area.


class LabelQLineEdit(QtWidgets.QLineEdit):
    def setListWidget(self, list_widget):
        self.list_widget = list_widget
    """
    def keyPressEvent(self, e):
        if e.key() in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]:
            self.list_widget.keyPressEvent(e)
        else:
            super(LabelQLineEdit, self).keyPressEvent(e)
    """

"""
class LabelDialog(QtWidgets.QDialog):
    def __init__(
        self,
        text="Enter object label",
        parent=None,
        labels=None,
        sort_labels=True,
        show_text_field=True,
        completion="startswith",
        fit_to_content=None,
        flags=None,
    ):
        if fit_to_content is None:
            fit_to_content = {"row": False, "column": True}
        self._fit_to_content = fit_to_content

        super(LabelDialog, self).__init__(parent)
        self.edit = LabelQLineEdit()
        self.edit.setPlaceholderText(text)
        self.edit.setValidator(labelme.utils.labelValidator())
        self.edit.editingFinished.connect(self.postProcess)
        if flags:
            self.edit.textChanged.connect(self.updateFlags)
        self.edit_group_id = QtWidgets.QLineEdit()
        self.edit_group_id.setPlaceholderText("Group ID")
        self.edit_group_id.setValidator(
            QtGui.QRegExpValidator(QtCore.QRegExp(r"\d*"), None)
        )
        layout = QtWidgets.QVBoxLayout()
        if show_text_field:
            layout_edit = QtWidgets.QHBoxLayout()
            layout_edit.addWidget(self.edit, 6)
            layout_edit.addWidget(self.edit_group_id, 2)
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
        self.labelList = QtWidgets.QListWidget()
        if self._fit_to_content["row"]:
            self.labelList.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
        if self._fit_to_content["column"]:
            self.labelList.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
        self._sort_labels = sort_labels
        if labels:
            self.labelList.addItems(labels)
        if self._sort_labels:
            self.labelList.sortItems()
        else:
            self.labelList.setDragDropMode(
                QtWidgets.QAbstractItemView.InternalMove
            )
        self.labelList.currentItemChanged.connect(self.labelSelected)
        self.labelList.itemDoubleClicked.connect(self.labelDoubleClicked)
        self.edit.setListWidget(self.labelList)
        layout.addWidget(self.labelList)
        # label_flags
        if flags is None:
            flags = {}
        self._flags = flags
        self.flagsLayout = QtWidgets.QVBoxLayout()
        self.resetFlags()
        layout.addItem(self.flagsLayout)
        self.edit.textChanged.connect(self.updateFlags)
        self.setLayout(layout)
        # completion
        completer = QtWidgets.QCompleter()
        if not QT5 and completion != "startswith":
            logger.warn(
                "completion other than 'startswith' is only "
                "supported with Qt5. Using 'startswith'"
            )
            completion = "startswith"
        if completion == "startswith":
            completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
            # Default settings.
            # completer.setFilterMode(QtCore.Qt.MatchStartsWith)
        elif completion == "contains":
            completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
            completer.setFilterMode(QtCore.Qt.MatchContains)
        else:
            raise ValueError("Unsupported completion: {}".format(completion))
        completer.setModel(self.labelList.model())
        self.edit.setCompleter(completer)

    def addLabelHistory(self, label):
        if self.labelList.findItems(label, QtCore.Qt.MatchExactly):
            return
        self.labelList.addItem(label)
        if self._sort_labels:
            self.labelList.sortItems()

    def labelSelected(self, item):
        self.edit.setText(item.text())

    def validate(self):
        text = self.edit.text()
        if hasattr(text, "strip"):
            text = text.strip()
        else:
            text = text.trimmed()
        if text:
            self.accept()

    def labelDoubleClicked(self, item):
        self.validate()

    def postProcess(self):
        text = self.edit.text()
        if hasattr(text, "strip"):
            text = text.strip()
        else:
            text = text.trimmed()
        self.edit.setText(text)

    def updateFlags(self, label_new):
        # keep state of shared flags
        flags_old = self.getFlags()

        flags_new = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label_new):
                for key in keys:
                    flags_new[key] = flags_old.get(key, False)
        self.setFlags(flags_new)

    def deleteFlags(self):
        for i in reversed(range(self.flagsLayout.count())):
            item = self.flagsLayout.itemAt(i).widget()
            self.flagsLayout.removeWidget(item)
            item.setParent(None)

    def resetFlags(self, label=""):
        flags = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label):
                for key in keys:
                    flags[key] = False
        self.setFlags(flags)

    def setFlags(self, flags):
        self.deleteFlags()
        for key in flags:
            item = QtWidgets.QCheckBox(key, self)
            item.setChecked(flags[key])
            self.flagsLayout.addWidget(item)
            item.show()

    def getFlags(self):
        flags = {}
        for i in range(self.flagsLayout.count()):
            item = self.flagsLayout.itemAt(i).widget()
            flags[item.text()] = item.isChecked()
        return flags

    def getGroupId(self):
        group_id = self.edit_group_id.text()
        if group_id:
            return int(group_id)
        return None

    def popUp(self, text=None, move=True, flags=None, group_id=None):
        if self._fit_to_content["row"]:
            self.labelList.setMinimumHeight(
                self.labelList.sizeHintForRow(0) * self.labelList.count() + 2
            )
        if self._fit_to_content["column"]:
            self.labelList.setMinimumWidth(
                self.labelList.sizeHintForColumn(0) + 2
            )
        # if text is None, the previous label in self.edit is kept
        if text is None:
            text = self.edit.text()
        if flags:
            self.setFlags(flags)
        else:
            self.resetFlags(text)
        self.edit.setText(text)
        self.edit.setSelection(0, len(text))
        if group_id is None:
            self.edit_group_id.clear()
        else:
            self.edit_group_id.setText(str(group_id))
        items = self.labelList.findItems(text, QtCore.Qt.MatchFixedString)
        if items:
            if len(items) != 1:
                logger.warning("Label list has duplicate '{}'".format(text))
            self.labelList.setCurrentItem(items[0])
            row = self.labelList.row(items[0])
            self.edit.completer().setCurrentRow(row)
        self.edit.setFocus(QtCore.Qt.PopupFocusReason)
        if move:
            self.move(QtGui.QCursor.pos())
        if self.exec_():
            return self.edit.text(), self.getFlags(), self.getGroupId()
        else:
            return None, None, None
"""

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
        horizontal_layout.setSpacing(1)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)

        label = QtWidgets.QLabel(self)
        txt = self._shape["label"]

        label.setText(txt)
        label.setFont(appFont())
        label.setStyleSheet("QLabel { padding: 2px; }")

        color_label = QtWidgets.QLabel(self)
        c_txt = self._shape["color"] if self._shape["color"] and self._shape["color"] != "" else "#808000"
        Qc = QtGui.QColor(c_txt)
        r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
        tmpcolor = QtGui.QColor(r, g, b)
        color_txt = tmpcolor.name(QtGui.QColor.HexRgb)
        #color_txt = self._shape["color"] if self._shape["color"] and self._shape["color"] != "" else "yellow"

        color_label.setText("")
        color_label.setStyleSheet("QLabel{border: 1px soild #aaa; background: %s;}" % color_txt)
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
        self.vContent_layout.setContentsMargins(0, 5, 0, 5)
        self.vContent_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

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
            if it._shape["label"] == shape.label:
                return True
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
        self._list_items = []
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.edit = LabelQLineEdit()

        self.setFont(appFont())
        self.edit.setPlaceholderText(text)
        self.edit.returnPressed.connect(self.searchProcess)
        layout = QtWidgets.QVBoxLayout()
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
        # self.labelList.itemSelectionChanged.connect(self.labelItemSelected)
        self.edit.setListWidget(self.labelList)
        layout.addWidget(self.labelList)

        self.setLayout(layout)

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

        if self.exec_():
            shape = self.labelList.getShapeSelectedItem()
            if shape:
                return shape
            else:
                return None
        else:
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
