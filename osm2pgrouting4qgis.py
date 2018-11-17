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
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtWidgets import QAction, QListWidgetItem, QFileDialog
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY, QgsMapSettings, QgsProject, \
    QgsDataSourceUri, QgsApplication

# Initialize Qt resources from file resources.py
# from .resources import *
# Import the code for the dialog
from .osm2pgrouting4qgis_dialog import osm2pgrouting4qgisDialog
import os.path

from psycopg2 import connect as dbconnect, sql
import requests
import subprocess
import sys


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

        # Toggle add attributes / add nodes
        self._attributes_and_tags_toggle = False
        self.dlg.nodes_checkBox.setChecked(False)
        self.dlg.nodes_checkBox.clicked.connect(self.toggle_attributes_and_tags)

        # Toggle alternative osm2pgr executable
        self._alt_osm2pgr_exec_toggle = False
        self.dlg.alt_osm2pgr_exec_checkBox.setChecked(False)
        self.dlg.alt_osm2pgr_exec_checkBox.clicked.connect(self.toggle_alt_osm2pgr_exec)

        # Only integers allowed for chunk size
        self.onlyInt = QIntValidator()
        self.dlg.chunk_size_lineEdit.setValidator(self.onlyInt)

        # Set up file chooser
        self.dlg.local_file_pushButton.clicked.connect(self.open_file_chooser)

        # Make "Current Extent" button generate the current extent in their respective lineEdits
        self.dlg.extent_pushButton.clicked.connect(self.use_current_extent)

        # Make REST endpoint test button test the endpoint
        self.dlg.rest_endpoint_test_pushButton.clicked.connect(self.test_rest_endpoint)

        # Set up initial GUI state
        self.set_initial_state()

        # cd to the plugin home folder
        os.chdir(os.path.join(QgsApplication.qgisSettingsDirPath(), r"python/plugins/osm2pgrouting4qgis"))


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

        # Add attributes / add nodes
        self.dlg.add_attributes_checkBox.setDisabled(True)
        self.dlg.add_tags_checkBox.setDisabled(True)
        self.dlg.addnodes_tree_decoration1.setDisabled(True)
        self.dlg.addnodes_tree_decoration2.setDisabled(True)
        self.dlg.addnodes_tree_decoration3.setDisabled(True)

        # Alternate osm2pgr exec
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

    def toggle_attributes_and_tags(self):

        if self._attributes_and_tags_toggle:
            self.dlg.add_attributes_checkBox.setDisabled(True)
            self.dlg.add_tags_checkBox.setDisabled(True)
            self.dlg.add_attributes_checkBox.setChecked(False)
            self.dlg.add_tags_checkBox.setChecked(False)
            self.dlg.addnodes_tree_decoration1.setDisabled(True)
            self.dlg.addnodes_tree_decoration2.setDisabled(True)
            self.dlg.addnodes_tree_decoration3.setDisabled(True)
        else:
            self.dlg.add_attributes_checkBox.setDisabled(False)
            self.dlg.add_tags_checkBox.setDisabled(False)
            self.dlg.addnodes_tree_decoration1.setDisabled(False)
            self.dlg.addnodes_tree_decoration2.setDisabled(False)
            self.dlg.addnodes_tree_decoration3.setDisabled(False)

        self._attributes_and_tags_toggle = not self._attributes_and_tags_toggle

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

    def test_rest_endpoint(self):

        rest_url = self.dlg.rest_endpoint_lineEdit.text()
        req = requests.get(r"{}?bbox=0,0.0001,0,0.0001".format(rest_url))

        if req.ok:
            self.dlg.rest_endpoint_test_label.setStyleSheet("font: bold 14px; color: green;")
        else:
            self.dlg.rest_endpoint_test_label.setStyleSheet("font: bold 14px; color: red;")

        self.dlg.rest_endpoint_test_label.setText("{}: {}".format(req.status_code, req.reason))

        return None

    def use_current_extent(self):

        # Get current CRS and set up a CRS transformer for the current CRS and WGS84 (EPSG: 4326)
        canvas = self.iface.mapCanvas()
        # current_crs = canvas.mapRenderer().destinationCrs().authid()
        current_crs = canvas.mapSettings().destinationCrs()
        source_crs = QgsCoordinateReferenceSystem(current_crs)
        target_crs = QgsCoordinateReferenceSystem(4326)
        transformer = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())

        # Get current extent and transform to WGS84
        extent = self.iface.mapCanvas().extent()
        bottom_left_point = QgsPointXY(extent.xMinimum(), extent.yMinimum())
        top_right_point = QgsPointXY(extent.xMaximum(), extent.yMaximum())
        bottom_left_point_transformed = transformer.transform(bottom_left_point)
        top_right_point_transformed = transformer.transform(top_right_point)

        # Extract extent boundaries
        top = top_right_point_transformed.y()
        left = bottom_left_point_transformed.x()
        right = top_right_point_transformed.x()
        bottom = bottom_left_point_transformed.y()

        # Populate extent lineEdits
        self.dlg.bounding_box_top_lineEdit.setText(str(top))
        self.dlg.bounding_box_left_lineEdit.setText(str(left))
        self.dlg.bounding_box_right_lineEdit.setText(str(right))
        self.dlg.bounding_box_bottom_lineEdit.setText(str(bottom))

        return None

    def make_new_database(self, dbname, host, port, user, password):

        # Log into maintenance database and create the new DB
        # TODO: parameterize maintenance DB (even though it will almost certainly be "postgres")
        conn_string = "dbname=postgres host={0} port={1} user={2} password={3}".format(host, port, user, password)
        with dbconnect(conn_string) as conn:
            conn.autocommit = True  # connection MUST be in autocommit mode to create databases!
            cur = conn.cursor()
            cur.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(dbname)))
            conn.commit()
            cur.close()

        # Add the connection to QGIS
        settings = QSettings()
        settings.setValue("PostgreSQL/connections/{0}/allowGeometrylessTables".format(self.db_credentials["name"]),
                          "false")
        settings.setValue("PostgreSQL/connections/{0}/authcfg".format(self.db_credentials["name"]), "")
        settings.setValue("PostgreSQL/connections/{0}/database".format(self.db_credentials["name"]),
                          self.db_credentials["dbname"])
        settings.setValue("PostgreSQL/connections/{0}/dontResolveType".format(self.db_credentials["name"]), "false")
        settings.setValue("PostgreSQL/connections/{0}/estimatedMetadata".format(self.db_credentials["name"]), "false")
        settings.setValue("PostgreSQL/connections/{0}/geometryColumnsOnly".format(self.db_credentials["name"]), "false")
        settings.setValue("PostgreSQL/connections/{0}/host".format(self.db_credentials["name"]),
                          self.db_credentials["host"])
        settings.setValue("PostgreSQL/connections/{0}/password".format(self.db_credentials["name"]),
                          self.db_credentials["password"])
        settings.setValue("PostgreSQL/connections/{0}/port".format(self.db_credentials["name"]),
                          self.db_credentials["port"])
        settings.setValue("PostgreSQL/connections/{0}/publicOnly".format(self.db_credentials["name"]), "false")
        settings.setValue("PostgreSQL/connections/{0}/savePassword".format(self.db_credentials["name"]),
                          self.db_credentials["save_password"])
        settings.setValue("PostgreSQL/connections/{0}/saveUsername".format(self.db_credentials["name"]),
                          self.db_credentials["save_username"])
        settings.setValue("PostgreSQL/connections/{0}/service".format(self.db_credentials["name"]),
                          self.db_credentials["service"])
        settings.setValue("PostgreSQL/connections/{0}/sslmode".format(self.db_credentials["name"]), "1")
        settings.setValue("PostgreSQL/connections/{0}/username".format(self.db_credentials["name"]),
                          self.db_credentials["user"])
        QCoreApplication.processEvents()  # refresh browser panel

        return None

    def make_db_schema(self, dbname, host, port, user, password, schema):

        conn_string = "dbname={0} host={1} port={2} user={3} password={4}".format(dbname, host, port, user, password)
        with dbconnect(conn_string) as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {};").format(sql.Identifier(schema)))
            conn.commit()
            cur.close()

        return None

    def make_db_extensions(self, dbname, host, port, user, password):

        conn_string = "dbname={0} host={1} port={2} user={3} password={4}".format(dbname, host, port, user, password)
        with dbconnect(conn_string) as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS pgrouting;"))
            conn.commit()
            cur.close()

        return None

    def download_osm_data(self, rest_url, bbox):

        req = requests.get(r"{}?bbox={},{},{},{}"
                           .format(rest_url, bbox[0], bbox[1], bbox[2], bbox[3]))
        with open(os.path.join(os.getcwd(), r"osm/data.osm"), "w") as osm_file:
            osm_file.write(req.text)
            osm_file_path = osm_file.name

        return osm_file_path

    def get_db_credentials(self, db_name):

        db_credentials = {}
        qs = QSettings()
        k_list = [k for k in sorted(qs.allKeys()) if k[:10] == "PostgreSQL" and k.split("/")[2] == db_name]
        for k in k_list:
            if k.split("/")[-1] == "database":
                db_credentials["dbname"] = qs.value(k)
            elif k.split("/")[-1] == "host":
                db_credentials["host"] = qs.value(k)
            elif k.split("/")[-1] == "port":
                db_credentials["port"] = qs.value(k)
            elif k.split("/")[-1] == "username":
                db_credentials["user"] = qs.value(k)
            elif k.split("/")[-1] == "password":
                db_credentials["password"] = qs.value(k)

        return db_credentials

    def add_hstore(self, dbname, host, port, user, password):

        conn_string = "dbname={0} host={1} port={2} user={3} password={4}".format(dbname, host, port, user, password)
        with dbconnect(conn_string) as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("CREATE EXTENSION IF NOT EXISTS hstore;"))
            conn.commit()
            cur.close()

        return None

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:

            # Get osm file either localy or from REST endpoint
            # TODO: requesting too much data puts an error in data.osm, check for this and inform the user
            if self.dlg.local_file_radioButton.isChecked():
                osm_file = self.dlg.local_file_lineEdit.text()
            elif self.dlg.osm_download_radioButton.isChecked():
                osm_bbox = [float(self.dlg.bounding_box_left_lineEdit.text()),
                            float(self.dlg.bounding_box_bottom_lineEdit.text()),
                            float(self.dlg.bounding_box_right_lineEdit.text()),
                            float(self.dlg.bounding_box_top_lineEdit.text())]
                osm_rest_endpoint = self.dlg.rest_endpoint_lineEdit.text()
                osm_file = self.download_osm_data(osm_rest_endpoint, osm_bbox)

            # Get credentials if a pre-existing connection from QGIS was selected
            if self.dlg.existing_db_radioButton.isChecked():
                db_name = self.dlg.db_listWidget.currentItem().text()
                self.db_credentials = self.get_db_credentials(db_name)

            # Define credentials from dialog and create database if new connection was selected
            elif self.dlg.new_db_radioButton.isChecked():
                self.db_credentials = {
                    "name": self.dlg.new_db_name_lineEdit.text(),
                    "service": self.dlg.new_db_service_lineEdit.text(),
                    "host": self.dlg.new_db_host_lineEdit.text(),
                    "port": self.dlg.new_db_port_lineEdit.text(),
                    "dbname": self.dlg.new_db_database_lineEdit.text(),
                    "user": self.dlg.new_db_username_lineEdit.text(),
                    "password": self.dlg.new_db_password_lineEdit.text(),
                    "save_username": "true" if self.dlg.new_db_save_username_checkBox.isChecked() else False,
                    "save_password": "true" if self.dlg.new_db_save_password_checkBox.isChecked() else False,
                    "schema": self.dlg.schema_lineEdit if self.dlg.schema_checkBox.isChecked() else "public",
                }

                self.make_new_database(self.db_credentials["dbname"], self.db_credentials["host"],
                                       self.db_credentials["port"], self.db_credentials["user"],
                                       self.db_credentials["password"])

            # Set map config
            if self.dlg.mapconfig_std_radioButton.isChecked():
                map_config = os.path.join(os.getcwd(), r"map_configs/mapconfig.xml")
            elif self.dlg.mapconfig_cars_radioButton.isChecked():
                map_config = os.path.join(os.getcwd(), r"map_configs/mapconfig_for_cars.xml")
            elif self.dlg.mapconfig_bicycles_radioButton.isChecked():
                map_config = os.path.join(os.getcwd(), r"map_configs/mapconfig_for_bicycles.xml")

            # Add the custom schema if it does not exist & the user specified it
            if self.dlg.schema_checkBox.isChecked():
                schema = self.dlg.schema_lineEdit.text()
                self.make_db_schema(self.db_credentials["dbname"], self.db_credentials["host"],
                                       self.db_credentials["port"], self.db_credentials["user"],
                                       self.db_credentials["password"], schema)
            else:
                schema = "public"

            # Add postgis & pgrouting extensions
            self.make_db_extensions(self.db_credentials["dbname"], self.db_credentials["host"],
                                       self.db_credentials["port"], self.db_credentials["user"],
                                       self.db_credentials["password"])

            # Add hstore extension in case the user specified --attributes or --tags
            if self.dlg.add_attributes_checkBox.isChecked() or self.dlg.add_tags_checkBox.isChecked():
                self.add_hstore(self.db_credentials["dbname"], self.db_credentials["host"],
                                       self.db_credentials["port"], self.db_credentials["user"],
                                       self.db_credentials["password"])

            # Set custom executable if applicable
            if self.dlg.alt_osm2pgr_exec_checkBox.isChecked() and self.dlg.alt_osm2pgr_exec_lineEdit.text() is not None:
                osm2pgr_exec = self.dlg.alt_osm2pgr_exec_lineEdit.text()
            else:
                osm2pgr_exec = "osm2pgrouting"

            # Build command line statement
            osm2pgrouting_parameters = [
                osm2pgr_exec,
                "--file", osm_file,
                "--conf", map_config,
                "--schema", schema,
                "--dbname", self.db_credentials["dbname"],
                "--host", self.db_credentials["host"],
                "--username", self.db_credentials["user"],
                "--password", self.db_credentials["password"],
                "--chunk", self.dlg.chunk_size_lineEdit.text()
            ]
            if self.dlg.overwrite_checkBox.isChecked():
                osm2pgrouting_parameters.append("--clean")
            if self.dlg.nodes_checkBox.isChecked():
                osm2pgrouting_parameters.append("--addnodes")
            if self.dlg.no_index_checkBox.isChecked():
                osm2pgrouting_parameters.append("--no-index")
            if self.dlg.prefix_checkBox.isChecked():
                osm2pgrouting_parameters.extend(["--prefix", self.dlg.prefix_lineEdit.text().lower()])
            if self.dlg.suffix_checkBox.isChecked():
                osm2pgrouting_parameters.extend(["--suffix", self.dlg.suffix_lineEdit.text().lower()])
            if self.dlg.add_attributes_checkBox.isChecked():
                osm2pgrouting_parameters.extend(["--attributes", self.dlg.suffix_lineEdit.text().lower()])
            if self.dlg.add_tags_checkBox.isChecked():
                osm2pgrouting_parameters.extend(["--tags", self.dlg.suffix_lineEdit.text().lower()])

            print("executing: {}".format(" ".join(osm2pgrouting_parameters)))

            # Execute command line statement
            osm2pgrouting_process = subprocess.Popen(osm2pgrouting_parameters, stdout=subprocess.PIPE)
            for line in iter(osm2pgrouting_process.stdout.readline, ''):
                if str(line) != "b''":
                    sys.stdout.write(str(line))
                else:
                    break

            # Remove the file only if it was downloaded
            if self.dlg.osm_download_radioButton.isChecked():
                # os.remove(osm_file)
                pass
