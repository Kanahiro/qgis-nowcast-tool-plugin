from PyQt5.QtCore import QSettings

# QSettings holds variables as list or dict or str.
# if int or bool value is set, they are converted to str in the Class.
# In particular, isVectorEnabled is treated as bool by cast str '0' or '1' to int(bool).


class SettingsManager:
    SETTING_GROUP = '/NowcastTool'

    def __init__(self):
        self.__settings = {
            'duration': 180,
        }

        self.load_settings()

    def load_setting(self, key):
        qsettings = QSettings()
        qsettings.beginGroup(self.SETTING_GROUP)
        value = qsettings.value(key)
        qsettings.endGroup()
        if value:
            self.__settings[key] = value

    def load_settings(self):
        for key in self.__settings:
            self.load_setting(key)

    def store_setting(self, key, value):
        qsettings = QSettings()
        qsettings.beginGroup(self.SETTING_GROUP)
        qsettings.setValue(key, value)
        qsettings.endGroup()
        self.load_settings()

    def get_setting(self, key):
        return self.__settings[key]

    def get_settings(self):
        return self.__settings
