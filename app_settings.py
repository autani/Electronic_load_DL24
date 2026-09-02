from os.path import abspath, dirname, exists, join

from PyQt5.QtCore import QSettings

SETTINGS_PATH = join(dirname(abspath(__file__)), '.settings')


def settings_path():
    return SETTINGS_PATH


def settings_exist():
    return exists(SETTINGS_PATH)


def app_settings():
    return QSettings(SETTINGS_PATH, QSettings.IniFormat)
