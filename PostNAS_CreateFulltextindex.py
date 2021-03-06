# -*- coding: utf-8 -*-
"""
/***************************************************************************
    PostNAS_Search
    -------------------
    Date                : June 2016
    copyright          : (C) 2016 by Kreis-Unna
    email                : marvin.kinberger@kreis-unna.de
 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtSql import *
from qgis.PyQt.QtWidgets import *
from qgis.core import *
import qgis.core

class PostNAS_CreateFulltextindex(QDialog):
    def __init__(self, iface, parent=None):
        super(PostNAS_CreateFulltextindex, self).__init__(parent)
        self.dialog = uic.loadUi(os.path.join(os.path.dirname(__file__), 'PostNAS_FulltextindexInProgress.ui'))

    def exec_(self):
        self.openDialog()
        self.createFulltextindex()
        self.coloseDialog()

    def openDialog(self):
        self.dialog.setModal(True)
        self.dialog.show()
        QApplication.processEvents()

    def coloseDialog(self):
        self.dialog.close()

    def createFulltextindex(self):
        if(self.checkPostnasSeachTable() == False):
            if(self.createIndexTable() == False):
                QMessageBox.critical(None,"Fehler",u"Indextabelle wurde nicht angelegt.\r\nPrüfen Sie die Schreibrechte des Datenbankbenutzers.")
                return False
        self.updateIndex()

    def createIndexTable(self):
        file_path = os.path.dirname(os.path.realpath(__file__)) + "/create_fulltexttable/create_table.sql"
        sql = open(file_path).read()

        if(hasattr(self,"db") == False):
            self.loadDbSettings()
            if(self.db.isOpen() == False):
                self.db.open()
        self.queryCreate = QSqlQuery(self.db)
        self.queryCreate.exec_(sql)

        if(self.queryCreate.lastError().number() == -1):
            return True
        else:
            return False

    def updateIndex(self):
        file_path = os.path.dirname(os.path.realpath(__file__)) + "/postprocessing_import/postnas-search-fulltextindex.sql"
        sql = open(file_path).read()

        if(hasattr(self,"db") == False):
            self.loadDbSettings()
            if(self.db.isOpen() == False):
                self.db.open()
        self.query = QSqlQuery(self.db)
        self.query.exec_(sql)
        if(self.query.lastError().number() != -1):
            QgsMessageLog.logMessage("Datenbankfehler beim Erzeugen des Volltextindex: " + self.query.lastError().text(),'PostNAS-Suche', Qgis.Critical)
        self.db.close()

    def checkPostnasSeachTable(self):
        sql = "SELECT table_name FROM information_schema.tables WHERE table_name = 'postnas_search'";

        if(hasattr(self,"db") == False):
            self.loadDbSettings()
            if(self.db.isOpen() == False):
                self.db.open()
        query = QSqlQuery(self.db)
        query.exec_(sql)

        if(query.size() > 0):
            return True
        else:
            return False

    def loadDbSettings(self):
        settings = QSettings("PostNAS", "PostNAS-Suche")

        self.dbHost = settings.value("host", "")
        self.dbDatabasename = settings.value("dbname", "")
        self.dbPort = settings.value("port", "5432")
        self.dbUsername = settings.value("user", "")
        self.dbPassword = settings.value("password", "")

        authcfg = settings.value( "authcfg", "" )

        if authcfg != "" and hasattr(qgis.core,'QgsAuthManager'):
            amc = qgis.core.QgsAuthMethodConfig()
            qgis.core.QgsAuthManager.instance().loadAuthenticationConfig( authcfg, amc, True)
            self.dbUsername = amc.config( "username", self.dbUsername )
            self.dbPassword = amc.config( "password", self.dbPassword )

        self.db = QSqlDatabase.addDatabase("QPSQL")
        self.db.setHostName(self.dbHost)
        self.db.setPort(int(self.dbPort))
        self.db.setDatabaseName(self.dbDatabasename)
        self.db.setUserName(self.dbUsername)
        self.db.setPassword(self.dbPassword)
