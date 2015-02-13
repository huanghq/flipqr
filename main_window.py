#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# FlipQR - transfer data over an air gap
# Copyright GPLv2 2015 Huang Hongqing (hhqyn@hotmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import sys
import codecs
import hashlib
import zlib
import base64
from os.path import isfile, getsize, basename

from PyQt4 import QtGui, QtCore
import icons_rc
from player_dialog import PlayerDialog
from scanner_dialog import ScannerDialog

import constants as const

try:
    import zbar
except ImportError:
    zbar = None

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle('FlipQR')
        self.setWindowIcon(QtGui.QIcon(':icons/flipqr.png'))
        self.setupUI()

    def setupUI(self):

        self.editor = QtGui.QPlainTextEdit()
        self.editor.document().setDefaultFont(
            QtGui.QFont(self.font().family(), 12))
        self.setCentralWidget(self.editor)

        self.statusBar()

        self.toolbar = self.addToolBar('toolbar')
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

        action = QtGui.QAction(QtGui.QIcon(':icons/open.png'), 'Open', self)
        action.setShortcut('Ctrl+O')
        action.setStatusTip('Open file')
        action.triggered.connect(self.onOpen)
        self.toolbar.addAction(action)

        action = QtGui.QAction(QtGui.QIcon(':icons/save.png'), 'Save', self)
        action.setShortcut('Ctrl+S')
        action.setStatusTip('Save as')
        action.triggered.connect(self.onSave)
        self.toolbar.addAction(action)

        action = QtGui.QAction(
            QtGui.QIcon(':icons/qrtext.png'), 'QR Text', self)
        action.setStatusTip('Convert text to QR code')
        action.triggered.connect(self.onConvertText)
        self.toolbar.addAction(action)

        action = QtGui.QAction(
            QtGui.QIcon(':icons/qrfile.png'), 'QR File', self)
        action.setStatusTip('Convert file to QR code')
        action.triggered.connect(self.onConvertFile)
        self.toolbar.addAction(action)

        action = QtGui.QAction(QtGui.QIcon(':icons/scan.png'), 'Scan', self)
        action.setStatusTip('Scan code')
        action.triggered.connect(self.onScan)
        self.scan_action = action
        self.toolbar.addAction(action)

        action = QtGui.QAction(QtGui.QIcon(':icons/about.png'), 'About', self)
        action.setStatusTip('About')
        action.triggered.connect(self.onAbout)
        self.toolbar.addAction(action)

        action = QtGui.QAction(QtGui.QIcon(':icons/exit.png'), 'Exit', self)
        action.setStatusTip('Exit application')
        action.triggered.connect(self.onExit)
        action.setShortcut('Ctrl+W')
        self.toolbar.addAction(action)

        self.setGeometry(300, 300, 600, 300)
        self.center()
        self.show()

        if not zbar:
            QtGui.QMessageBox.information(self, 'FlipQR',
                                            "Python zbar package not found, scan feature is disabled.")
            self.scan_action.setEnabled(False)


    def openFileDialog(self):
        fd = QtGui.QFileDialog(self)
        filename = unicode(fd.getOpenFileName())
        if isfile(filename):
            if getsize(filename) > const.MAX_FILE_SIZE:
                QtGui.QMessageBox.information(self, 'FlipQR', "File size can't greater than %d M" %
                                              (const.MAX_FILE_SIZE / 1000 ** 2))
                return False
            return filename
        else:
            return False

    def onOpen(self):
        fn = self.openFileDialog()
        if fn:
            self.filename = fn
            try:
                text = codecs.open(self.filename, 'r', 'utf-8').read()
                self.editor.setPlainText(text)
            except UnicodeDecodeError:
                QtGui.QMessageBox.information(self, 'FlipQR',
                                              "To convert binary file, please use QR File button")

    def onSave(self):
        fd = QtGui.QFileDialog(self)
        savefile = unicode(fd.getSaveFileName())

        if savefile:
            fh = codecs.open(savefile, 'w', 'utf-8')
            fh.write(unicode(self.editor.toPlainText()))
            fh.close()
            self.filename = savefile

    def onConvertText(self):
        text = unicode(self.editor.toPlainText())

        if not text:
            QtGui.QMessageBox.information(
                self, 'FlipQR', "No content to convert")
            return True

        src_md5 = hashlib.md5(text.encode('utf-8')).hexdigest()
        source = {
            "id": src_md5[0:6],
            "data": text,
            "type": const.TYPE_RAW_TEXT,
            "md5": src_md5,
        }

        PlayerDialog(self, source).exec_()

    def onConvertFile(self):
        fn = self.openFileDialog()
        if fn:
            self.filename = fn
            fh = open(self.filename, "rb")
            raw = fh.read()
            fh.close()
            if not len(raw):
                return
            src_md5 = hashlib.md5(raw).hexdigest()
            compressed = zlib.compress(raw)
            if float(len(compressed)) / len(raw) < const.ZIP_RATIO_THRESHOLD:
                data = base64.b64encode(compressed)
                src_type = const.TYPE_ZIP_BASE64_FILE
            else:
                data = base64.b64encode(raw)
                src_type = const.TYPE_BASE64_FILE

            source = {
                "id": src_md5[0:6],
                "data": data,
                "type": src_type,
                "md5": src_md5,
                "filename": basename(self.filename),
            }

            PlayerDialog(self, source).exec_()

    def onScan(self):
        if not hasattr(self, "scanner"):
            self.scanner = ScannerDialog(self)
            self.scanner.setModal(True)

        self.scanner.reset()
        return_code = self.scanner.exec_()
        if return_code == QtGui.QDialog.Accepted and self.scanner.source_type == const.TYPE_RAW_TEXT:
            self.editor.setPlainText(unicode(self.scanner.result, "utf-8"))

    def onAbout(self):
        QtGui.QMessageBox.about(self, "FlipQR", "Version:%s <br><br>%s" % (
                                const.FLIPQR_VERSION,
                                "FlipQR, a simple tool to transfer long text or small file by QR code animations when physical network connection is not available.<br><br> ")
                                + "Source: <a href=\"https://github.com/huanghq/flipqr\">https://github.com/huanghq/flipqr</a><br>Coypright: GPLv2 2015")

    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def onExit(self):
        QtCore.QCoreApplication.instance().quit()
