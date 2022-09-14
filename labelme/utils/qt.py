from math import sqrt
import os.path as osp
import time
import numpy as np
import requests, json

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy.QtGui import QFontDatabase
from requests import RequestException
from urllib3 import Timeout
from urllib3.exceptions import ProxyError

here = osp.dirname(osp.abspath(__file__))
font_dir = osp.join(here, "../font")


def newLang(lang: str):
    trans_dir = osp.join(here, "../translate")
    return osp.join(":/", trans_dir, "%s.qm" % lang)


def appFont(fontname: str = None):
    if fontname is not None:
        fontid = QFontDatabase.addApplicationFont(osp.join(":/", font_dir, "%s.ttf" % fontname))
    else:
        fontid = QFontDatabase.addApplicationFont(osp.join(":/", font_dir, "NanumGothic - Regular.ttf"))
    ffamile = QFontDatabase.applicationFontFamilies(fontid)
    if fontid > -1:
        return QtGui.QFont(ffamile[0], 10, QtGui.QFont.Normal)
    else:
        return QtGui.QFont("맑은 고딕", 10, QtGui.QFont.Normal)


def newIcon(icon):
    icons_dir = osp.join(here, "../icons")
    return QtGui.QIcon(osp.join(":/", icons_dir, "%s.png" % icon))


def urlIcon(icon):
    icons_dir = osp.join(here, "../icons")
    return osp.join(":/", icons_dir, "%s.png" % icon)


def newButton(text, icon=None, slot=None):
    b = QtWidgets.QPushButton(text)
    if icon is not None:
        b.setIcon(newIcon(icon))
    if slot is not None:
        b.clicked.connect(slot)
    return b


def newAction(
    parent,
    text,
    slot=None,
    shortcut=None,
    icon=None,
    tip=None,
    checkable=False,
    enabled=True,
    checked=False,
):
    """Create a new action and assign callbacks, shortcuts, etc."""
    a = QtWidgets.QAction(text, parent)
    if icon is not None:
        a.setIconText(text.replace(" ", "\n"))
        a.setIcon(newIcon(icon))
    if shortcut is not None:
        if isinstance(shortcut, (list, tuple)):
            a.setShortcuts(shortcut)
        else:
            a.setShortcut(shortcut)
    if tip is not None:
        a.setToolTip(tip)
        a.setStatusTip(tip)
    if slot is not None:
        a.triggered.connect(slot)
    if checkable:
        a.setCheckable(True)
    a.setEnabled(enabled)
    a.setChecked(checked)
    return a


def addActions(widget, actions):
    for action in actions:
        if action is None:
            widget.addSeparator()
        elif isinstance(action, QtWidgets.QMenu):
            widget.addMenu(action)
        else:
            widget.addAction(action)


def labelValidator():
    return QtGui.QRegExpValidator(QtCore.QRegExp(r"^[^ \t].+"), None)


class struct(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def distance(p):
    return sqrt(p.x() * p.x() + p.y() * p.y())


def distancetoline(point, line):
    p1, p2 = line
    p1 = np.array([p1.x(), p1.y()])
    p2 = np.array([p2.x(), p2.y()])
    p3 = np.array([point.x(), point.y()])
    if np.dot((p3 - p1), (p2 - p1)) < 0:
        return np.linalg.norm(p3 - p1)
    if np.dot((p3 - p2), (p1 - p2)) < 0:
        return np.linalg.norm(p3 - p2)
    if np.linalg.norm(p2 - p1) == 0:
        return 0
    return np.linalg.norm(np.cross(p2 - p1, p1 - p3)) / np.linalg.norm(p2 - p1)


def fmtShortcut(text):
    mod, key = text.split("+", 1)
    return "<b>%s</b>+<b>%s</b>" % (mod, key)


def LogPrint(error: str):
    current_time = time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time()))
    with open("Log.txt", "a") as f:
        f.write(f"[{current_time}] - {error}\n")


def httpReq(url, method, headers=None, data=None, param=None):
    try:
        if method == "get":
            if headers is not None and data is None:  # 1 0
                respone = requests.get(url, headers=headers)
            elif headers is not None and data is not None:  # 1 1
                respone = requests.get(url, headers=headers, json=data)
            elif headers is None and data is not None:  # 0 1
                respone = requests.get(url, json=data)
            else:
                respone = requests.get(url)  # 0 0
        else:
            if headers is not None and data is None:  # 1 0
                respone = requests.post(url, headers=headers)
            elif headers is not None and data is not None:  # 1 1
                respone = requests.post(url, headers=headers, json=data)
            elif headers is None and data is not None:  # 0 1
                respone = requests.post(url, json=data)
            else:
                respone = requests.post(url)  # 0 0
        jsstr = respone.json()
        return jsstr
    # except ProxyError as e:
    #     jsstr = 'ProxyError when try to get %s' % e.args
    except Exception as e:
        jsstr = 'Exception when try to get %s' % e.args

    return {"message": jsstr}