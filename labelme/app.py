# -*- coding: utf-8 -*-

import functools
import html
import math
import os
import os.path as osp
import re
import webbrowser
import threading
import copy
import platform
import time
# import ctypes
import subprocess

import asyncio

from typing import final

import imgviz
import natsort
from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy.QtWidgets import QLabel, QListWidgetItem
from keyboard import press

# from win32api import GetSystemMetrics

from labelme import __appname__
from labelme import PY2

from . import utils
from labelme.config import get_config
from labelme.label_file import LabelFile
from labelme.label_file import LabelFileError
from labelme.logger import logger
from labelme.shape import Shape
from labelme.widgets import BrightnessContrastDialog
from labelme.widgets import PolygonTransDialog
from labelme.widgets import LoadingLabelProgress
from labelme.widgets import FileSaveDelayProgress
from labelme.widgets import AppVersionDialog
from labelme.widgets import Canvas
from labelme.widgets import FileDialogPreview
#from labelme.widgets import LabelDialog
from labelme.widgets import LabelSearchDialog
from labelme.widgets import LabelListWidget
from labelme.widgets import LabelListWidgetItem
from labelme.widgets import ToolBar
from labelme.widgets import UniqueLabelQListWidget
from labelme.widgets import ZoomWidget

from labelme.utils.qt import LogPrint
from labelme.utils.qt import httpReq
from labelme.widgets import DockInPutTitleBar
from labelme.widgets import DockCheckBoxTitleBar
from labelme.widgets import CustomListWidget
from labelme.widgets import CustomLabelListWidget
from labelme.widgets import CustomLabelListWidgetItem
from labelme.widgets import topToolWidget
from labelme.widgets.pwdDlg import PwdDlg
from labelme.widgets import labelme2coco
from labelme.utils import appFont
from labelme.convert_coco_label import ConvertCoCOLabel

# FIXME
# - [medium] Set max zoom value to something big enough for FitWidth/Window

# TODO(unknown):
# - Zoom is too "steppy".
LABEL_COLORMAP = imgviz.label_colormap()

# os.environ['HTTP_PROXY'] = "http://127.0.0.1:3213"
# os.environ['HTTPS_PROXY'] = "https://127.0.0.1:3213"

