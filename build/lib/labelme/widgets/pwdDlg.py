import threading

from PyQt5.QtWidgets import QDesktopWidget, QWidget
from qtpy import QtWidgets
from qtpy.QtCore import Qt
from qtpy import QtGui, QtCore
from labelme.utils.qt import httpReq
from labelme.utils import newIcon
from labelme.utils import appFont


class PwdDLG(QtWidgets.QDialog):

    def __init__(
            self,
            config=None,
            parent=None
    ):
        super(PwdDLG, self).__init__(parent)
        self._config = config
        self._app = parent
        self._sms = False
        self.setFont(appFont())

        self.initUI()

    def initUI(self):
        v_mainlayout = QtWidgets.QVBoxLayout()
        v_mainlayout.setContentsMargins(40, 20, 40, 20)
        v_mainlayout.setSpacing(10)
        self.setLayout(v_mainlayout)
        self.setWindowTitle(self.tr('Change Password'))
        self.setWindowIcon(newIcon("chg_pwd"))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        # self.setWindowFlag(QtCore.Qt.WindowType.WindowContextHelpButtonHint | QtCore.Qt.WindowType.WindowCloseButtonHint)
        self.setFixedSize(400, 300)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        name_layout = QtWidgets.QHBoxLayout()
        pwd_layout = QtWidgets.QHBoxLayout()
        new_layout = QtWidgets.QHBoxLayout()
        verify_layout = QtWidgets.QHBoxLayout()
        btn_layout = QtWidgets.QHBoxLayout()
        alram_layout = QtWidgets.QHBoxLayout()

        v_mainlayout.addLayout(name_layout)
        v_mainlayout.addLayout(pwd_layout)
        v_mainlayout.addLayout(new_layout)
        v_mainlayout.addLayout(verify_layout)
        v_mainlayout.addLayout(alram_layout)
        v_mainlayout.addLayout(btn_layout)

        lb_name = QtWidgets.QLabel(self.tr('Name'))

        self._name_edit = QtWidgets.QLineEdit()

        self._name_edit.setFixedWidth(200)
        self._name_edit.setFixedHeight(25)
        self._name_edit.setStyleSheet("QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 6px}")
        name_layout.addWidget(lb_name)
        name_layout.addWidget(self._name_edit)
        #id_layout.setSpacing(10)

        lb_pwd = QtWidgets.QLabel(self.tr('Current pasword'))

        self._lb_pwd_edit = QtWidgets.QLineEdit()

        self._lb_pwd_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self._lb_pwd_edit.setFixedWidth(200)
        self._lb_pwd_edit.setFixedHeight(25)
        self._lb_pwd_edit.setStyleSheet("QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 6px}")
        pwd_layout.addWidget(lb_pwd)
        pwd_layout.addWidget(self._lb_pwd_edit)
        pwd_layout.setContentsMargins(0, 5, 0, 0)

        lb_newpwd = QtWidgets.QLabel(self.tr('New pasword'))

        self._newpwd_edit = QtWidgets.QLineEdit()

        self._newpwd_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self._newpwd_edit.setFixedWidth(200)
        self._newpwd_edit.setFixedHeight(25)
        self._newpwd_edit.setStyleSheet("QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 6px}")
        new_layout.addWidget(lb_newpwd)
        new_layout.addWidget(self._newpwd_edit)
        new_layout.setContentsMargins(0, 5, 0, 0)

        lb_verify = QtWidgets.QLabel(self.tr('verify pasword'))

        self._verify_edit = QtWidgets.QLineEdit()

        self._verify_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self._verify_edit.setFixedWidth(200)
        self._verify_edit.setFixedHeight(25)
        self._verify_edit.setStyleSheet("QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 6px}")
        verify_layout.addWidget(lb_verify)
        verify_layout.addWidget(self._verify_edit)
        verify_layout.setContentsMargins(0, 5, 0, 0)

        self._lb_alram = QtWidgets.QLabel('')

        self._lb_alram.setStyleSheet("QLabel { color : red; }")
        self._lb_alram.setFixedHeight(18)
        alram_layout.addWidget(self._lb_alram)

        btn_change = QtWidgets.QPushButton(self.tr('Change'))

        btn_change.setFixedWidth(150)
        btn_change.setFixedHeight(30)
        btn_change.setStyleSheet("QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 3px; color:white;background-color: #043966; font-size: 13px}")
        btn_change.clicked.connect(self.changeAction)

        btn_cancle = QtWidgets.QPushButton(self.tr('Cancel'))

        btn_cancle.setFixedWidth(150)
        btn_cancle.setFixedHeight(30)
        btn_cancle.setStyleSheet(
            "QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 3px; color:white;background-color: #043966; font-size: 13px}")
        btn_cancle.clicked.connect(self.reject)

        btn_layout.addWidget(btn_change)
        btn_layout.addSpacing(20)
        btn_layout.addWidget(btn_cancle)
        btn_layout.setContentsMargins(0, 5, 0, 5)


    def popUpDlg(self):

        self._name_edit.setText("")
        self._lb_pwd_edit.setText("")
        self._newpwd_edit.setText("")
        self._verify_edit.setText("")
        self._lb_alram.setText("")
        self._sms = False

        if self.exec_():
            if self._sms is True:
                return True
        else:
            return False

    # noinspection PyUnresolvedReferences
    def changeAction_test(self):
        url = 'https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/ords/lm/v1/labelme/accounts/demo'
        headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
        data = {
                "user_id": "demo",
                "password_old": "demo1234!@",
                "password_new": "demo1234!"
               }
        jsstr = httpReq(url, "post", headers=headers, data=data)
        if jsstr['message'] == 'success':
            self._sms = True
            self.accept()
        else:
            self._lb_alram.setText("%s" % jsstr['message'])
            threading.Timer(5, self.showErrorText).start()

    def changeAction(self):
        self._lb_alram.setStyleSheet("QLabel { color : red; }")
        user_id = self._config["user_id"]
        name = self._name_edit.text().strip()
        if user_id != name:
            self._lb_alram.setText(self.tr("The user name is not correct."))
            threading.Timer(3, self.showErrorText).start()
        elif self._lb_pwd_edit.text().strip() == "":
            self._lb_alram.setText(self.tr("Please enter your current password."))
            threading.Timer(3, self.showErrorText).start()
        elif self._newpwd_edit.text().strip() != self._verify_edit.text().strip() or self._newpwd_edit.text().strip() == "":
            self._lb_alram.setText(self.tr("The password is not correct."))
            threading.Timer(3, self.showErrorText).start()
        else:
            url = 'https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/ords/lm/v1/labelme/accounts/%s' % name
            headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
            data = {
                    "user_id": name,
                    "password_old": self._lb_pwd_edit.text().strip(),
                    "password_new": self._newpwd_edit.text().strip()
                   }
            jsstr = httpReq(url, "post", headers=headers, data=data)
            if jsstr['message'] == 'success':
                self._sms = True
                self._lb_alram.setStyleSheet("QLabel { color : #03ef62; }")
                self._lb_alram.setText(self.tr("The password be changed successfully."))
                threading.Timer(3, self.showErrorText).start()
                self.accept()
            else:
                self._lb_alram.setText("%s" % jsstr['message'])
                threading.Timer(5, self.showErrorText).start()

    def showErrorText(self):
        self._lb_alram.setText("")
