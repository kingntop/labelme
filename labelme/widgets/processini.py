import os
import configparser
import copy


class ProcessINI(object):

    SECTION = 'DEFAULT'
    configFileName = None
    key = None
    configDef = {}
    isExist = False

    def __init__(self, pFileName=None, pSection=None, pKey=None):
        # Load setting in the main thread
        self.configFileName = pFileName
        self.SECTION = pSection
        self.key = pKey
        ext = os.path.exists(self.configFileName)
        if os.path.exists(self.configFileName) is not False:
            self.isExist = True

    def hasINIFile(self):
        if self.isExist is True:
            return True
        return False

    def setConfigDef(self, dfile):
        self.configDef = dfile

    # setting section
    def setSection(self, section):
        self.SECTION = section

    # setting filename
    def setFileName(self, fileName):
        self.configFileName = fileName

    # setting key
    def setKey(self, pkey):
        self.key = pkey

    def setValue(self, keyVal=None):
        if self.isExist is False:
            return
        if keyVal is None:
            return
        self.configDef[self.key] = keyVal
        self.saveConfig()
        return True

    def getValue(self):
        if self.isExist is False:
            return
        if self.configDef[self.key]:
            return self.configDef[self.key]
        return

    def getValueByKey(self, pkey=None):
        if self.isExist is False:
            return
        if pkey is None and self.key is not None:
            if self.configDef[self.key]:
                return self.configDef[self.key]
        elif pkey is not None:
            if self.configDef[pkey]:
                return self.configDef[pkey]
        return

    def loadSectionKeys(self):
        if self.isExist is False:
            return
        configFile = configparser.ConfigParser()
        configFile.read(self.configFileName)

        if configFile[self.SECTION]:
            for key in configFile[self.SECTION]:
                if type(configFile[self.SECTION][key]) == int:
                    try:
                        val = int(configFile[self.SECTION][key])
                        self.configDef[key] = val
                    except:
                        pass
                elif type(configFile[self.SECTION][key]) == float:
                    try:
                        val = float(configFile[self.SECTION][key])
                        self.configDef[key] = val
                    except:
                        pass
                elif type(configFile[self.SECTION][key]) == bool:
                    if configFile[self.SECTION][key] == 'True':
                        self.configDef[key] = True
                    else:
                        self.configDef[key] = False
                else:
                    self.configDef[key] = configFile[self.SECTION][key]

    def loadConfig(self, configParam):
        if not self.configFileName:
            return
        configFile = configparser.ConfigParser()
        configFile.read(self.configFileName)

        for key in configParam.keys():
            if key in configFile[self.SECTION]:
                if type(configParam[key]) == int:
                    try:
                        val = int(configFile[self.SECTION][key])
                        configParam[key] = val
                    except:
                        pass
                elif type(configParam[key]) == float:
                    try:
                        val = float(configFile[self.SECTION][key])
                        configParam[key] = val
                    except:
                        pass
                elif type(configParam[key]) == bool:
                    if configFile[self.SECTION][key] == 'True':
                        configParam[key] = True
                    else:
                        configParam[key] = False
                else:
                    configParam[key] = configFile[self.SECTION][key]

    def createConfigFile(self):
        if not self.configFileName:
            return False
        lbFile = configparser.ConfigParser()
        if not lbFile.has_section(self.SECTION):
            lbFile.add_section(self.SECTION)
        lbFile.set(self.SECTION, self.key, 'null')
        with open(self.configFileName, 'w') as writeFile:
            lbFile.write(writeFile)
        return True

    # 현재 설정을 파일로 저장함
    def saveConfig(self):
        if not self.configFileName:
            return
        lbFile = configparser.ConfigParser()
        lbFile.read(self.configFileName)

        for key in self.configDef:
            val = None
            if type(self.configDef[key]) == int:
                val = "%d" % self.configDef[key]
            elif type(self.configDef[key]) == float:
                val = "%f" % self.configDef[key]
            elif type(self.configDef[key]) == bool:
                if self.configDef[key]:
                    val = 'True'
                else:
                    val = 'False'
            elif type(self.configDef[key]) == str:
                val = self.configDef[key]
            if val:
                lbFile[self.SECTION][key] = val
        with open(self.configFileName, 'w') as writeFile:
            lbFile.write(writeFile)

    # 현재 설정 내용을 출력함
    def dumpConfig(self):
        for key in self.configDef:
            if type(self.configDef[key]) == int:
                print("%s = %d[int]" % (key, self.configDef[key]))
            elif type(self.configDef[key]) == float:
                print("%s = %f[float]" % (key, self.configDef[key]))
            elif type(self.configDef[key]) == bool:
                if self.configDef[key]:
                    print("%s = True[bool]" % key)
                else:
                    print("%s = False[bool]" % key)
            elif type(self.configDef[key]) == str:
                print("%s = %s[str]" % (key, self.configDef[key]))