class MainWindow(QtWidgets.QMainWindow):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = 0, 1, 2
    selected_grade = None
    userInfo = {}
    isSaving = False
    forceExit = False
    showErrMessageBox = None
    saveTimer = None

    def __init__(
        self,
        config=None,
        filename=None,
        output=None,
        output_file=None,
        output_dir=None,
    ):

        if output is not None:
            logger.warning(
                "argument output is deprecated, use output_file instead"
            )
            if output_file is None:
                output_file = output

        # see labelme/config/default_config.yaml for valid configuration
        if config is None:
            config = get_config()
        self._config = config
        self._polyonList = [{
            "label_display": "미정-미정",
            "label": "미정",
            "grade": "미정",
            "color": "#ff0000"
        }]

        # set default shape colors
        Shape.line_color = QtGui.QColor(*self._config["shape"]["line_color"])
        Shape.fill_color = QtGui.QColor(*self._config["shape"]["fill_color"])
        Shape.select_line_color = QtGui.QColor(
            *self._config["shape"]["select_line_color"]
        )
        Shape.select_fill_color = QtGui.QColor(
            *self._config["shape"]["select_fill_color"]
        )
        Shape.vertex_fill_color = QtGui.QColor(
            *self._config["shape"]["vertex_fill_color"]
        )
        Shape.hvertex_fill_color = QtGui.QColor(
            *self._config["shape"]["hvertex_fill_color"]
        )

        # Set point size from config file
        Shape.point_size = self._config["shape"]["point_size"]

        super(MainWindow, self).__init__()

        self.setWindowTitle(__appname__)
        self.setFont(appFont())

        # Whether we need to save or not.
        self.dirty = False
        self._noSelectionSlot = False
        self._copied_shapes = None
        self._itemList = []

        # Main widgets and related state.
        self.labelDialog = LabelSearchDialog(
            text=self.tr("Enter Label for searching"),
            parent=self,
            show_text_field=self._config["show_label_text_field"],
            fit_to_content=self._config["fit_to_content"],
        )


        # grades part ckd
        self.selected_grade = None
        self.grades_dock = self.grades_widget = None
        self.grades_dock = QtWidgets.QDockWidget(self.tr("Grades"), self)

        self.grades_dock.setObjectName("grades")
        self.grade_title_bar = DockInPutTitleBar(self.grades_dock, "gradesbar", self)
        self.grades_dock.setTitleBarWidget(self.grade_title_bar)

        self.grades_widget = CustomListWidget(self, "grades")
        self.grades_dock.setWidget(self.grades_widget)
        #if self._config["grades"]:
        threading.Timer(0.3, self.gradeButtonEvent, args=(True,)).start()

        # products part ckd
        self.selected_product = None
        self.products_dock = self.products_widget = None
        self.products_dock = QtWidgets.QDockWidget(self.tr("Products"), self)

        self.products_dock.setObjectName("products")
        self.products_title_bar = DockInPutTitleBar(self.products_dock, "productsbar", self)
        self.products_dock.setTitleBarWidget(self.products_title_bar)

        self.products_widget = QtWidgets.QListWidget(self)
        self.products_widget.setSpacing(3)
        self.products_widget.setContentsMargins(3, 6, 3, 3)
        self.products_dock.setWidget(self.products_widget)
        self.products_widget.itemChanged.connect(self.setDirty)
        self.products_widget.itemSelectionChanged.connect(
            self.productsSelectionChanged
        )

        self.polygonSearch = QtWidgets.QLineEdit()
        self.polygonSearch.setPlaceholderText(self.tr("Search label name"))
        #self.polygonSearch.textChanged.connect(self.polygonSearchChanged)
        self.polygonSearch.returnPressed.connect(self.polygonReturnSearchChanged)

        self.labelList = CustomLabelListWidget()
        self.lastOpenDir = None
        self.labelList.itemSelectionChanged.connect(self.labelSelectionChanged)
        self.labelList.itemDoubleClicked.connect(self.editLabel)
        self.labelList.itemChanged.connect(self.labelItemChanged)
        self.labelList.itemDropped.connect(self.labelOrderChanged)

        polygonListLayout = QtWidgets.QVBoxLayout()
        polygonListLayout.setContentsMargins(0, 0, 0, 0)
        polygonListLayout.setSpacing(0)
        polygonListLayout.addWidget(self.polygonSearch)
        polygonListLayout.addWidget(self.labelList)

        self.shape_dock = QtWidgets.QDockWidget(
            self.tr("Polygon Labels"), self

        )
        self.shape_dock.setObjectName("Labels")
        self.customLabelTitleBar = DockCheckBoxTitleBar(self, self.shape_dock)
        self.shape_dock.setTitleBarWidget(self.customLabelTitleBar)
        polygonListWidget = QtWidgets.QWidget()
        polygonListWidget.setLayout(polygonListLayout)
        self.shape_dock.setWidget(polygonListWidget)

        # top Tool area
        self.topToolWidget = topToolWidget("toptool", self)
        self.topToolbar_dock = QtWidgets.QDockWidget(self.tr("Top bar"), self)
        self.topToolbar_dock.setWidget(self.topToolWidget)
        self.topToolbar_dock.setTitleBarWidget(QtWidgets.QWidget())
        self.topToolWidget.setEnabled(True)


        self.fileSearch = QtWidgets.QLineEdit()
        self.fileSearch.setPlaceholderText(self.tr("Search File name"))
        self.fileSearch.textChanged.connect(self.fileSearchChanged)
        self.fileListWidget = QtWidgets.QListWidget()
        self.fileListWidget.itemSelectionChanged.connect(
            self.fileSelectionChanged
        )
        fileListLayout = QtWidgets.QVBoxLayout()
        fileListLayout.setContentsMargins(0, 0, 0, 0)
        fileListLayout.setSpacing(0)
        fileListLayout.addWidget(self.fileSearch)
        fileListLayout.addWidget(self.fileListWidget)

        fdname = "File List (Total 0)" if self._config["local_lang"] != "ko_KR" else "파일 목록 (총 0)"
        self.file_dock = QtWidgets.QDockWidget(fdname, self)
        self.file_dock.setObjectName("Files")
        fileListWidget = QtWidgets.QWidget()
        fileListWidget.setLayout(fileListLayout)
        self.file_dock.setWidget(fileListWidget)

        self.zoomWidget = ZoomWidget()
        self.setAcceptDrops(True)

        self.canvas = self.labelList.canvas = Canvas(
            epsilon=self._config["epsilon"],
            double_click=self._config["canvas"]["double_click"],
            num_backups=self._config["canvas"]["num_backups"],
            lang=self._config["local_lang"],
        )
        self.canvas.zoomRequest.connect(self.zoomRequest)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidget(self.canvas)
        scrollArea.setWidgetResizable(True)
        self.scrollBars = {
            Qt.Vertical: scrollArea.verticalScrollBar(),
            Qt.Horizontal: scrollArea.horizontalScrollBar(),
        }
        self.canvas.scrollRequest.connect(self.scrollRequest)

        self.canvas.newShape.connect(self.newShape)
        self.canvas.shapeMoved.connect(self.setDirty)
        self.canvas.selectionChanged.connect(self.shapeSelectionChanged)
        self.canvas.drawingPolygon.connect(self.toggleDrawingSensitive)

        self.setCentralWidget(scrollArea)


        features = QtWidgets.QDockWidget.DockWidgetFeatures()
        for dock in ["grades_dock", "products_dock", "shape_dock", "file_dock"]:
            if self._config[dock]["closable"]:
                features = features | QtWidgets.QDockWidget.DockWidgetClosable
            if self._config[dock]["floatable"]:
                features = features | QtWidgets.QDockWidget.DockWidgetFloatable
            if self._config[dock]["movable"]:
                features = features | QtWidgets.QDockWidget.DockWidgetMovable

            getattr(self, dock).setFeatures(features)

            if self._config[dock]["show"] is False:
                getattr(self, dock).setVisible(False)


        self._pwdDlg = PwdDlg(self._config, self)


        self.addDockWidget(Qt.TopDockWidgetArea, self.topToolbar_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.grades_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.products_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.shape_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.file_dock)

        # Actions
        action = functools.partial(utils.newAction, self)
        shortcuts = self._config["shortcuts"]
        quit = action(
            self.tr("&Quit"),
            self.close,
            shortcuts["quit"],
            "quit",
            self.tr("Quit application"),
        )
        open_ = action(
            self.tr("&Open"),
            self.openFile,
            shortcuts["open"],
            "open",
            self.tr("Open image or label file"),
        )
        opendir = action(
            self.tr("&Open Dir"),
            self.openDirDialog,
            shortcuts["open_dir"],
            "open",
            self.tr("Open Dir"),
        )
        openNextImg = action(
            self.tr("&Next Image"),
            self.openNextImg,
            shortcuts["open_next"],
            "next",
            self.tr("Open next (hold Ctl+Shift to copy labels)"),
            enabled=False,
        )
        openPrevImg = action(
            self.tr("&Prev Image"),
            self.openPrevImg,
            shortcuts["open_prev"],
            "prev",
            self.tr("Open prev (hold Ctl+Shift to copy labels)"),
            enabled=False,
        )
        save = action(
            self.tr("&Save"),
            self.saveFile,
            shortcuts["save"],
            "save",
            self.tr("Save labels to file"),
            enabled=False,
        )
        # add 9.28.2022
        # saveAs = action(
        #     self.tr("&Save As"),
        #     self.saveFileAs,
        #     shortcuts["save_as"],
        #     "save-as",
        #     self.tr("Save labels to a different file"),
        #     enabled=False,
        # )

        deleteFile = action(
            self.tr("&Delete File"),
            self.deleteFile,
            shortcuts["delete_file"],
            "delete",
            self.tr("Delete current label file"),
            enabled=False,
        )

        # add 9.28.2022
        # changeOutputDir = action(
        #     self.tr("&Change Output Dir"),
        #     slot=self.changeOutputDirDialog,
        #     shortcut=shortcuts["save_to"],
        #     icon="open",
        #     tip=self.tr("Change where annotations are loaded/saved"),
        # )

        saveAuto = action(
            text=self.tr("Save &Automatically") if self._config["auto_save"] is False else self.tr("Turn off Save automatically"),
            slot=lambda x: self.actions.saveAuto.setChecked(x),  #   slot=self.saveAutoAction,
            shortcut=shortcuts["saveAuto"],
            icon="save",
            tip=self.tr("Save &Automatically") if self._config["auto_save"] is False else self.tr("Turn off Save automatically"),
            checkable=True,
            enabled=True,
        )
        saveAuto.setChecked(self._config["auto_save"])

        # saveWithImageData = action(
        #     text=self.tr("Save With Image Data"),
        #     slot=self.enableSaveImageWithData,
        #     tip=self.tr("Save image data in label file"),
        #     checkable=True,
        #     checked=self._config["store_data"],
        # )  add 9.28.2022

        close = action(
            "&Close",
            self.closeFile,
            shortcuts["close"],
            "close",
            "Close current file",
        )

        # toggle_keep_prev_mode = action(
        #     self.tr("Keep Previous Annotation"),
        #     self.toggleKeepPrevMode,
        #     shortcuts["toggle_keep_prev_mode"],
        #     None,
        #     self.tr('Toggle "keep pevious annotation" mode'),
        #     checkable=True,
        # )
        # toggle_keep_prev_mode.setChecked(self._config["keep_prev"])

        createMode = action(
            self.tr("Create Polygons"),
            lambda: self.toggleDrawMode(False, createmode="polygon"),
            shortcuts["create_polygon"],
            "objects",
            self.tr("Start drawing polygons"),
            enabled=False,
        )
        createRectangleMode = action(
            self.tr("Create Rectangle"),
            lambda: self.toggleDrawMode(False, createmode="rectangle"),
            shortcuts["create_rectangle"],
            "objects",
            self.tr("Start drawing rectangles"),
            enabled=False,
        )
        createCircleMode = action(
            self.tr("Create Circle"),
            lambda: self.toggleDrawMode(False, createmode="circle"),
            shortcuts["create_circle"],
            "objects",
            self.tr("Start drawing circles"),
            enabled=False,
        )
        """
        createLineMode = action(
            self.tr("Create Line"),
            lambda: self.toggleDrawMode(False, createmode="line"),
            shortcuts["create_line"],
            "objects",
            self.tr("Start drawing lines"),
            enabled=False,
        )
        createPointMode = action(
            self.tr("Create Point"),
            lambda: self.toggleDrawMode(False, createmode="point"),
            shortcuts["create_point"],
            "objects",
            self.tr("Start drawing points"),
            enabled=False,
        )
        """
        # createLineStripMode = action(
        #     self.tr("Create LineStrip"),
        #     lambda: self.toggleDrawMode(False, createmode="linestrip"),
        #     shortcuts["create_linestrip"],
        #     "objects",
        #     self.tr("Start drawing linestrip. Ctrl+LeftClick ends creation."),
        #     enabled=False,
        # )
        editMode = action(
            self.tr("Edit Polygons"),
            self.setEditMode,
            shortcuts["edit_polygon"],
            "edit",
            self.tr("Move and edit the selected polygons"),
            enabled=False,
        )

        delete = action(
            self.tr("Delete Polygons"),
            self.deleteSelectedShape,
            shortcuts["delete_polygon"],
            "cancel",
            self.tr("Delete the selected polygons"),
            enabled=False,
        )
        duplicate = action(
            self.tr("Duplicate Polygons"),
            self.duplicateSelectedShape,
            shortcuts["duplicate_polygon"],
            "copy",
            self.tr("Create a duplicate of the selected polygons"),
            enabled=False,
        )
        copy = action(
            self.tr("Copy Polygons"),
            self.copySelectedShape,
            shortcuts["copy_polygon"],
            "copy_clipboard",
            self.tr("Copy selected polygons to clipboard"),
            enabled=False,
        )
        paste = action(
            self.tr("Paste Polygons"),
            self.pasteSelectedShape,
            shortcuts["paste_polygon"],
            "paste",
            self.tr("Paste copied polygons"),
            enabled=False,
        )
        undoLastPoint = action(
            self.tr("Undo last point"),
            self.canvas.undoLastPoint,
            shortcuts["undo_last_point"],
            "undo",
            self.tr("Undo last drawn point"),
            enabled=False,
        )
        removePoint = action(
            text="Remove Selected Point" if self._config['local_lang'] != 'ko_KR' else '선택한 점 삭제',
            slot=self.removeSelectedPoint,
            shortcut=shortcuts["remove_selected_point"],
            icon="edit",
            tip="Remove selected point from polygon" if self._config['local_lang'] != 'ko_KR' else '폴리곤으로 부터 선택한 점을 삭제한다',
            enabled=False,
        )

        undo = action(
            self.tr("Undo"),
            self.undoShapeEdit,
            shortcuts["undo"],
            "undo",
            self.tr("Undo last add and edit of shape"),
            enabled=False,
        )

        hideAll = action(
            self.tr("&Hide\nPolygons"),
            functools.partial(self.togglePolygons, False),
            shortcuts["hideAll"],
            icon="eye",
            tip=self.tr("Hide all polygons"),
            enabled=False,
        )
        showAll = action(
            self.tr("&Show\nPolygons"),
            functools.partial(self.togglePolygons, True),
            shortcuts["showAll"],
            icon="eye",
            tip=self.tr("Show all polygons"),
            enabled=False,
        )

        tutorial = action(
            self.tr("&Help"),
            self.tutorial,
            shortcuts["tutorial"],
            icon="help",
            tip=self.tr("Show Help page"),
        )
        changepwd = action(
            self.tr("&Change Password"),
            self.changePasswordAction,
            shortcuts["changepwd"],
            icon="chg_pwd",
            tip=self.tr("To change self password")
        )
        appVersion = action(
            "버전정보" if self._config['local_lang'] == 'ko_KR' else 'Version',
            self.viewAppVersion,
            icon="icon"
        )


        zoom = QtWidgets.QWidgetAction(self)
        zoom.setDefaultWidget(self.zoomWidget)
        self.zoomWidget.setWhatsThis(
            str(
                self.tr(
                    "Zoom in or out of the image. Also accessible with "
                    "{} and {} from the canvas."
                )
            ).format(
                utils.fmtShortcut(
                    "{},{}".format(shortcuts["zoom_in"], shortcuts["zoom_out"])
                ),
                utils.fmtShortcut(self.tr("Ctrl+Wheel")),
            )
        )
        self.zoomWidget.setEnabled(False)

        zoomIn = action(
            self.tr("Zoom &In"),
            functools.partial(self.addZoom, 1.1),
            shortcuts["zoom_in"],
            "zoom-in",
            self.tr("Increase zoom level"),
            enabled=False,
        )
        zoomOut = action(
            self.tr("&Zoom Out"),
            functools.partial(self.addZoom, 0.9),
            shortcuts["zoom_out"],
            "zoom-out",
            self.tr("Decrease zoom level"),
            enabled=False,
        )
        zoomOrg = action(
            self.tr("&Original size"),
            functools.partial(self.setZoom, 100),
            shortcuts["zoom_to_original"],
            "zoom",
            self.tr("Zoom to original size"),
            enabled=False,
        )
        # keepPrevScale = action(
        #     self.tr("&Keep Previous Scale"),
        #     self.enableKeepPrevScale,
        #     tip=self.tr("Keep previous zoom scale"),
        #     checkable=True,
        #     checked=self._config["keep_prev_scale"],
        #     enabled=True,
        # )
        fitWindow = action(
            self.tr("&Fit Window"),
            self.setFitWindow,
            shortcuts["fit_window"],
            "fit-window",
            self.tr("Zoom follows window size"),
            checkable=True,
            enabled=False,
        )
        fitWidth = action(
            self.tr("&Fit Width"),
            self.setFitWidth,
            shortcuts["fit_width"],
            "fit-width",
            self.tr("Zoom follows window width"),
            checkable=True,
            enabled=False,
        )
        brightnessContrast = action(
            self.tr("&Brightness\nContrast"),
            self.brightnessContrast,
            shortcuts["brightness_contrast"],
            "color",
            self.tr("Adjust brightness and contrast"),
            enabled=False,
        )
        # Group zoom controls into a list for easier toggling.
        zoomActions = (
            self.zoomWidget,
            zoomIn,
            zoomOut,
            zoomOrg,
            fitWindow,
            fitWidth,
        )
        self.zoomMode = self.FIT_WINDOW
        fitWindow.setChecked(Qt.Checked)
        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow,
            self.FIT_WIDTH: self.scaleFitWidth,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

        edit = action(
            self.tr("&Edit Label"),
            self.editLabel,
            shortcuts["edit_label"],
            "edit",
            self.tr("Modify the label of the selected polygon"),
            enabled=False,
        )

        # fill_drawing = action(
        #     self.tr("Fill Drawing Polygon"),
        #     self.canvas.setFillDrawing,
        #     None,
        #     "color",
        #     self.tr("Fill polygon while drawing"),
        #     checkable=True,
        #     enabled=True,
        # )
        # fill_drawing.trigger()

        # Label list context menu.
        labelMenu = QtWidgets.QMenu()
        utils.addActions(labelMenu, (edit, delete))
        utils.addActions(labelMenu, (delete, ))
        self.labelList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.labelList.customContextMenuRequested.connect(
            self.popLabelListMenu
        )

        # Store actions for further handling.
        self.actions = utils.struct(
            saveAuto=saveAuto,
            # saveWithImageData=saveWithImageData,
            # changeOutputDir=changeOutputDir,
            save=save,
            #saveAs=saveAs,
            open=open_,
            close=close,
            deleteFile=deleteFile,
            #toggleKeepPrevMode=toggle_keep_prev_mode,
            delete=delete,
            edit=edit,
            duplicate=duplicate,
            copy=copy,
            paste=paste,
            undoLastPoint=undoLastPoint,
            undo=undo,
            removePoint=removePoint,
            createMode=createMode,
            editMode=editMode,
            createRectangleMode=createRectangleMode,
            createCircleMode=createCircleMode,
            #createLineMode=createLineMode,
            #createPointMode=createPointMode,
            #createLineStripMode=createLineStripMode,

            zoom=zoom,
            zoomIn=zoomIn,
            zoomOut=zoomOut,
            zoomOrg=zoomOrg,
            #keepPrevScale=keepPrevScale,
            fitWindow=fitWindow,
            fitWidth=fitWidth,
            brightnessContrast=brightnessContrast,
            zoomActions=zoomActions,
            openNextImg=openNextImg,
            openPrevImg=openPrevImg,
            #fileMenuActions=(open_, opendir, save, saveAs, close, quit),
            fileMenuActions=(open_, opendir, save, close, quit),
            tool=(),
            # XXX: need to add some actions here to activate the shortcut
            editMenu=(
                edit,
                duplicate,
                delete,
                None,
                undo,
                undoLastPoint,
                # None,
                removePoint,
                # None,
                # toggle_keep_prev_mode,
            ),
            # menu shown at right click
            menu=(
                createMode,
                createRectangleMode,
                createCircleMode,
                #createLineMode,
                #createPointMode,
                #createLineStripMode,
                editMode,
                edit,
                duplicate,
                copy,
                paste,
                delete,
                undo,
                undoLastPoint,
                removePoint,
            ),
            onLoadActive=(
                close,
                createMode,
                createRectangleMode,
                createCircleMode,
                #createLineMode,
                #createPointMode,
                #createLineStripMode,
                editMode,
                brightnessContrast,
            ),
            #onShapesPresent=(saveAs, hideAll, showAll),
            onShapesPresent=(hideAll, showAll),
        )

        self.canvas.vertexSelected.connect(self.actions.removePoint.setEnabled)

        self.menus = utils.struct(
            file=self.menu(self.tr("&File")),
            edit=self.menu(self.tr("&Edit")),
            view=self.menu(self.tr("&View")),
            help=self.menu(self.tr("&Help")),
            recentFiles=QtWidgets.QMenu(self.tr("Open &Recent")),
            labelList=labelMenu,
        )

        utils.addActions(
            self.menus.file,
            (
                open_,
                openNextImg,
                openPrevImg,
                opendir,
                self.menus.recentFiles,
                save,
                #saveAs,
                saveAuto,
                #changeOutputDir,
                #saveWithImageData,
                close,
                deleteFile,
                None,
                quit,
            ),
        )
        utils.addActions(self.menus.help, (tutorial, None, changepwd, None, appVersion))

        self.tools = self.toolbar("Tools")
        utils.addActions(
            self.menus.view,
            (
                # fill_drawing,
                # None,
                hideAll,
                showAll,
                None,
                self.tools.toggleViewAction(),
                self.topToolbar_dock.toggleViewAction(),
                self.grades_dock.toggleViewAction(),
                self.products_dock.toggleViewAction(),
                self.shape_dock.toggleViewAction(),
                self.file_dock.toggleViewAction(),
                None,
                zoomIn,
                zoomOut,
                zoomOrg,
                #keepPrevScale,
                None,
                fitWindow,
                fitWidth,
                None,
                brightnessContrast,
            ),
        )

        self.menus.file.aboutToShow.connect(self.updateFileMenu)

        # Custom context menu for the canvas widget:
        utils.addActions(self.canvas.menus[0], self.actions.menu)
        utils.addActions(
            self.canvas.menus[1],
            (
                action("&Copy here" if self._config["local_lang"] != "ko_KR" else "여기에 복사", self.copyShape),
                action("&Move here" if self._config["local_lang"] != "ko_KR" else "여기로 이동", self.moveShape),
            ),
        )

        # Menu buttons on Left
        self.actions.tool = (
            open_,
            opendir,
            openNextImg,
            openPrevImg,
            save,
            deleteFile,
            None,
            createMode,
            editMode,
            hideAll,
            showAll,
            duplicate,
            # copy,
            # paste,
            delete,
            undo,
            brightnessContrast,
            None,
            zoom,
            fitWidth,
        )

        # Menu buttons on Left
        self.statusBar().showMessage(str(self.tr("%s started.")) % __appname__)
        self.statusBar().setFont(appFont())
        self.statusBar().show()

        if output_file is not None and self._config["auto_save"]:
            logger.warn(
                "If `auto_save` argument is True, `output_file` argument "
                "is ignored and output filename is automatically "
                "set as IMAGE_BASENAME.json."
            )
        self.output_file = output_file
        self.output_dir = output_dir

        # Application state.
        self.image = QtGui.QImage()
        self.imagePath = None
        self.recentFiles = []
        self.maxRecent = 7
        self.otherData = None
        self.zoom_level = 100
        self.fit_window = False
        self.zoom_values = {}  # key=filename, value=(zoom_mode, zoom_value)
        self.brightnessContrast_values = {}
        self.polygonTrans_deta_value = 128
        self.polygonTrans_value = 0
        self.lineweight_value = 2.0
        self.scroll_values = {
            Qt.Horizontal: {},
            Qt.Vertical: {},
        }  # key=filename, value=scroll_value

        if filename is not None and osp.isdir(filename):
            self.importDirImages(filename, load=False)
        else:
            self.filename = filename

        if self._config["file_search"]:
            self.fileSearch.setText(self._config["file_search"])
            self.fileSearchChanged()

        # XXX: Could be completely declarative.
        # Restore application settings.
        self.settings = QtCore.QSettings("labelme", "labelme")
        self.recentFiles = self.settings.value("recentFiles", []) or []

        size = self.settings.value("window/size", QtCore.QSize(600, 500))
        # user32 = ctypes.windll.user32
        # size = self.settings.value("window/size", QtCore.QSize(user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)))

        position = self.settings.value("window/position", QtCore.QPoint(0, 0))
        state = self.settings.value("window/state", QtCore.QByteArray())
        self.resize(size)
        self.showMaximized()
        self.move(position)
        # or simply:
        # self.restoreGeometry(settings['window/geometry']
        self.restoreState(state)

        # Populate the File menu dynamically.
        self.updateFileMenu()
        # Since loading the file may take some time,
        # make sure it runs in the background.
        if self.filename is not None:
            self.queueEvent(functools.partial(self.loadFile, self.filename))

        # Callbacks:
        self.zoomWidget.valueChanged.connect(self.paintCanvas)
        self.populateModeActions()
        # self.addRecentFilesToList("first")  # add ckd

    # self.firstStart = True
    # if self.firstStart:
    #    QWhatsThis.enterWhatsThisMode()

        threading.Timer(0.1, self.connetNetDriver).start()

    def connetNetDriver(self):
        self._config['net_dirve'] = ''
        if self._config["net"] != "":
            cmd = ''
            try:
                #nd = r'net use d:\\Temp /user:{} {}'.format(self._config['user_id'], 'demo1234!')
                dstr = re.findall(r'(\w+):', self._config["net"])
                dstr = dstr[0]
                dstr = str(dstr).strip()
                self._config['net_dirve'] = dstr
                cmd = r'{}'.format(self._config['net'])  # net use z: \\data /user:user123 password
                subproc = subprocess.run(cmd, shell=True)
                # arg = self.subprocess.args
                #print(subproc)
            except subprocess.CalledProcessError as e:
                LogPrint("Net 드라이브에 접속중 : %s" % e)
            except Exception as e:
                LogPrint("Net 드라이브에 접속중 : %s" % e)
            finally:
                LogPrint("컴맨드 (%s) 실행되였습니다." % cmd)

    def deConnetNetDriver(self):
        if self._config["net"] != "" and self._config["net_dirve"] != "":
            cmd = ''
            try:
                # nd = r'net use d:\\Temp /user:{} {}'.format(self._config['user_id'], 'demo1234!')
                # net use z: /delete /yes
                cmd = r'net use {}: /delete /yes'.format(self._config['net_dirve'])
                subproc = subprocess.run(cmd, shell=True)
                #print(subproc)
            except subprocess.CalledProcessError as e:
                LogPrint("Net 드라이브 해체중 : %s" % e)
            except Exception as e:
                LogPrint("Net 드라이브 해체중 : %s" % e)
            finally:
                LogPrint("컴맨드 (%s) 실행되였습니다." % cmd)

    # add recent files
    def addRecentFilesToList(self):
        self.fileListWidget.clear()
        for fname in self.recentFiles:
            extensions = [
                ".%s" % fmt.data().decode().lower()
                for fmt in QtGui.QImageReader.supportedImageFormats()
            ]
            if fname.lower().endswith(tuple(extensions)):
                label_file = osp.splitext(fname)[0] + ".json"
                if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(label_file):
                    item = QtWidgets.QListWidgetItem(fname)
                    self.fileListWidget.addItem(item)
                    # print(fname)
            # print("first recent file : ", fname)



    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        menu.setFont(appFont())
        if actions:
            utils.addActions(menu, actions)
        return menu

    def toolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setFont(appFont())
        toolbar.setObjectName("%sToolBar" % title)
        # toolbar.setOrientation(Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if actions:
            utils.addActions(toolbar, actions)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        return toolbar

    # add ckd
    def toptoolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setObjectName("%sToolBar" % title)
        try:
            # toolbar.setOrientation(Qt.Vertical)
            toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
            if actions:
                utils.addActions(toolbar, actions)
            #self.addToolBar(Qt.TopToolBarArea, toolbar)
        except Exception as e:
            LogPrint("Top 틀바액션중 : %s" % e)
        return toolbar

    # Support Functions

    def noShapes(self):
        return not len(self.labelList)

    def populateModeActions(self):
        tool, menu = self.actions.tool, self.actions.menu
        self.tools.clear()
        if isinstance(tool[7], QtWidgets.QAction):
            ac_txt = tool[7].iconText()
            ac_txt = ac_txt + "(1)"
            tool[7].setIconText(ac_txt)


        utils.addActions(self.tools, tool)
        self.canvas.menus[0].clear()
        utils.addActions(self.canvas.menus[0], menu)
        self.menus.edit.clear()
        actions = (
            self.actions.createMode,
            self.actions.createRectangleMode,
            self.actions.createCircleMode,
            #self.actions.createLineMode,
            #self.actions.createPointMode,
            #self.actions.createLineStripMode,
            self.actions.editMode,
        )
        utils.addActions(self.menus.edit, actions + self.actions.editMenu)


    def setvisibilityChange(self):
        print("setvisibilityChange")

    def topToolbar_dockAction(self):
        self.topToolbar_dock.hide()

    def setDirty(self):
        # Even if we autosave the file, we keep the ability to undo
        self.actions.undo.setEnabled(self.canvas.isShapeRestorable)

        if self._config["auto_save"] or self.actions.saveAuto.isChecked():
            label_file = osp.splitext(self.imagePath)[0] + ".json"
            if self.output_dir:
                label_file_without_path = osp.basename(label_file)
                label_file = osp.join(self.output_dir, label_file_without_path)
            self.saveLabels(label_file)
            if label_file.find("meta") < 0:
                label_file = osp.dirname(label_file) + "/meta/" + osp.basename(label_file)
            # run coco format
            threading.Timer(0.005, self.putDownCocoFormat, [label_file]).start()

            # add ckd 보관후에 되돌이막기
            saveShapes = self.canvas.shapes
            self.canvas.shapes = []
            self.canvas.shapesBackups = []
            self.canvas.loadShapes(saveShapes, True)
            self.actions.undo.setEnabled(self.canvas.isShapeRestorable)
            # add ckd

            return

        self.dirty = True
        self.actions.save.setEnabled(True)
        title = __appname__
        if self.filename is not None:
            title = "{} - {}*".format(title, self.filename)
        self.setWindowTitle(title)

    def setClean(self):
        self.dirty = False
        self.actions.save.setEnabled(False)
        self.actions.createMode.setEnabled(True)
        self.actions.createRectangleMode.setEnabled(True)
        self.actions.createCircleMode.setEnabled(True)
        #self.actions.createLineMode.setEnabled(True)
        #self.actions.createPointMode.setEnabled(True)
        #self.actions.createLineStripMode.setEnabled(True)
        title = __appname__
        if self.filename is not None:
            title = "{} - {}".format(title, self.filename)
        self.setWindowTitle(title)

        if self.hasLabelFile():
            self.actions.deleteFile.setEnabled(True)
        else:
            self.actions.deleteFile.setEnabled(False)

    def toggleActions(self, value=True):
        """Enable/Disable widgets which depend on an opened image."""
        for z in self.actions.zoomActions:
            z.setEnabled(value)
        for action in self.actions.onLoadActive:
            action.setEnabled(value)

        self.topToolWidget.setEnabled(value)
        self.topToolWidget.trans.setEnabled(value)
        self.topToolWidget.topbarHide.setEnabled(value)

    def queueEvent(self, function):
        QtCore.QTimer.singleShot(0, function)

    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)

    def resetState(self):
        self.labelList.clear()  # this block now when polygon list is deleted
        # update polygon count ckd
        prodT = "Polygon Labels (Total %s)"
        if self._config["local_lang"] == "ko_KR":
            prodT = "다각형 레이블 (총 %s)"
        self.shape_dock.titleBarWidget().titleLabel.setText(prodT % len(self.labelList))

        self.filename = None
        self.imagePath = None
        self.imageData = None
        self.labelFile = None
        self.otherData = None
        self.canvas.resetState()

    def currentItem(self):
        try:
            items = self.labelList.selectedItems()
            if items:
                return items[0]
        except Exception as e:
            LogPrint("선택한 아이템 %s" % e)
        return None

    def addRecentFile(self, filename):
        try:
            if osp.splitext(filename)[1] == ".json":  # don't save json file
                return
            if filename in self.recentFiles:
                self.recentFiles.remove(filename)
            elif len(self.recentFiles) >= self.maxRecent:
                self.recentFiles.pop()
            self.recentFiles.insert(0, filename)
        except Exception as e:
            LogPrint("최신 파일 추가중 : %s" % e)
            pass

    # Callbacks

    def undoShapeEdit(self):
        try:
            self.canvas.restoreShape()
            self.labelList.clear()
            self._itemList.clear()
            self.loadShapes(self.canvas.shapes)
            self.actions.undo.setEnabled(self.canvas.isShapeRestorable)
            #self.setDirty()  # add 11.02.2022
        except Exception as e:
            LogPrint("undoShapeEdit 실행중 %s" % e)
            pass

    def tutorial(self):
        try:
            url = self._config["api_url"] + 'ords/r/lm/lm'  # NOQA
            webbrowser.open(url)
        except Exception as e:
            LogPrint("웹브라우져열기중 %s" % e)
            pass

    def changePasswordAction(self):
        status = self._pwdDlg.popUpDlg()
        #print("status of change pwd is %s" % status)
        #pass


    def toggleDrawingSensitive(self, drawing=True):
        """Toggle drawing sensitive.
        In the middle of drawing, toggling between modes should be disabled.
        """
        self.actions.editMode.setEnabled(not drawing)
        self.actions.undoLastPoint.setEnabled(drawing)
        self.actions.undo.setEnabled(not drawing)
        self.actions.delete.setEnabled(not drawing)

    def toggleDrawMode(self, edit=True, createmode="polygon"):
        try:
            self.canvas.setEditing(edit)
            self.canvas.createMode = createmode
            if edit:
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                #self.actions.createLineMode.setEnabled(True)
                #self.actions.createPointMode.setEnabled(True)
                #self.actions.createLineStripMode.setEnabled(True)
                self.topToolWidget.editmodeClick(True)
            else:
                if createmode == "polygon":
                    self.actions.createMode.setEnabled(False)
                    self.actions.createRectangleMode.setEnabled(True)
                    self.actions.createCircleMode.setEnabled(True)
                    #self.actions.createLineMode.setEnabled(True)
                    #self.actions.createPointMode.setEnabled(True)
                    # self.actions.createLineStripMode.setEnabled(True)
                    self.topToolWidget.eventFromMenu(createmode)
                elif createmode == "rectangle":
                    self.actions.createMode.setEnabled(True)
                    self.actions.createRectangleMode.setEnabled(False)
                    self.actions.createCircleMode.setEnabled(True)
                    #self.actions.createLineMode.setEnabled(True)
                    #self.actions.createPointMode.setEnabled(True)
                    #self.actions.createLineStripMode.setEnabled(True)
                    self.topToolWidget.eventFromMenu(createmode)
                elif createmode == "line":
                    self.actions.createMode.setEnabled(True)
                    self.actions.createRectangleMode.setEnabled(True)
                    self.actions.createCircleMode.setEnabled(True)
                    #self.actions.createLineMode.setEnabled(False)
                    #self.actions.createPointMode.setEnabled(True)
                    #self.actions.createLineStripMode.setEnabled(True)
                    self.topToolWidget.eventFromMenu(createmode)
                elif createmode == "point":
                    self.actions.createMode.setEnabled(True)
                    self.actions.createRectangleMode.setEnabled(True)
                    self.actions.createCircleMode.setEnabled(True)
                    #self.actions.createLineMode.setEnabled(True)
                    #self.actions.createPointMode.setEnabled(False)
                    #self.actions.createLineStripMode.setEnabled(True)
                    self.topToolWidget.eventFromMenu(createmode)
                elif createmode == "circle":
                    self.actions.createMode.setEnabled(True)
                    self.actions.createRectangleMode.setEnabled(True)
                    self.actions.createCircleMode.setEnabled(False)
                    #self.actions.createLineMode.setEnabled(True)
                    #self.actions.createPointMode.setEnabled(True)
                    # self.actions.createLineStripMode.setEnabled(True)
                    self.topToolWidget.eventFromMenu(createmode)
                elif createmode == "linestrip":
                    self.actions.createMode.setEnabled(True)
                    self.actions.createRectangleMode.setEnabled(True)
                    self.actions.createCircleMode.setEnabled(True)
                    #self.actions.createLineMode.setEnabled(True)
                    #self.actions.createPointMode.setEnabled(True)
                    #self.actions.createLineStripMode.setEnabled(False)
                    self.topToolWidget.eventFromMenu(createmode)
                else:
                    raise ValueError("Unsupported createMode: %s" % createmode)
            self.actions.editMode.setEnabled(not edit)
        except Exception as e:
            LogPrint("도글모드 전환중 %s" % e)
            pass

    def setEditMode(self):
        self.toggleDrawMode(True)

    def updateFileMenu(self):
        current = self.filename

        def exists(filename):
            return osp.exists(str(filename))

        menu = self.menus.recentFiles
        menu.clear()
        files = [f for f in self.recentFiles if f != current and exists(f)]
        for i, f in enumerate(files):
            icon = utils.newIcon("labels")
            action = QtWidgets.QAction(
                icon, "&%d %s" % (i + 1, QtCore.QFileInfo(f).fileName()), self
            )
            action.triggered.connect(functools.partial(self.loadRecent, f))
            menu.addAction(action)

    def popLabelListMenu(self, point):
        self.menus.labelList.exec_(self.labelList.mapToGlobal(point))

    def validateLabel(self, label):
        # no validation
        if self._config["validate_label"] is None:
            return True

        return False

    def editLabels(self):
        try:
            if len(self._polyonList) < 1:
                return self.errorMessage(self.tr("Wrong Empty label"),
                                         self.tr("please select one grade for label in Grade list"))
            if not self.canvas.editing():
                return

            f_item = self.labelList.selectedItems()[0]
            if f_item and not isinstance(f_item, CustomLabelListWidgetItem):
                LogPrint("item must be CustomLabelListWidgetItem type")
                raise TypeError("item must be CustomLabelListWidgetItem type")
            f_shape = f_item.shape()
            if f_shape is None:
                return
            old_color = f_shape.color
            assert isinstance(old_color, QtGui.QColor)

            polyitems = copy.deepcopy(self._polyonList)
            ritem = self.labelDialog.popUpLabelDlg(polyitems, f_shape, "edit")
            if ritem is None:
                return
            if not self.validateLabel(ritem["label"]):
                self.errorMessage(
                    self.tr("Invalid label"),
                    self.tr("Invalid label '{}' with validation type '{}'").format(
                        ritem["label"], self._config["validate_label"]
                    ),
                )
                return

            for item in self.labelList.selectedItems():
                if not isinstance(item, CustomLabelListWidgetItem):
                    raise TypeError("item must be CustomLabelListWidgetItem type")
                shape = item.shape()
                shape.label = ritem["label"]
                shape.label_display = ritem["label_display"]
                shape.grade = ritem["grade"]
                shape.color = ritem["color"]

                old_a = old_color.alpha()
                sc = shape.color if shape.color else "#808000"
                Qc = QtGui.QColor(sc)
                r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
                shape.color = QtGui.QColor(r, g, b, old_a)
                self._update_shape_color(shape)

                item_len = item.getNumber()
                if item_len < 10000:
                    item_len = "%04d" % item_len
                else:
                    item_len = "%08d" % item_len

                item.setText(
                    '&nbsp; <font size=3 color="#{:02x}{:02x}{:02x}">█</font>&nbsp;   #{}  &nbsp;  {}'.format(
                        *shape.color.getRgb()[:3], item_len, html.escape(shape.label_display)
                    )
                )

            self.setDirty()
        except Exception as e:
            LogPrint("멀티라벨 변경중 %s" % e)
            pass


    def editLabel(self, item=None):

        if len(self.labelList.selectedItems()) > 1:
            self.editLabels()
            return
        try:
            if item and not isinstance(item, CustomLabelListWidgetItem):
                raise TypeError("item must be CustomLabelListWidgetItem type")

            if not self.canvas.editing():
                return
            if not item:
                item = self.currentItem()
            if item is None:
                return

            shape = item.shape()
            if shape is None:
                return
            old_color = shape.color
            assert isinstance(old_color, QtGui.QColor)

            polyitems = copy.deepcopy(self._polyonList)
            ritem = self.labelDialog.popUpLabelDlg(polyitems, shape, "edit")
            if ritem is None:
                return
            if not self.validateLabel(ritem["label"]):
                self.errorMessage(
                    self.tr("Invalid label"),
                    self.tr("Invalid label '{}' with validation type '{}'").format(
                        ritem["label"], self._config["validate_label"]
                    ),
                )
                return

            shape.label = ritem["label"]
            shape.label_display = ritem["label_display"]
            shape.grade = ritem["grade"]
            shape.color = ritem["color"]

            old_a = old_color.alpha()
            sc = shape.color if shape.color else "#808000"
            Qc = QtGui.QColor(sc)
            r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
            shape.color = QtGui.QColor(r, g, b, old_a)
            self._update_shape_color(shape)

            item_len = item.getNumber()
            if item_len < 10000:
                item_len = "%04d" % item_len
            else:
                item_len = "%08d" % item_len

            # update label
            item.setText(
                '&nbsp; <font size=3 color="#{:02x}{:02x}{:02x}">█</font>&nbsp;   #{}  &nbsp;  {}'.format(
                    *shape.color.getRgb()[:3], item_len, html.escape(shape.label_display)
                )
            )

            self.setDirty()
        except Exception as e:
            LogPrint("라벨 변경중 %s" % e)
            pass

    def fileSearchChanged(self):
        self.importDirImages(
            self.lastOpenDir,
            pattern=self.fileSearch.text(),
            load=False,
        )

    def polygonReturnSearchChanged(self):
        try:
            pattern = self.polygonSearch.text().strip()  #3/3/2023
            temp_items = self._itemList
            self.labelList.clear()
            saveShapes = []  #add 01/02/2023
            for shape in temp_items:
                grade = shape.grade
                label = shape.label
                if pattern and pattern not in grade and pattern not in label:
                    continue

                if shape.label_display is None:
                    text = shape.label
                else:
                    text = shape.label_display

                list_item = CustomLabelListWidgetItem(text, shape)
                self.labelList.addItem(list_item)

                item_len = self.labelList.__len__()
                list_item.setNumber(item_len)

                if item_len < 10000:
                    item_len = "%04d" % item_len
                else:
                    item_len = "%08d" % item_len
                list_item.setText(
                    '&nbsp; <font size=3 color="#{:02x}{:02x}{:02x}">█</font>&nbsp;   #{}  &nbsp;  {}'.format(
                        *shape.color.getRgb()[:3], item_len, html.escape(text)
                    )
                )
                saveShapes.append(shape)  #add 01/02/2023

            # add 01/02/2023 {
            self.canvas.shapes = []
            self.canvas.shapesBackups = []
            self.canvas.loadShapes(saveShapes, True)
            self.actions.undo.setEnabled(self.canvas.isShapeRestorable)
            # add 01/02/2023 }
            prodT = "Polygon Labels (Total {})".format(self.labelList.__len__())
            if self._config["local_lang"] == "ko_KR":
                prodT = "다각형 레이블 (총 {})".format(self.labelList.__len__())
            self.shape_dock.titleBarWidget().titleLabel.setText(prodT)
        except Exception as e:
            LogPrint("라벨검색중 %s" % e)
            pass


    def polygonSearchChanged_No(self):
        try:
            pattern = self.polygonSearch.text()
            pattern = pattern.strip()
            if len(pattern) > 0:
                return

            temp_items = self._itemList
            self.labelList.clear()
            saveShapes = []  # add 01/02/2023
            for shape in temp_items:
                grade = shape.grade
                label = shape.label
                if pattern and pattern not in grade and pattern not in label:
                    continue

                if shape.label_display is None:
                    text = shape.label
                else:
                    text = shape.label_display

                list_item = CustomLabelListWidgetItem(text, shape)
                self.labelList.addItem(list_item)

                item_len = self.labelList.__len__()
                list_item.setNumber(item_len)

                if item_len < 10000:
                    item_len = "%04d" % item_len
                else:
                    item_len = "%08d" % item_len
                list_item.setText(
                    '&nbsp; <font size=3 color="#{:02x}{:02x}{:02x}">█</font>&nbsp;   #{}  &nbsp;  {}'.format(
                        *shape.color.getRgb()[:3], item_len, html.escape(text)
                    )
                )
                saveShapes.append(shape)  # add 01/02/2023
            # add 01/02/2023 {
            self.canvas.shapes = []
            self.canvas.shapesBackups = []
            self.canvas.loadShapes(saveShapes, True)
            self.actions.undo.setEnabled(self.canvas.isShapeRestorable)
            # add 01/02/2023 }

            prodT = "Polygon Labels (Total {})".format(self.labelList.__len__())
            if self._config["local_lang"] == "ko_KR":
                prodT = "다각형 레이블 (총 {})".format(self.labelList.__len__())
            self.shape_dock.titleBarWidget().titleLabel.setText(prodT)
        except Exception as e:
            LogPrint("라벨검색1 중 %s" % e)
            pass

    # no using
    def productsSelectionChanged(self):
        try:
            items = self.products_widget.selectedItems()
            if not items:
                return
            item = items[0]
            #print(str(item.text()))
            self.selected_product = item.text()
        except Exception as e:
            LogPrint("품명 선택 변경중 %s" % e)
            pass

    def fileSelectionChanged(self):
        try:
            items = self.fileListWidget.selectedItems()
            if not items:
                return
            item = items[0]

            if not self.mayContinue():
                return

            currIndex = self.imageList.index(str(item.text()))
            if currIndex < len(self.imageList):
                filename = self.imageList[currIndex]
                if filename:
                    self.loadFile(filename)
        except Exception as e:
            LogPrint("선택한 파일로딩중 %s" % e)
            pass

    # React to canvas signals.
    def shapeSelectionChanged(self, selected_shapes):
        try:
            self._noSelectionSlot = True
            for shape in self.canvas.selectedShapes:
                shape.selected = False
            self.labelList.clearSelection()
            self.canvas.selectedShapes = selected_shapes
            for shape in self.canvas.selectedShapes:
                shape.selected = True
                item = self.labelList.findItemByShape(shape)
                if item:
                    self.labelList.selectItem(item)
                    self.labelList.scrollToItem(item)

            self._noSelectionSlot = False
            n_selected = len(selected_shapes)
            self.actions.delete.setEnabled(n_selected)
            self.actions.duplicate.setEnabled(n_selected)
            self.actions.copy.setEnabled(n_selected)
            # self.actions.edit.setEnabled(n_selected == 1) # edit for single
            self.actions.edit.setEnabled(n_selected)  # add ckd 9/7/2022
        except Exception as e:
            LogPrint("선택한 shape 변경중 %s" % e)
            pass

    def addLabel(self, shape):
        try:
            if shape.label_display is None:
                text = shape.label
            else:
                text = shape.label_display

            list_item = CustomLabelListWidgetItem(text, shape)
            self.labelList.addItem(list_item)
            self._itemList.append(shape)

            self.labelDialog.addLabelHistory(shape)
            for action in self.actions.onShapesPresent:
                action.setEnabled(True)

            item_len = self.labelList.__len__()
            list_item.setNumber(item_len)

            if item_len < 10000:
                item_len = "%04d" % item_len
            else:
                item_len = "%08d" % item_len

            if not isinstance(shape.color, QtGui.QColor):
                self._update_shape_color(shape)
                self.canvas.update()

            list_item.setText(
                '&nbsp; <font size=3 color="#{:02x}{:02x}{:02x}">█</font>&nbsp;   #{}  &nbsp;  {}'.format(
                    *shape.color.getRgb()[:3], item_len, html.escape(text)
                )
            )

            prodT = "Polygon Labels (Total %s)"
            if self._config["local_lang"] == "ko_KR":
                prodT = "다각형 레이블 (총 %s)"
            self.shape_dock.titleBarWidget().titleLabel.setText(prodT % self.labelList.__len__())
            #self._update_shape_color(shape) 이부분에선 불필요
        except Exception as e:
            LogPrint("라벨추가중 오류 :: %s" % e)
            pass


    def _update_shape_color(self, shape):
        try:
            if shape.color:
                if isinstance(shape.color, QtGui.QColor):
                    Qc = shape.color
                else:
                    Qc = QtGui.QColor(shape.color)
            else:
                Qc = QtGui.QColor("#808000")

            r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
            sa = a if a < self.polygonTrans_deta_value else self.polygonTrans_deta_value
            shape.color = QtGui.QColor(r, g, b, sa)
            la = int(sa * 255 / 128)
            shape.line_color = QtGui.QColor(r, g, b, la)
            shape.vertex_fill_color = QtGui.QColor(r, g, b, a)
            shape.hvertex_fill_color = QtGui.QColor(255, 255, 255)
            shape.fill_color = QtGui.QColor(r, g, b, a if a < 255 else 128)  # a=128
            shape.select_line_color = QtGui.QColor(255, 255, 255, a + 80)
            shape.select_fill_color = QtGui.QColor(r, g, b, a + 27)  # a = 155
            shape.lineweight = self.lineweight_value
        except Exception as e:
            LogPrint("shape 색깔 변경중 %s" % e)
            pass

    def _get_rgb_by_label(self, label):
        try:
            if self._config["shape_color"] == "auto":
                item = self.uniqLabelList.findItemsByLabel(label)[0]
                label_id = self.uniqLabelList.indexFromItem(item).row() + 1
                label_id += self._config["shift_auto_shape_color"]
                return LABEL_COLORMAP[label_id % len(LABEL_COLORMAP)]
            elif (
                self._config["shape_color"] == "manual"
                and self._config["label_colors"]
                and label in self._config["label_colors"]
            ):
                return self._config["label_colors"][label]
            elif self._config["default_shape_color"]:
                return self._config["default_shape_color"]
            return (0, 255, 0)
        except Exception as e:
            LogPrint("shape 색설정 얻는중 %s" % e)
        return (0, 0, 0)

    def remLabels(self, shapes):
        try:
            for shape in shapes:
                item = self.labelList.findItemByShape(shape)
                if item:
                    self.labelList.removeItem(item)
            idx = 1
            for item in self.labelList:
                if item:
                    shape = item.shape()
                    item.setNumber(idx)
                    if idx < 10000:
                        item_len = "%04d" % idx
                    else:
                        item_len = "%08d" % idx
                    if shape:
                        item.setText(
                            '&nbsp; <font size=3 color="#{:02x}{:02x}{:02x}">█</font>&nbsp;   #{}  &nbsp;  {}'.format(
                                *shape.color.getRgb()[:3], item_len, html.escape(shape.label_display)
                            )
                        )
                    idx = idx+1


            threading.Timer(0.005, self.removeitemListShapesWithThread, [shapes]).start()
        except Exception as e:
            LogPrint("라벨리스트에서 삭제중 %s" % e)


    def removeitemListShapesWithThread(self, shapes):
        try:
            for shape in shapes:
                for i in range(len(self._itemList)):
                    itm_shape = self._itemList[i]
                    if itm_shape == shape:
                        del self._itemList[i]
                        break
        except Exception as e:
            LogPrint("아이템 리스트에서 아이템삭제중 : %s" % e)
            pass

    def loadShapes(self, shapes, replace=True):
        try:
            self._noSelectionSlot = True
            for shape in shapes:
                self.addLabel(shape)
            self.labelList.clearSelection()
            self._noSelectionSlot = False
            self.canvas.loadShapes(shapes, replace=replace)
        except Exception as e:
            LogPrint("shape 오브젝트들을 로딩중 : %s" % e)
            pass

        ##threading.Timer(0.005, self.addLabelWithThread, [shapes]).start()

    def addLabelWithThread(self, shapes):
        splt = 500
        slen = len(shapes) / splt
        if slen > 2:
            self.loadingLabelDlg = LoadingLabelProgress(parent=self, config=self._config, size=len(shapes), splt=splt)
            self.loadingLabelDlg.show()
            i = 0
            for shape in shapes:
                self.addLabel(shape)
                if i < splt:
                    i = i + 1
                else:
                    self.loadingLabelDlg.doAction()
                    time.sleep(0.001)
                    i = 0
            self.loadingLabelDlg._isEnd = True
            self.loadingLabelDlg.close()
        else:
            for shape in shapes:
                self.addLabel(shape)

    def loadLabels(self, shapes):
        s = []
        inval = False
        for shape in shapes:
            try:
                grade = shape["grade"]
            except AttributeError as e:
                grade = shape["label"]
                LogPrint("shape 에 grade 속성이 없습니다 : %s" % e)
                pass

            try:
                label_display = shape["label_display"]
            except AttributeError as e:
                label_display = shape["label"]
                LogPrint("shape 에 label 속성이 없습니다 : %s" % e)
                pass

            label = shape["label"]
            color = shape["color"]
            points = shape["points"]
            lineweight = shape["lineweight"]
            shape_type = shape["shape_type"]
            group_id = shape["group_id"]
            other_data = shape["other_data"]

            Qc = QtGui.QColor(color if color else "#808000")
            r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
            # print("load shape", str(a))
            if inval is False:
                if a >= self.polygonTrans_deta_value:
                    self.polygonTrans_value = 0
                else:
                    self.polygonTrans_value = self.polygonTrans_deta_value - a

                self.lineweight_value = float(lineweight)
                inval = True

            #color = QtGui.QColor(r, g, b, a if a < self.polygonTrans_deta_value else self.polygonTrans_deta_value)
            if not points:
                # skip point-empty shape
                continue

            try:
                shape = Shape(
                    self,
                    grade=grade,
                    label=label,
                    label_display=label_display,
                    color=color if color else "#808000",
                    lineweight=lineweight,
                    shape_type=shape_type,
                    group_id=group_id,
                )
                for x, y in points:
                    shape.addPoint(QtCore.QPointF(x, y))
                shape.close()
                shape.other_data = other_data
            except Exception as e:
                LogPrint("shape 생성중 %s" % e)
                pass

            s.append(shape)
        self.loadShapes(s)

    def loadGrades(self, items):
        try:
            self.grades_widget.clear()
            for i in range(len(items)):
                itm = items[i]
                item = QtWidgets.QListWidgetItem(itm["grade"])
                # item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                # item.setCheckState(Qt.Checked if flag else Qt.Unchecked)
                self.grades_widget.addItem(item)
        except Exception as e:
            LogPrint("grade 로딩중 %s" % e)
            pass

    def loadProducts(self, items):
        try:
            self.products_widget.clear()
            for i in range(len(items)):
                itm = items[i]
                item = QtWidgets.QListWidgetItem(itm["product"])
                item.setFont(appFont())
                # item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                # item.setCheckState(Qt.Checked if flag else Qt.Unchecked)
                self.products_widget.addItem(item)
            if self._config["local_lang"] == "ko_KR":
                self.products_title_bar.titleLabel.setText("대표 품목 (총 %s)" % self.products_widget.__len__())
            else:
                self.products_title_bar.titleLabel.setText("Products (Total %s)" % self.products_widget.__len__())
        except Exception as e:
            LogPrint("대표품목 로딩중: %s" %e)
            pass


    def addProduct(self, new_str):
        try:
            item = QtWidgets.QListWidgetItem(new_str)
            item.setFont(appFont())
            self.products_widget.insertItem(0, item)
            if self._config["local_lang"] == "ko_KR":
                self.products_title_bar.titleLabel.setText("대표 품목 (총 %s)" % self.products_widget.__len__())
            else:
                self.products_title_bar.titleLabel.setText("Products (Total %s)" % self.products_widget.__len__())
        except Exception as e:
            LogPrint("대표품목 추가중 %s" % e)
            pass


    def saveLabels(self, filename):
        lf = LabelFile()

        def format_shape(s):
            data = s.other_data.copy()
            grade = s.grade.encode("utf-8") if PY2 else s.grade
            label_display = s.label_display.encode("utf-8") if PY2 else s.label_display
            label = s.label.encode("utf-8") if PY2 else s.label

            cColor = QtGui.QColor(s.color if s.color else "#808000")
            lineweight = s.lineweight if s.lineweight else "2.0"
            # r, g, b, a = cColor.red(), cColor.green(), cColor.blue(), cColor.alpha()
            #print("save shape", str(a))
            plen = len(s.points)
            if plen == 1:
                s.shape_type = "point"
            cnams_str = cColor.name(QtGui.QColor.HexArgb)
            data.update(
                dict(
                    grade=grade,
                    label=label,
                    label_display=label_display,
                    color=cnams_str,
                    points=[(p.x(), p.y()) for p in s.points],
                    lineweight=lineweight,
                    shape_type=s.shape_type,
                    group_id=s.group_id
                )
            )
            return data

        shapes = [format_shape(shape) for shape in self._itemList] #add 03/03/2023
        #shapes = [format_shape(item.shape()) for item in self.labelList]
        try:
            if self.imagePath.find("meta/") > -1:
                self.imagePath = self.imagePath.replace("meta/", "")
            imagePath = osp.relpath(self.imagePath, osp.dirname(filename))
            #imageData = self.imageData if self._config["store_data"] else None # add ckd 9.28.2022
            imageData = None
            meta_dir = osp.dirname(filename) + "/meta"
            filename = meta_dir + '/' + osp.basename(filename)
            # if osp.dirname(filename) and not osp.exists(osp.dirname(filename)):
            #     os.makedirs(osp.dirname(filename))
            if osp.dirname(filename) and not osp.exists(osp.dirname(filename)):
                os.makedirs(osp.dirname(filename))

            lf.save(
                filename=filename,
                shapes=shapes,
                imagePath=imagePath,
                imageData=imageData,
                imageHeight=self.image.height(),
                imageWidth=self.image.width(),
                otherData=self.otherData,
            )
            self.labelFile = lf
            items = self.fileListWidget.findItems(
                self.imagePath, Qt.MatchExactly
            )
            if len(items) > 0:
                if len(items) != 1:
                    raise RuntimeError("There are duplicate files.")
                items[0].setCheckState(Qt.Checked)
            # disable allows next and previous image to proceed
            # self.filename = filename
            return True
        except LabelFileError as e:
            self.errorMessage(
                self.tr("Error saving label data"), self.tr("<b>%s</b>") % e
            )
            LogPrint("labelFile에 오브젝트를 보관하는중 : %s" % e)
            return False

    def duplicateSelectedShape(self):
        try:
            added_shapes = self.canvas.duplicateSelectedShapes()
            self.labelList.clearSelection()
            for shape in added_shapes:
                self.addLabel(shape)
            prodT = "Polygon Labels (Total %s)"
            if self._config["local_lang"] == "ko_KR":
                prodT = "다각형 레이블 (총 %s)"
            self.shape_dock.titleBarWidget().titleLabel.setText(prodT % self.labelList.__len__())
            self.setDirty()
        except Exception as e:
            LogPrint("duplicateSelectedShape %s" % e)
            pass

    def pasteSelectedShape(self):
        try:
            self.loadShapes(self._copied_shapes, replace=False)
            prodT = "Polygon Labels (Total %s)"
            if self._config["local_lang"] == "ko_KR":
                prodT = "다각형 레이블 (총 %s)"
            self.shape_dock.titleBarWidget().titleLabel.setText(prodT % self.labelList.__len__())
            self.setDirty()
        except Exception as e:
            LogPrint("pasteSelectedShape %s" % e)
            pass

    def copySelectedShape(self):
        self._copied_shapes = [s.copy() for s in self.canvas.selectedShapes]
        self.actions.paste.setEnabled(len(self._copied_shapes) > 0)

    def labelSelectionChanged(self):
        try:
            if self._noSelectionSlot:
                return
            if self.canvas.editing():
                selected_shapes = []
                for item in self.labelList.selectedItems():
                    selected_shapes.append(item.shape())
                if selected_shapes:
                    self.canvas.selectShapes(selected_shapes)
                else:
                    self.canvas.deSelectShape()
        except Exception as e:
            LogPrint("labelSelectionChanged %s" % e)
            pass

    def labelItemChanged(self, item):
        try:
            shape = item.shape()
            if shape:
                self.canvas.setShapeVisible(shape, item.checkState() == Qt.Checked)
        except Exception as e:
            LogPrint("labelItemChanged %s" % e)
            pass

    def labelOrderChanged(self):
        try:
            self.setDirty()
            self.canvas.loadShapes([item.shape() for item in self.labelList])
        except Exception as e:
            LogPrint("labelOrderChanged %s" % e)
            pass
    # Callback functions:

    def labelItemsChecked(self, flag):
        try:
            for item in self.labelList:
                shape = item.shape()
                if shape:
                    if flag is True:
                        item.setCheckState(Qt.Checked)
                        self.canvas.setShapeVisible(shape, Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
                        self.canvas.setShapeVisible(shape, Qt.Unchecked)
        except Exception as e:
            LogPrint("labelItemsChecked %s" % e)
            pass

    def newShape(self):
        try:
            #items = self._polyonList[:]
            items = copy.deepcopy(self._polyonList)
            if len(items) < 1:
                self.canvas.shapes.pop()
                self.canvas.repaint()
                return self.errorMessage(self.tr("Wrong Empty label"), self.tr("please select one grade for label in Grade list"))
    
            group_id = None
            item = None
            if self._config["display_label_popup"]:
                previous_text = self.labelDialog.edit.text()
                item = self.labelDialog.popUpLabelDlg(items)
                if not item:
                    self.labelDialog.edit.setText(previous_text)
    
            if item and not self.validateLabel(item["label"]):
                self.errorMessage(
                    self.tr("Invalid label"),
                    self.tr("Invalid label '{}' with validation type '{}'").format(
                        item["label"], self._config["validate_label"]
                    ),
                )
                item = None
            if item:
                self.labelList.clearSelection()
                shape = self.canvas.setLastLabel(item)
                shape.group_id = group_id
                sc = shape.color if shape.color else "#808000"
                Qc = QtGui.QColor(sc)
                r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
                shape.color = QtGui.QColor(r, g, b, a)
                if self.polygonTrans_value > 0:
                    a = self.polygonTrans_deta_value - self.polygonTrans_value
                else:
                    a = self.polygonTrans_deta_value

                shape.color = QtGui.QColor(r, g, b, a)
                #add 01/02/2023 {
                la = int(a * 255 / 128)
                shape.line_color = QtGui.QColor(r, g, b, la)
                shape.vertex_fill_color = QtGui.QColor(r, g, b, a)
                shape.hvertex_fill_color = QtGui.QColor(255, 255, 255)
                shape.fill_color = QtGui.QColor(r, g, b, a)
                shape.select_line_color = QtGui.QColor(255, 255, 255, a + 80)
                shape.select_fill_color = QtGui.QColor(r, g, b, a + 27)
                #add 01/02/2023 }

                shape.lineweight = self.lineweight_value
                # print("new shape", str(a))
                self.addLabel(shape)
                self.actions.editMode.setEnabled(True)
                self.actions.undoLastPoint.setEnabled(False)
                self.actions.undo.setEnabled(True)
                self.setDirty()
            else:
                self.canvas.undoLastLine()
                self.canvas.shapesBackups.pop()
        except Exception as e:
            LogPrint("shape 추가중 %s" % e)
            pass

    def scrollRequest(self, delta, orientation):
        units = -delta * 0.1  # natural scroll
        bar = self.scrollBars[orientation]
        value = bar.value() + bar.singleStep() * units
        self.setScroll(orientation, value)

    def setScroll(self, orientation, value):
        self.scrollBars[orientation].setValue(value)
        self.scroll_values[orientation][self.filename] = value

    def setZoom(self, value):
        self.actions.fitWidth.setChecked(False)
        self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.MANUAL_ZOOM
        self.zoomWidget.setValue(value)
        self.zoom_values[self.filename] = (self.zoomMode, value)

    def addZoom(self, increment=1.1):
        zoom_value = self.zoomWidget.value() * increment
        if increment > 1:
            zoom_value = math.ceil(zoom_value)
        else:
            zoom_value = math.floor(zoom_value)
        self.setZoom(zoom_value)

    def zoomRequest(self, delta, pos):
        canvas_width_old = self.canvas.width()
        units = 1.1
        if delta < 0:
            units = 0.9
        self.addZoom(units)

        canvas_width_new = self.canvas.width()
        if canvas_width_old != canvas_width_new:
            canvas_scale_factor = canvas_width_new / canvas_width_old

            x_shift = round(pos.x() * canvas_scale_factor) - pos.x()
            y_shift = round(pos.y() * canvas_scale_factor) - pos.y()

            self.setScroll(
                Qt.Horizontal,
                self.scrollBars[Qt.Horizontal].value() + x_shift,
            )
            self.setScroll(
                Qt.Vertical,
                self.scrollBars[Qt.Vertical].value() + y_shift,
            )

    def setFitWindow(self, value=True):
        if value:
            self.actions.fitWidth.setChecked(False)
        self.zoomMode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjustScale()

    def setFitWidth(self, value=True):
        if value:
            self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjustScale()

    def enableKeepPrevScale(self, enabled):
        self._config["keep_prev_scale"] = enabled
        self.actions.keepPrevScale.setChecked(enabled)

    def onNewBrightnessContrast(self, qimage):
        try:
            self.canvas.loadPixmap(
                QtGui.QPixmap.fromImage(qimage), clear_shapes=False
            )
        #print("ending...Brightness")
        except Exception as e:
            LogPrint("onNewBrightnessContrast %s" % e)
            pass

    def brightnessContrast(self, value):
        try:
            if self.brightDialog is None:
                self.brightDialog = BrightnessContrastDialog(
                    utils.img_data_to_pil(self.imageData),
                    self.onNewBrightnessContrast,
                    parent=self,
                )
            brightness, contrast = self.brightnessContrast_values.get(
                self.filename, (None, None)
            )
            if brightness is not None:
                self.brightDialog.slider_brightness.setValue(brightness)
            if contrast is not None:
                self.brightDialog.slider_contrast.setValue(contrast)
            self.brightDialog.exec_()

            brightness = self.brightDialog.slider_brightness.value()
            contrast = self.brightDialog.slider_contrast.value()
            self.brightnessContrast_values[self.filename] = (brightness, contrast)
        except Exception as e:
            LogPrint("brightnessContrast %s" % e)
            pass

    def PolygonAlpha(self, transobj):
        try:
            if self.polygonAlphaDlg is None:
                self.polygonAlphaDlg = PolygonTransDialog(
                    utils.img_data_to_pil(self.imageData),
                    self.onNewBrightnessContrast,
                    self.polygonTrans,
                    self.lineweight,
                    parent=self,
                )
            brightness, contrast = self.brightnessContrast_values.get(
                self.filename, (None, None)
            )
            if brightness is not None:
                self.polygonAlphaDlg.slider_brightness.setValue(brightness)
            if contrast is not None:
                self.polygonAlphaDlg.slider_contrast.setValue(contrast)

            if self.polygonTrans_value:
                self.polygonAlphaDlg.slider_trans.setValue(self.polygonTrans_value)

            if self.lineweight_value:
                self.polygonAlphaDlg.slider_pen.setValue(self.lineweight_value)

            self.polygonAlphaDlg.exec_()

            #brightness = dialog.slider_brightness.value()
            #contrast = dialog.slider_contrast.value()

            brightness = self.polygonAlphaDlg.slider_brightness.value()
            contrast = self.polygonAlphaDlg.slider_contrast.value()
            self.brightnessContrast_values[self.filename] = (brightness, contrast)

            val = self.polygonAlphaDlg.slider_trans.value()
            self.polygonTrans_value = val

            val_l = self.polygonAlphaDlg.slider_pen.value()
            self.lineweight_value = val_l

            transobj.setEnabled(True)
            self.setDirty()
        except Exception as e:
            LogPrint("알파적용중 %s" % e)
            pass

    def viewAppVersion(self):
        self.appVersionDialog = AppVersionDialog(
            self._config,
            parent=self,
        )
        self.appVersionDialog.exec_()

    def polygonTrans(self, value):
        try:
            if self.canvas.shapes and len(self.canvas.shapes) < 1:
                return
            for shape in self.canvas.shapes:
                Qc = QtGui.QColor(shape.color)
                r, g, b, a = Qc.red(), Qc.green(), Qc.blue(), Qc.alpha()
                alpha = self.polygonTrans_deta_value - value
                shape.color = QtGui.QColor(r, g, b, alpha)
                # shape.line_color = QtGui.QColor(r, g, b, alpha + 50)
                # shape.fill_color = QtGui.QColor(r, g, b, alpha)
                # shape.vertex_fill_color = QtGui.QColor(r, g, b, alpha + 50)
                # shape.hvertex_fill_color = QtGui.QColor(255, 255, 255)
                # shape.select_line_color = QtGui.QColor(255, 255, 255, alpha + 50)
                # shape.select_fill_color = QtGui.QColor(r, g, b, alpha + 27)  # a = 155
                self._update_shape_color(shape)
            self.canvas.update()
        except Exception as e:
            LogPrint("폴리곤 색변경중 %s" % e)
            pass

    def lineweight(self, value):
        try:
            if self.canvas.shapes and len(self.canvas.shapes) < 1:
                return
            for shape in self.canvas.shapes:
                shape.lineweight = value
            self.canvas.update()
        except Exception as e:
            LogPrint("라인굵기적용중 %s" % e)
            pass


    def togglePolygons(self, value):
        if value:
            self.actions.tool[9].setEnabled(True)
            self.actions.tool[10].setEnabled(False)
        else:
            self.actions.tool[9].setEnabled(False)
            self.actions.tool[10].setEnabled(True)

        #self.labelList.checkStatus(1 if value else 0)

    def loadFile(self, filename=None):
        """Load the specified file, or the last opened file if None."""
        # changing fileListWidget loads file
        if filename in self.imageList and (
            self.fileListWidget.currentRow() != self.imageList.index(filename)
        ):
            self.fileListWidget.setCurrentRow(self.imageList.index(filename))
            self.fileListWidget.repaint()
            return

        self.resetState()
        self._itemList.clear()
        self.canvas.setEnabled(False)
        if filename is None:
            filename = self.settings.value("filename", "")
        filename = str(filename)
        if not QtCore.QFile.exists(filename):
            self.errorMessage(
                self.tr("Error opening file"),
                self.tr("No such file: <b>%s</b>") % filename,
            )
            return False
        # assumes same name, but json extension
        self.status(
            str(self.tr("Loading %s...")) % osp.basename(str(filename))
        )
        cocofile = False
        labelfile = False
        meta_dir = osp.dirname(filename) + "/meta"
        coco_file = meta_dir + '/{}_coco.{}'.format(osp.splitext(osp.basename(filename))[0], "json")
        #coco_file = "{}_coco.{}".format(osp.splitext(filename)[0], "json")
        if self.output_dir:
            coco_file_without_path = osp.basename(coco_file)
            coco_file = osp.join(self.output_dir, coco_file_without_path)

        if QtCore.QFile.exists(coco_file) and ConvertCoCOLabel.is_coco_file(
            coco_file
        ):
            cocofile = True

        label_file = meta_dir + '/{}.{}'.format(osp.splitext(osp.basename(filename))[0], "json")
        #label_file = osp.splitext(filename)[0] + ".json"
        if self.output_dir:
            label_file_without_path = osp.basename(label_file)
            label_file = osp.join(self.output_dir, label_file_without_path)
        if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
            label_file
        ):
            labelfile = True

        if cocofile is True and labelfile is True:
            try:
                self.labelFile = LabelFile(label_file)
            except LabelFileError as e:
                self.errorMessage(
                    self.tr("Error opening file" if self._config['local_lang'] != 'ko_KR' else '레이블 파일 열기중 오류'),
                    self.tr(
                        "<p><b>{}</b></p>"
                        "<p>Make sure <i>{}</i> is a valid label file." if self._config['local_lang'] != 'ko_KR' else '<i>{}</i> 이 유효한 레이블파일인가를 확인하세요'
                    ).format(e, label_file),
                    #% (e, label_file),
                )
                LogPrint("레이블파일읽기중 %s" % e)
                self.status(self.tr("Error reading {}" if self._config['local_lang'] != 'ko_KR' else '레이블 파일 읽기중 오류').format(label_file))
                return False
            self.imageData = self.labelFile.imageData
            imgpath = label_file
            if imgpath.find("meta/") > -1:
                imgpath = imgpath.replace("meta/", "")
            self.imagePath = osp.join(
                osp.dirname(imgpath),
                self.labelFile.imagePath,
            )
            self.otherData = self.labelFile.otherData
        elif cocofile is False and labelfile is True:
            try:
                self.labelFile = LabelFile(label_file)
            except LabelFileError as e:
                self.errorMessage(
                    self.tr("Error opening file" if self._config['local_lang'] != 'ko_KR' else '레이블 파일 열기중 오류'),
                    self.tr(
                        "<p><b>{}</b></p>"
                        "<p>Make sure <i>{}</i> is a valid label file." if self._config['local_lang'] != 'ko_KR' else '<i>{}</i> 이 유효한 레이블 파일인가를 확인하세요'
                    ).format(e, label_file),
                    # % (e, label_file),
                )
                LogPrint("레이블파일읽기중 %s" % e)
                self.status(
                    self.tr("Error reading {}" if self._config['local_lang'] != 'ko_KR' else '레이블 파일 읽기중 오류').format(
                        label_file))
                return False
            self.imageData = self.labelFile.imageData
            imgpath = label_file
            if imgpath.find("meta/") > -1:
                imgpath = imgpath.replace("meta/", "")
            self.imagePath = osp.join(
                osp.dirname(imgpath),
                self.labelFile.imagePath,
            )
            self.otherData = self.labelFile.otherData
        elif cocofile is True and labelfile is False:
            try:
                ccls = ConvertCoCOLabel(coco_file, label_file)
                label_file = ccls.save()
            except Exception as e:
                LogPrint("coco 파일로 라벨파일변환중 에러 , " + e)
                pass

            if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
                    label_file
            ):
                try:
                    self.labelFile = LabelFile(label_file)
                except LabelFileError as e:
                    self.errorMessage(
                        self.tr("Error opening file" if self._config['local_lang'] != 'ko_KR' else '레이블 열기중 오류'),
                        self.tr(
                            "<p><b>{}</b></p>"
                            "<p>Make sure <i>{}</i> is a valid label file." if self._config['local_lang'] != 'ko_KR' else '<i>{}</i> 이 유효한 레벨파일인가를 확인하세요'
                        ).format(e, label_file),
                        # % (e, label_file),
                    )
                    LogPrint("레이블 파일 읽기중 %s" % e)
                    self.status(
                        self.tr("Error reading {}" if self._config['local_lang'] != 'ko_KR' else '레벨파일 읽기중 오류').format(label_file))
                    return False
                self.imageData = self.labelFile.imageData
                imgpath = label_file
                if imgpath.find("meta/") > -1:
                    imgpath = imgpath.replace("meta/", "")
                self.imagePath = osp.join(
                    osp.dirname(imgpath),
                    self.labelFile.imagePath,
                )
                self.otherData = self.labelFile.otherData
        else:
            self.imageData = LabelFile.load_image_file(filename)
            if self.imageData:
                self.imagePath = filename
            self.labelFile = None

        image = QtGui.QImage.fromData(self.imageData)

        if image.isNull():
            formats = [
                "*.{}".format(fmt.data().decode())
                for fmt in QtGui.QImageReader.supportedImageFormats()
            ]
            ermsg = "<p>Make sure <i>{0}</i> is a valid image file.<br/>" if self._config["local_lang"] != "ko_KR" else "<p><i>{0}</i> 이 유효한 이미지파일인가를 확인하세요<br/>(이미지 이름과 레이블 json 파일에 저장된 이미지 이름이 일치하지 않을수 있습니다)<br/>"
            ermsg += "Supported image formats: {1}</p>" if self._config["local_lang"] != "ko_KR" else "지원하는 이미지 형식: {1}</p>"
            self.errorMessage(
                self.tr("Error opening file" if self._config['local_lang'] != 'ko_KR' else '파일 열기중 오류'),
                ermsg.format(filename, ",".join(formats)),
            )
            LogPrint("레이블파일의 이미지형식 오류")
            self.status(self.tr("Error reading {}" if self._config['local_lang'] != 'ko_KR' else '레이블 파일 읽기중 오류').format(filename))
            return False

        self.image = image
        self.filename = filename
        prev_shapes = None
        if self._config["keep_prev"]:
            prev_shapes = self.canvas.shapes
        self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))

        if self.labelFile:
            self.loadLabels(self.labelFile.shapes)

        if self._config["keep_prev"] and self.noShapes():
            self.loadShapes(prev_shapes, replace=False)
            self.setDirty()
        else:
            self.setClean()
        self.canvas.setEnabled(True)

        # set zoom values
        is_initial_load = not self.zoom_values
        if self.filename in self.zoom_values:
            self.zoomMode = self.zoom_values[self.filename][0]
            self.setZoom(self.zoom_values[self.filename][1])
        elif is_initial_load or not self._config["keep_prev_scale"]:
            self.adjustScale(initial=True)
        # set scroll values
        for orientation in self.scroll_values:
            if self.filename in self.scroll_values[orientation]:
                self.setScroll(
                    orientation, self.scroll_values[orientation][self.filename]
                )
        # set brightness contrast values
        self.brightDialog = BrightnessContrastDialog(
            utils.img_data_to_pil(self.imageData),
            self.onNewBrightnessContrast,
            parent=self,
        )
        self.polygonAlphaDlg = PolygonTransDialog(
            utils.img_data_to_pil(self.imageData),
            self.onNewBrightnessContrast,
            self.polygonTrans,
            self.lineweight,
            parent=self,
        )

        brightness, contrast = self.brightnessContrast_values.get(
            self.filename, (None, None)
        )
        if self._config["keep_prev_brightness"] and self.recentFiles:
            brightness, _ = self.brightnessContrast_values.get(
                self.recentFiles[0], (None, None)
            )
        if self._config["keep_prev_contrast"] and self.recentFiles:
            _, contrast = self.brightnessContrast_values.get(
                self.recentFiles[0], (None, None)
            )
        if brightness is not None:
            self.brightDialog.slider_brightness.setValue(brightness)
            self.polygonAlphaDlg.slider_brightness.setValue(brightness)
        if contrast is not None:
            self.brightDialog.slider_contrast.setValue(contrast)
            self.polygonAlphaDlg.slider_contrast.setValue(contrast)
        self.brightnessContrast_values[self.filename] = (brightness, contrast)
        if brightness is not None or contrast is not None:
            self.brightDialog.onNewValue(None)
            self.polygonAlphaDlg.onNewValue(None)

        self.paintCanvas()
        self.addRecentFile(self.filename)
        self.toggleActions(True)
        self.canvas.setFocus()
        self.status(str(self.tr("Loaded %s")) % osp.basename(str(self.filename)))

        self.togglePolygons(True)  # add ckd
        # add ckd
        ac = self.canvas.drawing()
        if ac:
            # self.toggleDrawMode(False, self.canvas.createMode)  # 이전의 모드로 하자면
            self.toggleDrawMode(True)  # 에디트모드로 강제전환
        return True


    def resizeEvent(self, event):
        if (
            self.canvas
            and not self.image.isNull()
            and self.zoomMode != self.MANUAL_ZOOM
        ):
            self.adjustScale()
        super(MainWindow, self).resizeEvent(event)

    def paintCanvas(self):
        try:
            assert not self.image.isNull(), "cannot paint null image"
            self.canvas.scale = 0.01 * self.zoomWidget.value()
            self.canvas.adjustSize()
            self.canvas.update()
        except Exception as e:
            LogPrint("캔버스에 그릴 이미지가 null 이다 %s" % e)
            pass

    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        value = int(100 * value)
        self.zoomWidget.setValue(value)
        self.zoom_values[self.filename] = (self.zoomMode, value)

    def scaleFitWindow(self):
        """Figure out the size of the pixmap to fit the main widget."""
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ratio.
        if self.canvas:
            w2 = self.canvas.pixmap.width() - 0.0
            h2 = self.canvas.pixmap.height() - 0.0
        else:
            w2 = w1
            h2 = h1
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scaleFitWidth(self):
        # The epsilon does not seem to work too well here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    def enableSaveImageWithData(self, enabled):
        self._config["store_data"] = enabled
        self.actions.saveWithImageData.setChecked(enabled)

    def saveAutoAction(self, enabled):
        self._config["auto_save"] = enabled
        if enabled is False:
            self.actions.saveAuto.setText(self.tr("Save automatically"))
            self.actions.saveAuto.setToolTip(self.tr("Save automatically"))
        else:
            self.actions.saveAuto.setText(self.tr("Turn off Save automatically"))
            self.actions.saveAuto.setToolTip(self.tr("Turn off Save automatically"))
            self.setDirty()  # add 11/02/2022

        self.actions.save.setEnabled(not enabled)  # add 11/02/2022
        self.actions.saveAuto.setChecked(enabled)

    def EndSavaingFile(self):
        self.saveTimer = threading.Timer(1, self.EndSavaingFile)
        #self.showErrMessageBox = self.errorMessage("알림", "파일 저장 중입니다.")
        self.saveTimer.start()
        if self.isSaving is False:
            self.saveTimer.cancel()
            LogPrint("%s 파일 저장 완료되었습니다!" % self.labelFile.filename if self.labelFile.filename is not None else self.filename)
            self.showErrMessageBox.label.setText(" 저장 완료되었습니다! ")
            self.showErrMessageBox._isEnd = True


    def closeEvent(self, event):
        try:
            if not self.mayContinue():
                event.ignore()
            if self.isSaving is True and self.forceExit is False:
                event.ignore()
                #self.endSavaingFile()
                LogPrint("%s 파일 저장 중입니다!" % self.labelFile.filename if self.labelFile.filename is not None else self.filename)
                self.showErrMessageBox = FileSaveDelayProgress(parent=self)
                self.showErrMessageBox.show()
                self.EndSavaingFile()
                return
            if self.isSaving is True and self.forceExit is True:
                if(self.saveTimer.is_alive()):
                    self.saveTimer.cancel()
                LogPrint("%s 파일 저장 중 강제 종료되였습니다!" % self.labelFile.filename if self.labelFile.filename is not None else self.filename)



            self.settings.setValue(
                "filename", self.filename if self.filename else ""
            )
            self.settings.setValue("window/size", self.size())
            self.settings.setValue("window/position", self.pos())
            self.settings.setValue("window/state", self.saveState())
            self.settings.setValue("recentFiles", self.recentFiles)
            # ask the use for where to save the labels
            # self.settings.setValue('window/geometry', self.saveGeometry())

            self.labelList.clear()
            self._itemList.clear()
            self._polyonList.clear()
            ##threading.Timer(0.01, self.deConnetNetDriver).start()
            self.deConnetNetDriver()
        except Exception as e:
            LogPrint("Error in closeEvent %s" % e)
            pass

    def dragEnterEvent(self, event):
        try:
            extensions = [
                ".%s" % fmt.data().decode().lower()
                for fmt in QtGui.QImageReader.supportedImageFormats()
            ]
            if event.mimeData().hasUrls():
                items = [i.toLocalFile() for i in event.mimeData().urls()]
                if any([i.lower().endswith(tuple(extensions)) for i in items]):
                    event.accept()
            else:
                event.ignore()
        except Exception as e:
            LogPrint("Error in dragEnterEvent %s" % e)
            pass

    def dropEvent(self, event):
        try:
            if not self.mayContinue():
                event.ignore()
                return
            items = [i.toLocalFile() for i in event.mimeData().urls()]
            self.importDroppedImageFiles(items)
        except Exception as e:
            LogPrint("Error in dropEvent %s" % e)
            pass
    # User Dialogs #

    def loadRecent(self, filename):
        try:
            if self.mayContinue():
                self.loadFile(filename)
        except Exception as e:
            LogPrint("Error in loadRecent %s" % e)
            pass

    def openPrevImg(self, _value=False):
        try:
            keep_prev = self._config["keep_prev"]
            if QtWidgets.QApplication.keyboardModifiers() == (
                Qt.ControlModifier | Qt.ShiftModifier
            ):
                self._config["keep_prev"] = True

            if not self.mayContinue():
                return

            if len(self.imageList) <= 0:
                return

            if self.filename is None:
                return

            currIndex = self.imageList.index(self.filename)
            if currIndex - 1 >= 0:
                filename = self.imageList[currIndex - 1]
                if filename:
                    self.loadFile(filename)

            self._config["keep_prev"] = keep_prev
        except Exception as e:
            LogPrint("Error in openPrevImg %s" % e)
            pass

    def openNextImg(self, _value=False, load=True):
        try:
            keep_prev = self._config["keep_prev"]
            if QtWidgets.QApplication.keyboardModifiers() == (
                Qt.ControlModifier | Qt.ShiftModifier
            ):
                self._config["keep_prev"] = True

            if not self.mayContinue():
                return

            if len(self.imageList) <= 0:
                return

            filename = None
            if self.filename is None:
                filename = self.imageList[0]
            else:
                currIndex = self.imageList.index(self.filename)
                if currIndex + 1 < len(self.imageList):
                    filename = self.imageList[currIndex + 1]
                else:
                    filename = self.imageList[-1]
            self.filename = filename

            if self.filename and load:
                self.loadFile(self.filename)

            self._config["keep_prev"] = keep_prev
        except Exception as e:
            LogPrint("Error in openNextImg %s" % e)
            pass

    def openFile(self, _value=False):
        try:
            if not self.mayContinue():
                return
            path = osp.dirname(str(self.filename)) if self.filename else "."
            formats = [
                "*.{}".format(fmt.data().decode())
                for fmt in QtGui.QImageReader.supportedImageFormats()
            ]
            # filters = self.tr("Image & Label files (%s)") % " ".join(
            #     formats + ["*%s" % LabelFile.suffix]
            # )
            stt = "Image (%s)" if self._config['local_lang'] != 'ko_KR' else "이미지 (%s)"
            filters = stt % " ".join(
                formats
            )

            fileDialog = FileDialogPreview(self)
            fileDialog.setFileMode(FileDialogPreview.ExistingFile)
            fileDialog.setNameFilter(filters)
            fileDialog.setWindowTitle(
                self.tr("%s - Choose Image or Label file") % __appname__,
            )
            fileDialog.setWindowFilePath(path)
            fileDialog.setViewMode(FileDialogPreview.Detail)
            if fileDialog.exec_():
                fileName = fileDialog.selectedFiles()[0]
                if fileName:
                    self.loadFile(fileName)
        except Exception as e:
            LogPrint("Error in openFile %s" % e)
            pass

    def changeOutputDirDialog(self, _value=False):
        try:
            default_output_dir = self.output_dir
            if default_output_dir is None and self.filename:
                default_output_dir = osp.dirname(self.filename)
            if default_output_dir is None:
                default_output_dir = self.currentPath()

            output_dir = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                self.tr("%s - Save/Load Annotations in Directory") % __appname__,
                default_output_dir,
                QtWidgets.QFileDialog.ShowDirsOnly
                | QtWidgets.QFileDialog.DontResolveSymlinks,
            )
            output_dir = str(output_dir)

            if not output_dir:
                return

            self.output_dir = output_dir

            self.statusBar().showMessage(
                self.tr("%s . Annotations will be saved/loaded in %s")
                % ("Change Annotations Dir", self.output_dir)
            )
            self.statusBar().show()

            current_filename = self.filename
            self.importDirImages(self.lastOpenDir, load=False)

            if current_filename in self.imageList:
                # retain currently selected file
                self.fileListWidget.setCurrentRow(
                    self.imageList.index(current_filename)
                )
                self.fileListWidget.repaint()
        except Exception as e:
            LogPrint("Error in changeOutputDirDialog %s" % e)
            pass

    def saveFile(self, _value=False):
        try:
            assert not self.image.isNull(), "cannot save empty image"
            if self.labelFile:
                # DL20180323 - overwrite when in directory
                filename = self.labelFile.filename
                if self.labelFile.filename.find("meta/") > -1:
                    filename = self.labelFile.filename.replace("meta/", "")  # add ckd
                self._saveFile(filename)
            elif self.output_file:
                self._saveFile(self.output_file)
                self.close()
            else:
                #self._saveFile(self.saveFileDialog())
                assert len(self.filename) > 3, "cannot save empty file"
                basename = osp.basename(osp.splitext(self.filename)[0])
                filename = osp.join(
                    self.currentPath(), basename + LabelFile.suffix
                )
                if isinstance(filename, tuple):
                    filename, _ = filename

                if filename.find("meta/") > -1:
                    filename = filename.replace("meta/", "")  # add ckd
                self._saveFile(filename)

            # add ckd 보관후에 되돌이막기
            saveShapes = self.canvas.shapes  
            self.canvas.shapes = []
            self.canvas.shapesBackups = []
            self.canvas.loadShapes(saveShapes, True)
            self.actions.undo.setEnabled(self.canvas.isShapeRestorable)
            # add ckd
        except Exception as e:
            LogPrint("Error in saveFile :: %s" % e)
            pass


    def saveFileAs(self, _value=False):
        try:
            assert not self.image.isNull(), "cannot save empty image"
            self._saveFile(self.saveFileDialog())
        except Exception as e:
            LogPrint("Error in saveFileAs :: %s" % e)
            pass

    def saveFileDialog(self):
        caption = self.tr("%s - Choose File") % __appname__
        filters = self.tr("Label files (*%s)") % LabelFile.suffix
        if self.output_dir:
            dlg = QtWidgets.QFileDialog(
                self, caption, self.output_dir, filters
            )
        else:
            dlg = QtWidgets.QFileDialog(
                self, caption, self.currentPath(), filters
            )
        dlg.setDefaultSuffix(LabelFile.suffix[1:])
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dlg.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite, False)
        dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, False)
        basename = osp.basename(osp.splitext(self.filename)[0])
        if self.output_dir:
            default_labelfile_name = osp.join(
                self.output_dir, basename + LabelFile.suffix
            )
        else:
            default_labelfile_name = osp.join(
                self.currentPath(), basename + LabelFile.suffix
            )
        filename = dlg.getSaveFileName(
            self,
            self.tr("Choose File"),
            default_labelfile_name,
            self.tr("Label files (*%s)") % LabelFile.suffix,
        )
        if isinstance(filename, tuple):
            filename, _ = filename
        return filename

    def _saveFile(self, filename):
        try:
            self.isSaving = True

            if filename and self.saveLabels(filename):
                if filename.find("meta") < 0:
                    meta_dir = osp.dirname(filename) + "/meta"
                    filename = meta_dir + '/' + osp.basename(filename)
                self.addRecentFile(filename)
                self.setClean()
                # run coco format
                threading.Timer(0.1, self.putDownCocoFormat, [filename]).start()
        except Exception as e:
            self.isSaving = False
            LogPrint("Error in _saveFile :: %s" % e)
            pass

    def putDownCocoFormat(self, arg):
        if arg is None:
            self.isSaving = False
            return
        # put to coco format
        cf = ""
        try:
            labelmefiles = []
            labelmefiles.append(arg)
            basename = os.path.basename(arg)
            coco_fname = os.path.splitext(basename)[0]
            dirname = os.path.dirname(arg)
            cocofp = "{}/{}_coco.{}".format(dirname, coco_fname, "json")
            if osp.dirname(cocofp) and not osp.exists(osp.dirname(cocofp)):
                os.makedirs(osp.dirname(cocofp))

            labelme2coco(labelmefiles, cocofp, self._itemList)
            self.isSaving = False
            #print("Success save coco json")
        except LabelFileError as e:
            self.isSaving = False
            LogPrint("라벨미파일을 코코파일로 보관중 에러 :: %s" % e)
            self.errorMessage(
                self.tr("Error creating coco file"),
                self.tr(
                    "<p><b>%s</b></p>"
                    "<p>Make sure <i>%s</i> is a valid label file."
                )
                % (e, cf),
            )


    def closeFile(self, _value=False):
        if not self.mayContinue():
            return
        self.resetState()
        self._itemList.clear()

        self.setClean()
        self.toggleActions(False)
        self.canvas.setEnabled(False)
        ##self.actions.saveAs.setEnabled(False)

        self.topToolWidget.editmodeClick(False)
        self.polygonTrans_value = 0
        try:
            if self.polygonAlphaDlg is not None:
                self.polygonAlphaDlg.label.setText("100%")
                self.polygonAlphaDlg.label_line.setText("2.0")
            self.polygonAlphaDlg = None
        except AttributeError as e:
            LogPrint("Error in closeFile :: %s" % e)
            pass


    def getLabelFile(self):
        if self.filename.lower().endswith(".json"):
            label_file = self.filename
        else:
            label_file = osp.splitext(self.filename)[0] + ".json"
        return label_file

    def deleteFile(self):
        try:
            mb = QtWidgets.QMessageBox
            msg = self.tr(
                "You are about to permanently delete this label file, "
                "proceed anyway?"
            )
            answer = mb.warning(self, self.tr("Attention"), msg, mb.Yes | mb.No)
            if answer != mb.Yes:
                return

            label_file = self.getLabelFile()
            if osp.exists(label_file):
                os.remove(label_file)
                logger.info("Label file is removed: {}".format(label_file))
            # delete coco file > add ckd
                basename = os.path.basename(label_file)
                coco_fname = os.path.splitext(basename)[0]
                dirname = os.path.dirname(label_file)
                cocofp = "{}/{}_coco.{}".format(dirname, coco_fname, "json")
                if osp.exists(cocofp):
                    os.remove(cocofp)

                item = self.fileListWidget.currentItem()
                if item:
                    item.setCheckState(Qt.Unchecked)
                self.resetState()
                self._itemList.clear()
        except Exception as e:
            LogPrint("Error in deleteFile :: %s" % e)
            pass

    # Message Dialogs.
    def hasLabels(self):
        if self.noShapes():
            self.errorMessage(
                "No objects labeled",
                "You must label at least one object to save the file.",
            )
            return False
        return True

    def hasLabelFile(self):
        if self.filename is None:
            return False

        label_file = self.getLabelFile()
        return osp.exists(label_file)

    def mayContinue(self):
        try:
            if not self.dirty:
                return True
            mb = QtWidgets.QMessageBox
            msgstr = 'Save annotations to "{}" before closing?' if self._config['local_lang'] != 'ko_KR' else '닫기전에 "{}" 을 보관하시겠습니까?'
            msg = msgstr.format(
                self.filename
            )
            answer = mb.question(
                self,
                "Save annotations?" if self._config['local_lang'] != 'ko_KR' else '주석 저장?',
                msg,
                mb.Save | mb.Discard | mb.Cancel,
                mb.Save,
            )
            if answer == mb.Discard:
                return True
            elif answer == mb.Save:
                self.saveFile()
                return True
            else:  # answer == mb.Cancel
                return False
        except Exception as e:
            LogPrint("Err in mayContinue :: %s" % e)
            pass
        return False

    def errorMessage(self, title, message):
        return QtWidgets.QMessageBox.critical(
            self, title, "<p><b>%s</b></p>%s" % (title, message)
        )

    def currentPath(self):
        return osp.dirname(str(self.filename)) if self.filename else "."

    def toggleKeepPrevMode(self):
        self._config["keep_prev"] = not self._config["keep_prev"]

    def removeSelectedPoint(self):
        try:
            self.canvas.removeSelectedPoint()
            self.canvas.update()
            if not self.canvas.hShape.points:
                self.canvas.deleteShape(self.canvas.hShape)
                self.remLabels([self.canvas.hShape])
                polyT = "Polygon Labels (Total %s)"
                if self._config["local_lang"] == "ko_KR":
                    polyT = "다각형 레이블 (총 %s)"
                if self.shape_dock:
                    self.shape_dock.titleBarWidget().titleLabel.setText(polyT % len(self.labelList))

                self.setDirty()
                if self.noShapes():
                    for action in self.actions.onShapesPresent:
                        action.setEnabled(False)
        except Exception as e:
            LogPrint("Error in removeSelectedPoint :: %s" % e)
            pass



    def deleteSelectedShape(self):
        try:
            yes, no = QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No
            msg = self.tr(
                "You are about to permanently delete {} polygons, "
                "proceed anyway?"
            ).format(len(self.canvas.selectedShapes))
            if yes == QtWidgets.QMessageBox.warning(
                    self, self.tr("Attention"), msg, yes | no, yes
            ):
                self.remLabels(self.canvas.deleteSelected())

                polyT = "Polygon Labels (Total %s)"
                if self._config["local_lang"] == "ko_KR":
                    polyT = "다각형 레이블 (총 %s)"
                if self.shape_dock:
                    self.shape_dock.titleBarWidget().titleLabel.setText(polyT % len(self.labelList))

                self.setDirty()
                if self.noShapes():
                    for action in self.actions.onShapesPresent:
                        action.setEnabled(False)
        except Exception as e:
            LogPrint("Error in deleteSelectedShape :: %s" % e)
            pass


    def copyShape(self):
        try:
            self.canvas.endMove(copy=True)
            for shape in self.canvas.selectedShapes:
                self.addLabel(shape)
            self.labelList.clearSelection()
            self.setDirty()
        except Exception as e:
            LogPrint("Error in copyShape :: %s" % e)
            pass


    def moveShape(self):
        try:
            self.canvas.endMove(copy=False)
            self.setDirty()
        except Exception as e:
            LogPrint("Error in moveShape :: %s" % e)
            pass

    def openDirDialog(self, _value=False, dirpath=None):
        if not self.mayContinue():
            return

        defaultOpenDirPath = dirpath if dirpath else "."
        if self.lastOpenDir and osp.exists(self.lastOpenDir):
            defaultOpenDirPath = self.lastOpenDir
        else:
            defaultOpenDirPath = (
                osp.dirname(self.filename) if self.filename else "."
            )

        targetDirPath = str(
            QtWidgets.QFileDialog.getExistingDirectory(
                self,
                self.tr("%s - Open Directory") % __appname__,
                defaultOpenDirPath,
                QtWidgets.QFileDialog.ShowDirsOnly
                | QtWidgets.QFileDialog.DontResolveSymlinks,
            )
        )
        self.importDirImages(targetDirPath)

    @property
    def imageList(self):
        lst = []
        for i in range(self.fileListWidget.count()):
            item = self.fileListWidget.item(i)
            lst.append(item.text())
        return lst

    def importDroppedImageFiles(self, imagefiles):
        try:
            extensions = [
                ".%s" % fmt.data().decode().lower()
                for fmt in QtGui.QImageReader.supportedImageFormats()
            ]

            self.filename = None
            for file in imagefiles:
                if file in self.imageList or not file.lower().endswith(
                    tuple(extensions)
                ):
                    continue
                #label_file = osp.splitext(file)[0] + ".json"
                label_file = osp.splitext(file)[0]
                if label_file.find("meta") < 0:
                    label_file = osp.dirname(label_file) + "/meta/" + osp.basename(label_file) + ".json"
                else:
                    label_file = osp.splitext(filename)[0] + ".json"

                if self.output_dir:
                    label_file_without_path = osp.basename(label_file)
                    label_file = osp.join(self.output_dir, label_file_without_path)
                item = QtWidgets.QListWidgetItem(file)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
                    label_file
                ):
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                self.fileListWidget.addItem(item)

            if len(self.imageList) > 1:
                self.actions.openNextImg.setEnabled(True)
                self.actions.openPrevImg.setEnabled(True)
        except Exception as e:
            LogPrint("Error in importDroppedImageFiles :: %s" % e)

        self.openNextImg()
        flistname = "File List (Total {})".format(self.fileListWidget.count()) if self._config["local_lang"] != "ko_KR" else "파일 목록 (총 {})".format(self.fileListWidget.count())
        self.file_dock.setWindowTitle(flistname)

    def importDirImages(self, dirpath, pattern=None, load=True):
        self.actions.openNextImg.setEnabled(True)
        self.actions.openPrevImg.setEnabled(True)

        if not self.mayContinue() or not dirpath:
            return

        self.lastOpenDir = dirpath
        self.filename = None
        self.fileListWidget.clear()
        for filename in self.scanAllImages(dirpath):
            if pattern and pattern not in filename:
                continue

            label_file = osp.splitext(filename)[0]
            if label_file.find("meta") < 0:
                label_file = osp.dirname(label_file) + "/meta/" + osp.basename(label_file) + ".json"
            else:
                label_file = osp.splitext(filename)[0] + ".json"

            coco_file = osp.splitext(filename)[0]
            if coco_file.find("meta") < 0:
                coco_file = osp.dirname(coco_file) + "/meta/" + osp.basename(coco_file) + "_coco.json"
            else:
                coco_file = osp.splitext(filename)[0] + "_coco.json"

            cocofile = False
            if QtCore.QFile.exists(coco_file) and ConvertCoCOLabel.is_coco_file(
                    coco_file
            ):
                cocofile = True

            if self.output_dir:
                label_file_without_path = osp.basename(label_file)
                label_file = osp.join(self.output_dir, label_file_without_path)
            item = QtWidgets.QListWidgetItem(filename)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

            if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
                label_file
            ):
                item.setCheckState(Qt.Checked)
            else:
                if cocofile is True:
                    try:
                        ccls = ConvertCoCOLabel(coco_file, label_file)
                        label_file = ccls.save()
                    except Exception as e:
                        LogPrint("coco 파일로 라벨파일 변환중 에러 , " + e)
                        pass

                if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
                        label_file
                ):
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)

            self.fileListWidget.addItem(item)

        self.openNextImg(load=load)
        # print("{}".format(self.fileListWidget.count()))
        flistname = "File List (Total {})".format(self.fileListWidget.count()) if self._config["local_lang"] != "ko_KR" else "파일 목록 (총 {})".format(self.fileListWidget.count())
        self.file_dock.setWindowTitle(flistname)

    def scanAllImages(self, folderPath):
        extensions = [
            ".%s" % fmt.data().decode().lower()
            for fmt in QtGui.QImageReader.supportedImageFormats()
        ]

        images = []
        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relativePath = osp.join(root, file)
                    images.append(relativePath)
        images = natsort.os_sorted(images)
        return images

    def gradeButtonEvent(self, arg):
        self.grade_title_bar.hidnBtn.clicked.emit()

    # send new grade
    def sendGradeToServer(self, item, items, callback):
        url = self._config['api_url'] + 'ords/lm/v1/labelme/codes/grades'
        headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
        data = {'user_id': self._config['user_id'], 'grade': item}
        jsstr = httpReq(url, "post", headers, data)
        if jsstr['message'] == 'success':
            callback(items)  # called addItemsToQHBox
        else:
            return QtWidgets.QMessageBox.critical(
                self, "Error", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
            )

    # send new product
    def sendProductToServer(self, pstr, callback):
        url = self._config["api_url"] + 'ords/lm/v1/labelme/codes/products'
        headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
        data = {'user_id': self._config['user_id'], 'grade': self.selected_grade, 'product': pstr}
        jsstr = httpReq(url, "post", headers, data)
        if jsstr['message'] == 'success':
            callback(pstr)  # called addItemsToQHBox
        else:
            return QtWidgets.QMessageBox.critical(
                self, "Error", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
            )

    def receiveProductsFromServerByGrade(self):
        try:
            if self.selected_grade:
                # print(self.selected_grade)
                url = self._config["api_url"] + 'ords/lm/v1/labelme/codes/products?grade=' + self.selected_grade
                headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
                jsstr = httpReq(url, "get", headers)
                if jsstr['message'] == 'success':
                    items = jsstr['items']
                    # print("products is ", items)
                    if items and len(items) > 0:
                        self.loadProducts(items)
                    else:
                        temp = [{"product": "미정"}]
                        self.loadProducts(temp)

                else:
                    return QtWidgets.QMessageBox.critical(
                        self, "Error", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
                    )
        except Exception as e:
            LogPrint("Error in receiveProductsFromServerByGrade :: %s" % e)
            pass

    def receiveLabelsFromServerByGrade(self):
        if self.selected_grade:
            # print(self.selected_grade)
            url = self._config["api_url"] + 'ords/lm/v1/labelme/codes/labels?grade=' + self.selected_grade
            headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
            jsstr = httpReq(url, "get", headers)
            if jsstr['message'] == 'success':
                items = jsstr['items']
                try:
                    if self._polyonList is not None:
                        self._polyonList.clear()
                    else:
                        self._polyonList = []

                    if items and len(items) > 0:
                        self._polyonList = items

                        if self.labelDialog.actived is True:
                            self.labelDialog._list_items.clear()
                            self.labelDialog._list_items = items[:]
                            self.labelDialog.labelList.clear()
                            self.labelDialog.labelList.addItems(items)
                    else:
                        temp = [{
                            "label_display": "미정-미정",
                            "label": "미정",
                            "grade": "미정",
                            "color": "#ff0000"
                        }]
                        self._polyonList = temp

                except AttributeError as e:
                    LogPrint("Error in receiveLabelsFromServerByGrade :: %s" % e)
                    pass
            else:
                return QtWidgets.QMessageBox.critical(
                    self, "Error", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
                )

    def receiveGradesFromServer(self):
        try:
            url = self._config["api_url"] + 'ords/lm/v1/labelme/codes/grades'
            headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
            jsstr = httpReq(url, "get", headers)
            if jsstr['message'] == 'success':
                self.grades_widget.set(jsstr['items'])
                self.labelDialog.addGrades(jsstr['items'])
            else:
                return QtWidgets.QMessageBox.critical(
                    self, "Error", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
                )
        except Exception as e:
            LogPrint("Error in receiveGradesFromServer :: %s" % e)
            pass

    # This function be not used now
    def receiveProductsFromServer(self):
        try:
            url = self._config["api_url"] + 'ords/lm/v1/labelme/codes/products'
            headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
            jsstr = httpReq(url, "get", headers)
            if jsstr['message'] == 'success':
                items = jsstr['items']
                # print("All products is ", items)
                if items and len(items) > 0:
                    self.loadProducts(items)
                else:
                    temp = [{"product": "미정"}]
                    self.loadProducts(temp)
            else:
                return QtWidgets.QMessageBox.critical(
                    self, "Error", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
                )
        except Exception as e:
            LogPrint("Error in receiveProductsFromServer :: %s" % e)
            pass