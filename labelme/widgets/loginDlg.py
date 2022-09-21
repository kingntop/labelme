import os
import requests
import threading

from PyQt5.QtWidgets import QDesktopWidget, QWidget
from qtpy import QtWidgets
from qtpy import QtGui, QtCore
from qtpy.QtCore import Qt
from labelme.utils.qt import httpReq
from labelme.utils import newIcon
from labelme.utils import urlIcon
from labelme.utils import appFont
from labelme.utils.qt import LogPrint
from labelme.widgets.processini import AppInfoFile
from labelme.config import get_app_origin_val



class LoginDLG(QWidget):

    def __init__(
            self,
            config=None,
            default_config_file=None
    ):
        super().__init__()
        self._config = config
        self._default_config_file = default_config_file
        self._downstate = False
        self.initUI()

    def initUI(self):
        self.setFont(appFont())
        v_mainlayout = QtWidgets.QVBoxLayout()
        v_mainlayout.setContentsMargins(40, 15, 40, 40)
        v_mainlayout.setSpacing(10)
        self.setLayout(v_mainlayout)
        self.setWindowTitle(self.tr('Label Studio (%s)' % self._config['app_version']))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # self.setGeometry(300, 300, 200, 150)
        #self.resize(400, 300)
        self.setFixedSize(500, 450)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        t_hlayout = QtWidgets.QVBoxLayout()
        t_hlayout.setContentsMargins(0, 30, 0, 25)

        v_mainlayout.addLayout(t_hlayout)

        b_hlayout = QtWidgets.QHBoxLayout()
        b_hlayout.setContentsMargins(0, 0, 0, 0)
        v_mainlayout.addLayout(b_hlayout, 1)

        pximg = QtGui.QPixmap(urlIcon("icon"))
        t_logiconlb = QtWidgets.QLabel()
        # t_logiconlb.setFixedHeight(85)
        # t_logiconlb.setFixedWidth(85)
        t_logiconlb.setAlignment(QtCore.Qt.AlignCenter)
        t_logiconlb.setPixmap(
            pximg.scaled(
                80,
                80,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        )


        tt_loginlb = QtWidgets.QLabel("RAIID-Label Studio\nDaehan Steel")
        tt_loginlb.setFont(appFont())
        tt_loginlb.setStyleSheet("QLabel {font-size: 20px; font-weight: bold}")
        tt_loginlb.setAlignment(QtCore.Qt.AlignCenter)

        t_hlayout.addWidget(t_logiconlb)
        t_hlayout.addSpacing(20)
        t_hlayout.addWidget(tt_loginlb)

        bv_control_layout = QtWidgets.QVBoxLayout()
        b_hlayout.addLayout(bv_control_layout)

        id_layout = QtWidgets.QHBoxLayout()
        id_layout.addSpacing(30)
        pwd_layout = QtWidgets.QHBoxLayout()
        pwd_layout.addSpacing(30)
        lang_layout = QtWidgets.QHBoxLayout()
        btn_layout = QtWidgets.QHBoxLayout()
        alram_layout = QtWidgets.QHBoxLayout()

        bv_control_layout.addLayout(id_layout)
        bv_control_layout.addLayout(pwd_layout)
        bv_control_layout.addLayout(lang_layout)
        bv_control_layout.addLayout(alram_layout)
        bv_control_layout.addLayout(btn_layout)

        lb_id = QtWidgets.QLabel("아이디  :" if self._config['local_lang'] == 'ko_KR' else 'ID *')
        lb_id.setStyleSheet("QLabel {font-size: 16px; font-weight: bold}")


        self._lb_id_edit = QtWidgets.QLineEdit()
        self._lb_id_edit.setText(get_app_origin_val(self._default_config_file, 'user_id'))
        self._lb_id_edit.setFixedHeight(35)
        self._lb_id_edit.setStyleSheet("QLineEdit { border: 1px solid #aaa; border-radius: 5px; padding: 2px 6px; font-size: 16px;}")

        id_layout.addWidget(lb_id)
        id_layout.addSpacing(28)
        id_layout.addWidget(self._lb_id_edit)
        id_layout.addSpacing(20)

        lb_pwd = QtWidgets.QLabel("비밀번호  :" if self._config['local_lang'] == 'ko_KR' else 'PWD *')
        lb_pwd.setStyleSheet("QLabel {font-size: 16px; font-weight: bold}")

        self._lb_pwd_edit = QtWidgets.QLineEdit()
        self._lb_pwd_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self._lb_pwd_edit.setFixedHeight(35)
        self._lb_pwd_edit.setStyleSheet("QLineEdit { border: 1px solid #aaa; border-radius: 5px; padding: 2px 6px; font-size: 16px;}")

        pwd_layout.addWidget(lb_pwd)
        pwd_layout.addSpacing(10)
        pwd_layout.addWidget(self._lb_pwd_edit)
        pwd_layout.setContentsMargins(0, 5, 0, 0)
        pwd_layout.addSpacing(20)

        self._lb_alram = QtWidgets.QLabel('')
        self._lb_alram.setStyleSheet("QLabel { color : red; }")
        self._lb_alram.setFixedHeight(18)

        alram_layout.addWidget(self._lb_alram)

        btn_login = QtWidgets.QPushButton("로그인" if self._config['local_lang'] == 'ko_KR' else 'Login')
        btn_login.setFont(appFont())
        btn_login.setFixedWidth(150)
        btn_login.setFixedHeight(35)
        btn_login.setStyleSheet("QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 3px; color:white;background-color: #043966; font-size: 16px; font-weight: bold}")
        btn_login.clicked.connect(self.loginAction)

        btn_cancel = QtWidgets.QPushButton("취소" if self._config['local_lang'] == 'ko_KR' else 'Cancel')
        btn_cancel.setFont(appFont())
        btn_cancel.setFixedWidth(150)
        btn_cancel.setFixedHeight(35)
        btn_cancel.setStyleSheet("QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 3px; color:white;background-color: #043966; font-size: 16px; font-weight: bold}")
        btn_cancel.clicked.connect(self.loginCancel)

        btn_layout.addWidget(btn_login)
        btn_layout.addSpacing(20)
        btn_layout.addWidget(btn_cancel)
        #btn_layout.setContentsMargins(0, 0, 0, 5)

    def initUI_temp(self):
        self.setFont(appFont())
        v_mainlayout = QtWidgets.QVBoxLayout()
        v_mainlayout.setContentsMargins(40, 15, 40, 40)
        v_mainlayout.setSpacing(10)
        self.setLayout(v_mainlayout)
        self.setWindowTitle(self.tr('Label Studio (%s)' % self._config['app_version']))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # self.setGeometry(300, 300, 200, 150)
        # self.resize(400, 300)
        self.setFixedSize(500, 450)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        t_hlayout = QtWidgets.QVBoxLayout()
        t_hlayout.setContentsMargins(0, 30, 0, 25)

        v_mainlayout.addLayout(t_hlayout)

        b_hlayout = QtWidgets.QHBoxLayout()
        b_hlayout.setContentsMargins(0, 0, 0, 0)
        v_mainlayout.addLayout(b_hlayout, 1)

        pximg = QtGui.QPixmap(urlIcon("icon"))
        t_logiconlb = QtWidgets.QLabel()
        # t_logiconlb.setFixedHeight(85)
        # t_logiconlb.setFixedWidth(85)
        t_logiconlb.setAlignment(QtCore.Qt.AlignCenter)
        t_logiconlb.setPixmap(
            pximg.scaled(
                80,
                80,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        )

        tt_loginlb = QtWidgets.QLabel("RAIID-Label Studio\nDaehan Steel")
        tt_loginlb.setFont(appFont())
        tt_loginlb.setStyleSheet("QLabel {font-size: 20px; font-weight: bold}")
        tt_loginlb.setAlignment(QtCore.Qt.AlignCenter)

        t_hlayout.addWidget(t_logiconlb)
        t_hlayout.addSpacing(20)
        t_hlayout.addWidget(tt_loginlb)

        bv_control_layout = QtWidgets.QVBoxLayout()
        b_hlayout.addLayout(bv_control_layout)

        id_layout = QtWidgets.QHBoxLayout()
        id_layout.addSpacing(30)
        pwd_layout = QtWidgets.QHBoxLayout()
        pwd_layout.addSpacing(30)
        lang_layout = QtWidgets.QHBoxLayout()
        btn_layout = QtWidgets.QHBoxLayout()
        alram_layout = QtWidgets.QHBoxLayout()

        bv_control_layout.addLayout(id_layout)
        bv_control_layout.addLayout(pwd_layout)
        bv_control_layout.addLayout(lang_layout)
        bv_control_layout.addLayout(alram_layout)
        bv_control_layout.addLayout(btn_layout)

        lb_id = QtWidgets.QLabel("아이디  :" if self._config['local_lang'] == 'ko_KR' else 'ID *')
        lb_id.setStyleSheet("QLabel {font-size: 16px; font-weight: bold}")

        pximg_uid = QtGui.QPixmap(urlIcon("uid"))
        pximg_uidlb = QtWidgets.QLabel()
        pximg_uidlb.setFixedHeight(32)
        pximg_uidlb.setFixedWidth(32)
        pximg_uidlb.setAlignment(QtCore.Qt.AlignCenter)
        pximg_uidlb.setPixmap(
            pximg_uid.scaled(
                30,
                30,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        )
        pximg_uidlb.move(0, 0)
        pximg_uidlb.setStyleSheet(
            "QLabel {position: absolute;left:0;top:0")

        self._lb_id_edit = QtWidgets.QLineEdit()
        self._lb_id_edit.setFixedHeight(35)
        # self._lb_id_edit.setStyleSheet("QLineEdit {border: 1px solid #aaa; border-radius: 5px; padding: 2px 6px; font-size: 16px;")

        qf_tool = QtWidgets.QToolBar()
        qf_tool.setStyleSheet("QToolBar  {border: 1px solid #aaa; border-radius: 5px; background:#fff")
        qf_tool.setAutoFillBackground(True)

        qf_tool.addWidget(pximg_uidlb)
        # qf_tool.addWidget(self._lb_id_edit)

        id_layout.addWidget(lb_id)
        id_layout.addSpacing(28)

        # id_layout.addWidget(pximg_uidlb)
        # id_layout.addWidget(self._lb_id_edit)
        id_layout.addWidget(qf_tool)
        id_layout.addSpacing(20)

        lb_pwd = QtWidgets.QLabel("비밀번호  :" if self._config['local_lang'] == 'ko_KR' else 'PWD *')
        lb_pwd.setStyleSheet("QLabel {font-size: 16px; font-weight: bold}")

        self._lb_pwd_edit = QtWidgets.QLineEdit()
        self._lb_pwd_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self._lb_pwd_edit.setFixedHeight(35)
        self._lb_pwd_edit.setStyleSheet(
            "QLineEdit {border: 1px solid #aaa; border-radius: 5px; padding: 2px 6px; font-size: 16px;background-image:url(%s)}" % urlIcon(
                "upwd"))

        pwd_layout.addWidget(lb_pwd)
        pwd_layout.addSpacing(10)
        pwd_layout.addWidget(self._lb_pwd_edit)
        pwd_layout.setContentsMargins(0, 5, 0, 0)
        pwd_layout.addSpacing(20)

        """
        # 언어변경부분
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
        """

        self._lb_alram = QtWidgets.QLabel('')
        self._lb_alram.setStyleSheet("QLabel { color : red; }")
        self._lb_alram.setFixedHeight(18)

        alram_layout.addWidget(self._lb_alram)

        btn_login = QtWidgets.QPushButton("로그인" if self._config['local_lang'] == 'ko_KR' else 'Login')
        btn_login.setFont(appFont())
        btn_login.setFixedWidth(150)
        btn_login.setFixedHeight(35)
        btn_login.setStyleSheet(
            "QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 3px; color:white;background-color: #043966; font-size: 16px; font-weight: bold}")
        btn_login.clicked.connect(self.loginAction)

        btn_cancel = QtWidgets.QPushButton("취소" if self._config['local_lang'] == 'ko_KR' else 'Cancel')
        btn_cancel.setFont(appFont())
        btn_cancel.setFixedWidth(150)
        btn_cancel.setFixedHeight(35)
        btn_cancel.setStyleSheet(
            "QWidget {border: 1px solid #aaa; border-radius: 5px; padding: 2px 3px; color:white;background-color: #043966; font-size: 16px; font-weight: bold}")
        btn_cancel.clicked.connect(self.loginCancel)

        btn_layout.addWidget(btn_login)
        btn_layout.addSpacing(20)
        btn_layout.addWidget(btn_cancel)
        # btn_layout.setContentsMargins(0, 0, 0, 5)

    # noinspection PyUnresolvedReferences
    def loginAction(self):
        # print("uname is " + self._lb_id_edit.text().strip())
        # print("pwd is " + self._lb_pwd_edit.text().strip())
        # print("cb  is " + self._cb.currentText() + " :: " + str(self._cb.currentData()))

        uid = self._lb_id_edit.text().strip()
        pwd = self._lb_pwd_edit.text().strip()
        # 언어부분을 없앤다
        #lang = str(self._cb.currentData())
        #self._config["local_lang"] = lang

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

        self._config["user_id"] = uid
        data = {'user_id': uid, 'password': pwd}
        # respone = requests.post(url, headers=headers, json=data)
        # jsstr = respone.json()
        jsstr = httpReq(url, "post", headers, data)

        if jsstr['message'] != 'success':
            if 'code' in jsstr and jsstr['code'].upper() == 'C001':  # 암호변경조건
                self._config["login_state"] = 'tochangepwd'
                self._lb_alram.setText(jsstr['message'])
                threading.Timer(3, self.showAlarmtext).start()
            else:
                return QtWidgets.QMessageBox.critical(
                    self, "Message", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
                )
        else:   # success
            if self._config is not None:
                self._config["grade_yn"] = jsstr['grade_yn'].upper() if jsstr['grade_yn'].upper() == "Y" else "N"
                self._config["product_yn"] = jsstr['product_yn'].upper() if jsstr['product_yn'].upper() == "Y" else "N"
                self._config["label_yn"] = jsstr['label_yn'].upper() if jsstr['label_yn'].upper() == "Y" else "N"
                self._config["net"] = jsstr['net'] if jsstr['net'] else ""

            self._config["login_state"] = False
            self.CheckAppVersion()  # 버전 체크


    def CheckAppVersion(self):
        url = self._config["api_url"] + 'ords/lm/v1/labelme/versions'
        headers = {'Authorization': 'Bearer 98EDFBC2D4A74E9AB806D4718EC503EE6DEDAAAD'}
        jsstr = httpReq(url, "get", headers)
        if jsstr['message'] != 'success':
            return QtWidgets.QMessageBox.critical(
                self, "Message", "<p><b>%s</b></p>%s" % ("Error", jsstr['message'])
            )
        else:  # success
            items = jsstr['items'][0]
            ser_vsion = items['version']
            durl = items['url']
            file_name = durl.split('/')[-1]
            local_vsion = self._config['app_version']
            if local_vsion != ser_vsion and int(ser_vsion) > int(local_vsion):  # 버전이 다르면
                filters = self.tr("save file (*%s)") % 'exe'
                dlg = QtWidgets.QFileDialog(
                    self, 'save', os.path.dirname(str(".")), filters
                )
                dlg.setDefaultSuffix('exe')
                dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
                dlg.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite, False)
                dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, False)
                basename = os.path.basename(os.path.splitext(file_name)[0])
                default_labelfile_name = os.path.join(
                    '.', basename + '.exe'
                )
                sfilename = dlg.getSaveFileName(
                    self,
                    self.tr("Choose File"),
                    default_labelfile_name,
                    self.tr("Label files (*%s)") % '.exe',
                )
                if isinstance(sfilename, tuple):
                    sfilename, _ = sfilename
                #print(sfilename)
                file = requests.get(durl, stream=True)
                if sfilename and sfilename != '':
                    self._lb_alram.setText(self.tr("File is being downloaded. Please wait for a moment."))
                    self.setEnabled(False)
                    self._downstate = True
                    threading.Timer(0.5, self.downloadApp, [sfilename, file]).start()
                else:
                    self._lb_alram.setText('')
                    self._config["login_state"] = False
            else:
                self._config["login_state"] = True  # 버전이 정상이라면 로그인
                if self._default_config_file is not None:
                    try:
                        d_user = get_app_origin_val(self._default_config_file, 'user_id')
                        if d_user is not None and d_user != self._config["user_id"]:
                            appinfo_file = AppInfoFile(self._default_config_file, "user_id", self._config["user_id"])
                            appinfo_file.overideKeyAndValue()
                        elif d_user is None:
                            appinfo_file = AppInfoFile(self._default_config_file, "user_id", self._config["user_id"])
                            appinfo_file.saveNewKeyAndValue()
                        else:
                            pass
                    except Exception as e:
                        pass


                self.close()


    def showErrorText(self):
        self._lb_alram.setText("")

    def showAlarmtext(self):
        self._lb_alram.setText("")
        self.close()

    def loginCancel(self):
        self._config["login_state"] = False
        self.close()

    def closeEvent(self, event):
        if self._downstate is True:
            event.ignore()

    def downloadApp(self, *args):
        filename = args[0]
        file = args[1]
        try:
            with open(filename, "wb") as fb:
                for chunk in file.iter_content(chunk_size=1024):
                    if chunk:
                        fb.write(chunk)
            self._config["login_state"] = False
            self.setEnabled(True)
            self._lb_alram.setText("")
            self._downstate = False
            self.close()
        except Exception as e:
            LogPrint("새로운 버젼 다운로딩중 오류발생하였습니다.")
            pass