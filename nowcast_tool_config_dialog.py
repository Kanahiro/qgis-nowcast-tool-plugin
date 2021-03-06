# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NowcastToolDialog
                                 A QGIS plugin
 Tool for Nowcast tiles, load tiles, create weather map animation.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-06-12
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Kanahiro Iguchi
        email                : kanahiro.iguchi@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

from .nowcast_settings import SettingsManager

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'nowcast_tool_config_dialog.ui'))


class NowcastToolConfigDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, callback=None):
        """Constructor."""
        super(NowcastToolConfigDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        self.__callback = callback

        self.setupUi(self)
        self.initGui()

    def initGui(self):
        self.saveButton.clicked.connect(lambda: self.save_settings())
        self.cancelButton.clicked.connect(lambda: self.close())

        settings_manager = SettingsManager()
        duration = int(settings_manager.get_setting('duration'))
        self.durationSpinbox.setValue(duration)

    def save_settings(self):
        duration = self.durationSpinbox.value()
        settings_manager = SettingsManager()
        settings_manager.store_setting('duration', duration)
        self.close()
        self.__callback()
