# -*- coding: utf-8 -*-
"""
/***************************************************************************
 osm2pgrouting4qgis
                                 A QGIS plugin
 Automatically builds a pgRouting-compatible layer in a PostGIS database
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2018-11-03
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Isaac Boates
        email                : iboates@gmail.com
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
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QListWidgetItem, QFileDialog

# Initialize Qt resources from file resources.py
# from .resources import *
# Import the code for the dialog
from .osm2pgrouting4qgis_dialog import osm2pgrouting4qgisDialog
import os.path


class osm2pgrouting4qgis:
    """QGIS Plugin Implementation."""


    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'osm2pgrouting4qgis_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = osm2pgrouting4qgisDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&osm2pgrouting4qgis')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'osm2pgrouting4qgis')
        self.toolbar.setObjectName(u'osm2pgrouting4qgis')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('osm2pgrouting4qgis', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToDatabaseMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/osm2pgrouting4qgis/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'osm2pgrouting4qgis'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # Toggle between local file and OSM Download
        self.file_source_toggle = "file"
        self.dlg.local_file_radioButton.clicked.connect(self.select_local_osm)
        self.dlg.osm_download_radioButton.clicked.connect(self.select_osm_download)

        # Toggle between existing db and new db
        self.dlg.existing_db_radioButton.clicked.connect(self.select_existing_db)
        self.dlg.new_db_radioButton.clicked.connect(self.select_new_db)

        # Toggle schema
        self._schema_toggle = False
        self.dlg.schema_checkBox.setChecked(False)
        self.dlg.schema_checkBox.clicked.connect(self.toggle_schema)

        # Toggle prefix
        self._prefix_toggle = False
        self.dlg.prefix_checkBox.setChecked(False)
        self.dlg.prefix_checkBox.clicked.connect(self.toggle_prefix)

        # Toggle suffix
        self._suffix_toggle = False
        self.dlg.suffix_checkBox.setChecked(False)
        self.dlg.suffix_checkBox.clicked.connect(self.toggle_suffix)

        # Toggle alternative osm2pgr executable
        self._alt_osm2pgr_exec_toggle = False
        self.dlg.alt_osm2pgr_exec_checkBox.setChecked(False)
        self.dlg.alt_osm2pgr_exec_checkBox.clicked.connect(self.toggle_alt_osm2pgr_exec)

        # Set up file chooser
        self.dlg.local_file_pushButton.clicked.connect(self.open_file_chooser)

        # Set up initial GUI state
        self.set_initial_state()


    def set_initial_state(self):

        # Radio buttons
        self.dlg.local_file_radioButton.setChecked(True)
        self.dlg.existing_db_radioButton.setChecked(True)
        self.dlg.mapconfig_std_radioButton.setChecked(True)

        # Source Data
        self.dlg.extent_pushButton.setDisabled(True)
        self.dlg.bounding_box_top_lineEdit.setDisabled(True)
        self.dlg.bounding_box_left_lineEdit.setDisabled(True)
        self.dlg.bounding_box_right_lineEdit.setDisabled(True)
        self.dlg.bounding_box_bottom_lineEdit.setDisabled(True)
        self.dlg.osm_download_label.setDisabled(True)
        self.dlg.rest_endpoint_lineEdit.setDisabled(True)
        self.dlg.rest_endpoint_test_pushButton.setDisabled(True)

        # Database
        self.dlg.overwrite_checkBox.setDisabled(False)
        self.dlg.db_listWidget.setDisabled(False)
        self.dlg.new_db_name_label.setDisabled(True)
        self.dlg.new_db_name_lineEdit.setDisabled(True)
        self.dlg.new_db_service_label.setDisabled(True)
        self.dlg.new_db_service_lineEdit.setDisabled(True)
        self.dlg.new_db_host_label.setDisabled(True)
        self.dlg.new_db_host_lineEdit.setDisabled(True)
        self.dlg.new_db_port_label.setDisabled(True)
        self.dlg.new_db_port_lineEdit.setDisabled(True)
        self.dlg.new_db_database_label.setDisabled(True)
        self.dlg.new_db_database_lineEdit.setDisabled(True)
        self.dlg.new_db_username_label.setDisabled(True)
        self.dlg.new_db_username_lineEdit.setDisabled(True)
        self.dlg.new_db_password_label.setDisabled(True)
        self.dlg.new_db_password_lineEdit.setDisabled(True)
        self.dlg.new_db_save_username_checkBox.setDisabled(True)
        self.dlg.new_db_save_password_checkBox.setDisabled(True)

        # Schema
        self.dlg.schema_lineEdit.setDisabled(True)

        # Prefix
        self.dlg.prefix_checkBox.setChecked(False)
        self.dlg.prefix_lineEdit.setDisabled(True)

        # Suffix
        self.dlg.suffix_checkBox.setChecked(False)
        self.dlg.suffix_lineEdit.setDisabled(True)

        self.dlg.alt_osm2pgr_exec_lineEdit.setDisabled(True)

        # Database connections
        qs = QSettings()
        k_list = [k for k in sorted(qs.allKeys()) if k[:10] == "PostgreSQL" and k[-8:] == "database"]
        for k in k_list:
            item = QListWidgetItem(k.split("/")[2])
            self.dlg.db_listWidget.addItem(item)

        return None

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginDatabaseMenu(
                self.tr(u'&osm2pgrouting4qgis'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def select_local_osm(self):

        self.dlg.local_file_lineEdit.setDisabled(False)
        self.dlg.local_file_pushButton.setDisabled(False)
        self.dlg.extent_pushButton.setDisabled(True)
        self.dlg.bounding_box_top_lineEdit.setDisabled(True)
        self.dlg.bounding_box_left_lineEdit.setDisabled(True)
        self.dlg.bounding_box_right_lineEdit.setDisabled(True)
        self.dlg.bounding_box_bottom_lineEdit.setDisabled(True)
        self.dlg.osm_download_label.setDisabled(True)
        self.dlg.rest_endpoint_lineEdit.setDisabled(True)
        self.dlg.rest_endpoint_test_pushButton.setDisabled(True)

        return None

    def select_osm_download(self):

        self.dlg.local_file_pushButton.setDisabled(True)
        self.dlg.local_file_lineEdit.setDisabled(True)
        self.dlg.extent_pushButton.setDisabled(False)
        self.dlg.bounding_box_top_lineEdit.setDisabled(False)
        self.dlg.bounding_box_left_lineEdit.setDisabled(False)
        self.dlg.bounding_box_right_lineEdit.setDisabled(False)
        self.dlg.bounding_box_bottom_lineEdit.setDisabled(False)
        self.dlg.osm_download_label.setDisabled(False)
        self.dlg.rest_endpoint_lineEdit.setDisabled(False)
        self.dlg.rest_endpoint_test_pushButton.setDisabled(False)

        return None

    def select_existing_db(self):

        self.dlg.overwrite_checkBox.setDisabled(False)
        self.dlg.db_listWidget.setDisabled(False)
        self.dlg.new_db_name_label.setDisabled(True)
        self.dlg.new_db_name_lineEdit.setDisabled(True)
        self.dlg.new_db_service_label.setDisabled(True)
        self.dlg.new_db_service_lineEdit.setDisabled(True)
        self.dlg.new_db_host_label.setDisabled(True)
        self.dlg.new_db_host_lineEdit.setDisabled(True)
        self.dlg.new_db_port_label.setDisabled(True)
        self.dlg.new_db_port_lineEdit.setDisabled(True)
        self.dlg.new_db_database_label.setDisabled(True)
        self.dlg.new_db_database_lineEdit.setDisabled(True)
        self.dlg.new_db_username_label.setDisabled(True)
        self.dlg.new_db_username_lineEdit.setDisabled(True)
        self.dlg.new_db_password_label.setDisabled(True)
        self.dlg.new_db_password_lineEdit.setDisabled(True)
        self.dlg.new_db_save_username_checkBox.setDisabled(True)
        self.dlg.new_db_save_password_checkBox.setDisabled(True)

        return None

    def select_new_db(self):

        self.dlg.overwrite_checkBox.setDisabled(True)
        self.dlg.db_listWidget.setDisabled(True)
        self.dlg.new_db_name_label.setDisabled(False)
        self.dlg.new_db_name_lineEdit.setDisabled(False)
        self.dlg.new_db_service_label.setDisabled(False)
        self.dlg.new_db_service_lineEdit.setDisabled(False)
        self.dlg.new_db_host_label.setDisabled(False)
        self.dlg.new_db_host_lineEdit.setDisabled(False)
        self.dlg.new_db_port_label.setDisabled(False)
        self.dlg.new_db_port_lineEdit.setDisabled(False)
        self.dlg.new_db_database_label.setDisabled(False)
        self.dlg.new_db_database_lineEdit.setDisabled(False)
        self.dlg.new_db_username_label.setDisabled(False)
        self.dlg.new_db_username_lineEdit.setDisabled(False)
        self.dlg.new_db_password_label.setDisabled(False)
        self.dlg.new_db_password_lineEdit.setDisabled(False)
        self.dlg.new_db_save_username_checkBox.setDisabled(False)
        self.dlg.new_db_save_password_checkBox.setDisabled(False)

        return None

    def toggle_schema(self):

        if self._schema_toggle:
            self.dlg.schema_lineEdit.setDisabled(True)
        else:
            self.dlg.schema_lineEdit.setDisabled(False)

        self._schema_toggle = not self._schema_toggle

        return None

    def toggle_prefix(self):

        if self._prefix_toggle:
            self.dlg.prefix_lineEdit.setDisabled(True)
        else:
            self.dlg.prefix_lineEdit.setDisabled(False)

        self._prefix_toggle = not self._prefix_toggle

        return None

    def toggle_suffix(self):

        if self._suffix_toggle:
            self.dlg.suffix_lineEdit.setDisabled(True)
        else:
            self.dlg.suffix_lineEdit.setDisabled(False)

        self._suffix_toggle = not self._suffix_toggle

        return None

    def toggle_alt_osm2pgr_exec(self):

        if self._alt_osm2pgr_exec_toggle:
            self.dlg.alt_osm2pgr_exec_lineEdit.setDisabled(True)
        else:
            self.dlg.alt_osm2pgr_exec_lineEdit.setDisabled(False)

        self._alt_osm2pgr_exec_toggle = not self._alt_osm2pgr_exec_toggle

        return None

    def open_file_chooser(self):

        filename = QFileDialog.getOpenFileName(self.dlg, "Select .osm file", "", "*.osm")[0]
        if filename:
            self.dlg.local_file_lineEdit.setText(filename)

        return None

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            pass