import argparse
import codecs
import logging
import os
import sys

import yaml
from qtpy import QtCore, QtWidgets
from labelme import __appname__, __version__
from labelme.app import MainWindow
from labelme.config import get_config
from labelme.config import get_app_version
from labelme.config import get_app_origin_val
from labelme.config import copy_to_version
from labelme.logger import logger
from labelme.utils import newIcon

from labelme.widgets.processini import AppInfoFile
from labelme.widgets.processini import ProcessINI
from labelme.widgets.loginDlg import LoginDLG
from labelme.widgets.pwdDlg import PwdDlgWin
from labelme.utils import newLang
from labelme.utils import appFont
from labelme.utils.qt import LogPrint


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version", "-V", action="store_true", help="show version"
    )
    parser.add_argument(
        "--reset-config", action="store_true", help="reset qt config"
    )
    parser.add_argument(
        "--logger-level",
        default="info",
        choices=["debug", "info", "warning", "fatal", "error"],
        help="logger level",
    )
    parser.add_argument("filename", nargs="?", help="image or label filename")
    parser.add_argument(
        "--output",
        "-O",
        "-o",
        help="output file or directory (if it ends with .json it is "
        "recognized as file, else as directory)",
    )
    default_config_file = os.path.join(os.path.expanduser("~"), ".labelmerc")
    parser.add_argument(
        "--config",
        dest="config",
        help="config file or yaml-format string (default: {})".format(
            default_config_file
        ),
        default=default_config_file,
    )
    # config for the gui
    parser.add_argument(
        "--nodata",
        dest="store_data",
        action="store_false",
        help="stop storing image data to JSON file",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--autosave",
        dest="auto_save",
        action="store_true",
        help="auto save",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--nosortlabels",
        dest="sort_labels",
        action="store_false",
        help="stop sorting labels",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--flags",
        help="comma separated list of flags OR file containing flags",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--grades",
        help="comma separated list of grades OR file containing flags",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--labelflags",
        dest="label_flags",
        help=r"yaml string of label specific flags OR file containing json "
        r"string of label specific flags (ex. {person-\d+: [male, tall], "
        r"dog-\d+: [black, brown, white], .*: [occluded]})",  # NOQA
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--labels",
        help="comma separated list of labels OR file containing labels",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--validatelabel",
        dest="validate_label",
        choices=["exact"],
        help="label validation types",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--keep-prev",
        action="store_true",
        help="keep annotation of previous frame",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--epsilon",
        type=float,
        help="epsilon to find nearest vertex on canvas",
        default=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if args.version:
        print("{0} {1}".format(__appname__, __version__))
        sys.exit(0)

    logger.setLevel(getattr(logging, args.logger_level.upper()))

    if hasattr(args, "flags"):
        if os.path.isfile(args.flags):
            with codecs.open(args.flags, "r", encoding="utf-8") as f:
                args.flags = [line.strip() for line in f if line.strip()]
        else:
            args.flags = [line for line in args.flags.split(",") if line]

    if hasattr(args, "grades"):
        if os.path.isfile(args.grades):
            with codecs.open(args.grades, "r", encoding="utf-8") as f:
                args.grades = [line.strip() for line in f if line.strip()]
        else:
            args.grades = [line for line in args.grades.split(",") if line]

    if hasattr(args, "labels"):
        if os.path.isfile(args.labels):
            with codecs.open(args.labels, "r", encoding="utf-8") as f:
                args.labels = [line.strip() for line in f if line.strip()]
        else:
            args.labels = [line for line in args.labels.split(",") if line]

    if hasattr(args, "label_flags"):
        if os.path.isfile(args.label_flags):
            with codecs.open(args.label_flags, "r", encoding="utf-8") as f:
                args.label_flags = yaml.safe_load(f)
        else:
            args.label_flags = yaml.safe_load(args.label_flags)

    config_from_args = args.__dict__
    config_from_args.pop("version")
    reset_config = config_from_args.pop("reset_config")
    filename = config_from_args.pop("filename")
    output = config_from_args.pop("output")
    config_file_or_yaml = config_from_args.pop("config")

    try:
        o_app_version = get_app_origin_val(config_file_or_yaml, 'app_version')
        if o_app_version is not None and o_app_version != "":
            r_app_version = get_app_version()
            if r_app_version != o_app_version:
                copy_to_version()
        elif o_app_version is None:
            copy_to_version()
        else:
            pass
    except Exception as e:
        LogPrint("앱버젼확인에서 오류가 발생하였습니다.")

    config = get_config(config_file_or_yaml, config_from_args)
    config['app_version'] = get_app_version()

    config['api_url'] = ''
    config_def = {"api_url": ""}
    config_ini = ProcessINI("config.ini", "server", "api_url")
    if config_ini.hasINIFile():
        config_ini.loadConfig(config_def)
        lnlen = len(config_def['api_url'])
        if lnlen < 8:
            config_def = {"api_url": "https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/"}
            config_ini.setConfigDef(config_def)
            config_ini.saveConfig()
            config['api_url'] = 'https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/'
        else:
            config['api_url'] = config_def['api_url']
    else:
        config_ini.createConfigFile()
        config_def = {"api_url": "https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/"}
        config['api_url'] = 'https://gb9fb258fe17506-apexdb.adb.ap-seoul-1.oraclecloudapps.com/'
        config_ini.setConfigDef(config_def)
        config_ini.saveConfig()


    if not config["labels"] and config["validate_label"]:
        logger.error(
            "--labels must be specified with --validatelabel or "
            "validate_label: true in the config file "
            "(ex. ~/.labelmerc)."
        )
        sys.exit(1)

    output_file = None
    output_dir = None
    if output is not None:
        if output.endswith(".json"):
            output_file = output
        else:
            output_dir = output

    local_lang = config["local_lang"] if config["local_lang"] is not None else QtCore.QLocale.system().name()
    # start get lang of UI
    # 언어를 변경하지 않는다.
    #config["local_lang"] = local_lang
    config["local_lang"] = 'ko_KR'  # 고정시킨다.

    run_loginWin(config, default_config_file, filename, output_file, output_dir, reset_config)

def run_loginWin(config, default_config_file, filename, output_file, output_dir, reset_config):
    log_translator = QtCore.QTranslator()
    lang = newLang(config["local_lang"])
    log_translator.load(lang)

    login_app = QtWidgets.QApplication([])
    login_app.setApplicationName(__appname__)
    login_app.setWindowIcon(newIcon("icon"))
    login_app.installTranslator(log_translator)

    config["login_state"] = False
    config["grade_yn"] = "N"
    config["product_yn"] = "N"
    config["label_yn"] = "N"
    config["user_id"] = ""
    config["net"] = ""

    login_win = LoginDLG(
        config=config,
        default_config_file=default_config_file,
    )
    login_win.show()
    ret = login_app.exec_()
    #print(ret)
    if config["login_state"] is True:
        run_mainApp(config, default_config_file, filename, output_file, output_dir, reset_config)
    elif config["login_state"] == 'tochangepwd':
        run_pwdWin(config, default_config_file, filename, output_file, output_dir, reset_config)
    else:
        sys.exit(0)


def run_pwdWin(config, default_config_file, filename, output_file, output_dir, reset_config):
    lang = config["local_lang"]
    lang = str(lang).replace('.qm', '')

    # 언어를 변경하지 않는다.
    #appinfo_file = AppInfoFile(default_config_file, "local_lang", lang)
    #appinfo_file.saveValue()

    pwd_translator = QtCore.QTranslator()
    mlang = newLang(lang)
    pwd_translator.load(mlang)

    pwd_app = QtWidgets.QApplication([])
    pwd_app.setApplicationName(__appname__)
    pwd_app.setWindowIcon(newIcon("icon"))
    pwd_app.installTranslator(pwd_translator)

    pwd_win = PwdDlgWin(config)
    pwd_win.show()

    ret = pwd_app.exec_()

    if config["login_state"] == 'tochangepwd':
        config["login_state"] = False
        run_loginWin(config, default_config_file, filename, output_file, output_dir, reset_config)
    elif config["login_state"] == 'endLogin':
        config["login_state"] = False
        sys.exit(0)

def run_mainApp(config, default_config_file, filename, output_file, output_dir, reset_config):
    lang = config["local_lang"]
    lang = str(lang).replace('.qm', '')

    # save new lang to labelme.spec //
    orign_lang = get_app_origin_val(default_config_file, 'local_lang')
    if orign_lang is None or orign_lang != lang:
        appinfo_file = AppInfoFile(default_config_file, "local_lang", lang)
        appinfo_file.saveValue()
    # // end save

    mlang = newLang(lang)
    translator = QtCore.QTranslator()
    translator.load(mlang)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(__appname__)
    app.setWindowIcon(newIcon("icon"))
    app.installTranslator(translator)

    win = MainWindow(
        config=config,
        filename=filename,
        output_file=output_file,
        output_dir=output_dir,
    )

    if reset_config:
        logger.info("Resetting Qt config: %s" % win.settings.fileName())
        win.settings.clear()
        sys.exit(0)

    win.show()
    win.raise_()
    sys.exit(app.exec_())


# this main block is required to generate executable by pyinstaller


if __name__ == "__main__":
    main()