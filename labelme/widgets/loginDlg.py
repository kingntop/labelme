import threading

from PyQt5.QtWidgets import QDesktopWidget, QWidget
from qtpy import QtWidgets
from qtpy import QtGui, QtCore
from qtpy.QtCore import Qt
from labelme.utils.qt import httpReq
from labelme.utils import newIcon
from labelme.utils import appFont
from labelme.utils.qt import LogPrint


class LoginDLG(QWidget):

    def __init__(
            self,
            config=None
    ):
        super().__init__()
        self._config = config
        self.initUI()

    def initUI(self):
        self.setFont(appFont())
        v_mainlayout = QtWidgets.QVBoxLayout()
        v_mainlayout.setContentsMargins(40, 15, 40, 30)
        v_mainlayout.setSpacing(10)
        self.setLayout(v_mainlayout)
        self.setWindowTitle(self.tr('User Login'))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # self.setGeometry(300, 300, 200, 150)
        #self.resize(400, 300)
        self.setFixedSize(400, 300)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        t_hlayout = QtWidgets.QHBoxLayout()
        v_mainlayout.addLayout(t_hlayout)
        b_hlayout = QtWidgets.QHBoxLayout()
        b_hlayout.setContentsMargins(0, 10, 0, 0)
        v_mainlayout.addLayout(b_hlayout, 1)

        t_loginlb = QtWidgets.QToolButton()
        t_loginlb.setIcon(newIcon("loginuser"))
        t_loginlb.setIconSize(QtCore.QSize(80, 70))
        t_loginlb.setStyleSheet("QWidget {background: none; border: 0px;}")

        t_hlayout.addWidget(t_loginlb)

        bv_control_layout = QtWidgets.QVBoxLayout()
        b_hlayout.addLayout(bv_control_layout)

        id_layout = QtWidgets.QHBoxLayout()
        pwd_layout = QtWidgets.QHBoxLayout()
        lang_layout = QtWidgets.QHBoxLayout()
        btn_layout = QtWidgets.QHBoxLayout()
        alram_layout = QtWidgets.QHBoxLayout()

        bv_control_layout.addLayout(id_layout)
        bv_control_layout.addLayout(pwd_layout)
        bv_control_layout.addLayout(lang_layout)
        bv_control_layout.addLayout(alram_layout)
        bv_control_layout.addLayout(btn_layout)

        lb_id = QtWidgets.QLabel(self.tr('ID *'))

        self._lb_id_edit = QtWidgets.QLineEdit()
        self._lb_id_edit.setFixedWidth(200)
        self._lb_id_edit.setFixedHeight(25)
        self._lb_id_edit.setStyleSheet("QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 6px}")
        id_layout.addWidget(lb_id)
        id_layout.addWidget(self._lb_id_edit)
        #id_layout.setSpacing(10)

        lb_pwd = QtWidgets.QLabel(self.tr('PWD *'))

        self._lb_pwd_edit = QtWidgets.QLineEdit()
        self._lb_pwd_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self._lb_pwd_edit.setFixedWidth(200)
        self._lb_pwd_edit.setFixedHeight(25)
        self._lb_pwd_edit.setStyleSheet("QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 6px}")
        pwd_layout.addWidget(lb_pwd)
        pwd_layout.addWidget(self._lb_pwd_edit)
        pwd_layout.setContentsMargins(0, 5, 0, 0)

        lb_lang = QtWidgets.QLabel(self.tr('Language'))
        self._cb = QtWidgets.QComboBox()
        self._cb.addItem(self.tr('English'), 'null')
        self._cb.addItem(self.tr('Korean'), 'ko_KR')
        self._cb.setFixedWidth(200)
        self._cb.setFixedHeight(25)
        self._cb.setStyleSheet("QWidget {border: 1px solid #aaa; border-radius: 2px; padding: 2px 6px}")

        lang_layout.addWidget(lb_lang)
        lang_layout.addWidget(self._cb)
        lang_layout.setContentsMargins(0, 5, 0, 0)
        cbidx = 0
        for i in range(0, self._cb.count()):
            itxt = self._cb.itemData(i)
            ml = self._config["local_lang"]
            if itxt == ml:
                cbidx = i
                break

        self._cb.setCurrentIndex(cbidx)


        self._lb_alram = QtWidgets.QLabel('')
        self._lb_alram.setStyleSheet("QLabel { color : red; }")
        self._lb_alram.setFixedHeight(18)

        alram_layout.addWidget(self._lb_alram)

        btn_login = QtWidgets.QPushButton(self.tr('Login'))
        btn_login.setFont(appFont())
        btn_login.setFixedWidth(150)
        btn_login.setFixedHeight(30)
        btn_login.setStyleSheet("QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 3px; color:white;background-color: #043966; font-size: 13px}")
        btn_login.clicked.connect(self.loginAction)
        btn_layout.addWidget(btn_login)
        btn_layout.setContentsMargins(0, 5, 0, 5)

    # noinspection PyUnresolvedReferences
    def loginAction(self):
        # print("uname is " + self._lb_id_edit.text().strip())
        # print("pwd is " + self._lb_pwd_edit.text().strip())
        # print("cb  is " + self._cb.currentText() + " :: " + str(self._cb.currentData()))

        uid = self._lb_id_edit.text().strip()
        pwd = self._lb_pwd_edit.text().strip()
        lang = str(self._cb.currentData())
        self._config["local_lang"] = lang

        if not uid:
            self._lb_alram.setText(self.tr("The ID should not be empty"))
            threading.Timer(3, self.showErrorText).start()
            self._lb_id_edit.setFocus()
            return

        if not pwd:
            self._lb_alram.setText(self.tr("The PWD should not be empty"))
            threading.Timer(3, self.showErrorText).start()
            self._lb_pwd_edit.setFocus()
            return

        url = self._config["api_url"] + 'ords/lm/v1/labelme/login'
        headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
        data = {'user_id': uid, 'password': pwd}
        # respone = requests.post(url, headers=headers, json=data)
        # jsstr = respone.json()
        jsstr = httpReq(url, "post", headers, data)
        # print(json.dumps(jsstr))
        if jsstr['message'] != 'success':
            if jsstr['code'].upper() == 'C001':
                self._config["login_state"] = 'tochangepwd'
                self._lb_alram.setText(jsstr['message'])
                threading.Timer(3, self.showAlarmtext).start()
            else:
                # self._lb_alram.setText(self.tr("Invalid ID or PWD"))
                # threading.Timer(2, self.showErrorText).start()
                return QtWidgets.QMessageBox.critical(
                    self, "Message", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
                )
        else:   # success
            if self._config is not None:
                self._config["grade_yn"] = jsstr['grade_yn'].upper() if jsstr['grade_yn'].upper() == "Y" else "N"
                self._config["product_yn"] = jsstr['product_yn'].upper() if jsstr['product_yn'].upper() == "Y" else "N"
                self._config["label_yn"] = jsstr['label_yn'].upper() if jsstr['label_yn'].upper() == "Y" else "N"
                self._config["user_id"] = uid
                self._config["net"] = jsstr['net'] if jsstr['net'] else ""
                if self._config["net"] != "":
                    import subprocess
                    try:
                        #nd = r'net use d:\\Temp /user:{} {}'.format(self._config['user_id'], 'demo1234!')
                        nd = r'{}'.format(self._config['net'])
                        subprocess.call(nd, shell=True)
                    except subprocess.CalledProcessError as e:
                        LogPrint("Error subprocess : %s" % e)
                        pass

            self._lb_alram.setText(self.tr("Sucess Log in"))
            self._config["login_state"] = True
            threading.Timer(0.05, self.showAlarmtext).start()

    def showErrorText(self):
        self._lb_alram.setText("")

    def showAlarmtext(self):
        self._lb_alram.setText("")
        self.close()