"""
 The class is class to save data in .labelmerc into path /user/xxx/
"""
class AppInfoFile(object):
    def __init__(self, pFileName=None, pKey=None, pVal=None, defaultyml=None):
        # Load setting in the main thread
        self._defaultyml = defaultyml
        self._file = pFileName
        self._key = pKey
        self._val = pVal

    def saveValue(self):
        if not self._file:
            return
        if os.path.exists(self._file) is not True:
            return
        # default_config_file = os.path.join(os.path.expanduser("~"), ".labelmerc")
        # local_lang: null
        #fp.write("{}: {}\n".format(self._key, self._val))
        line_content = ""
        with open(self._file, "r", encoding="utf-8") as fp:
            lines = fp.readlines()
            for i, le in enumerate(lines):
                line = le.rstrip()
                if line:
                    if line.find(self._key) == 0:
                        line_content += "{}: {}\n".format(self._key, self._val)
                    else:
                        line_content += line + "\n"
                else:
                    line_content += "\n"

        with open(self._file, "w", encoding="utf-8") as fp:
            fp.write(line_content)

    def saveNewKeyAndValue(self):
        if not self._file:
            return
        if os.path.exists(self._file) is not True:
            return

        hv = False
        with open(self._file, "r", encoding="utf-8") as fp:
            lines = fp.readlines()
            for i, le in enumerate(lines):
                if le:
                    if le.find(self._key) == 0:
                        hv = True

        if hv is False:
            line_content = ""
            with open(self._file, "r", encoding="utf-8") as fp:
                lines = fp.readlines()
                for i, le in enumerate(lines):
                    if le:
                        line_content += le
                    else:
                        line_content += '\n'

            line_content += "{}: {}\n".format(self._key, self._val)
            with open(self._file, "w", encoding="utf-8") as fp:
                fp.write(line_content)
        else:
            self.overideKeyAndValue()

    def overideKeyAndValue(self):
        if not self._file:
            return
        if os.path.exists(self._file) is not True:
            return
        if self._key is None:
            return
        if self._val is None:
            return

        hv = False
        with open(self._file, "r", encoding="utf-8") as fp:
            lines = fp.readlines()
            for i, le in enumerate(lines):
                if le:
                    if le.find(self._key) == 0:
                        hv = True

        if hv is True:
            line_content = ""
            with open(self._file, "r", encoding="utf-8") as fp:
                lines = fp.readlines()
                for i, le in enumerate(lines):
                    if le:
                        if le.find(self._key) == 0:
                            line_content += "{}: {}\n".format(self._key, self._val)
                        else:
                            line_content += le
                    else:
                        line_content += '\n'

            with open(self._file, "w", encoding="utf-8") as fp:
                fp.write(line_content)


    def hasKey(self, key=None):
        if not self._file:
            return False
        if os.path.exists(self._file) is not True:
            return False

        hv = False
        akey = key if key is not None else self._key
        if akey:
            hv = False
            with open(self._file, "r", encoding="utf-8") as fp:
                lines = fp.readlines()
                for i, le in enumerate(lines):
                    if le:
                        if le.find(akey) == 0:
                            hv = True

        return hv


    def getValueByKey(self):
        if not self._file:
            return
        if os.path.exists(self._file) is not True:
            return
        val = ''
        with open(self._file, "r", encoding="utf-8") as fp:
            lines = fp.readlines()
            for i, le in enumerate(lines):
                line = copy.copy(le)
                line = line.rstrip()
                if line:
                    if line.find(self._key) == 0:
                        line = line.strip('\n')
                        line = line.strip('\t')
                        val = line.split(':')[1].strip()
        return val