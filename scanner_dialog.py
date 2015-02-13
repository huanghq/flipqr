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
from PyQt4 import QtGui, QtCore
from os.path import isfile
import zbar
import time
import hashlib
import zlib
import base64
import traceback
import constants as const


class ScannerDialog(QtGui.QDialog):

    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setModal(True)
        self.setupUI()

    def reset(self):
        self.source_id = ''
        self.todo_list = []
        self.done_list = []
        self.is_done = False
        self.is_success = False
        self.total_frames = 0
        self.source_md5 = ''
        self.source_type = 0
        self.source_filename = ''
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.lbl_status.setText('')
        self.btn_scan_finish.setText('Scan')
        self.show()
        QtGui.qApp.processEvents()

    def setupUI(self):

        vbox = QtGui.QVBoxLayout()

        self.progress_bar = QtGui.QProgressBar(self)
        vbox.addWidget(self.progress_bar)
        self.lbl_status = QtGui.QLabel()
        vbox.addWidget(self.lbl_status)
        vbox.addStretch(1)

        self.btn_scan_finish = QtGui.QPushButton("Scan")
        self.btn_scan_finish.clicked.connect(self.onScanFinish)
        # self.btn_scan_finish.setEnabled(False)

        self.btn_cancel = QtGui.QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.onCancel)
        # self.btn_cancel.setEnabled(False)

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.btn_scan_finish)
        hbox.addWidget(self.btn_cancel)

        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.setWindowTitle('Scan')
        self.setFixedSize(300, 100)

    def isFlipQR(self, text):
        return text.startswith('FLIPQR')

    def dataHandler(self, proc, image, closure):
        # only use first symbol
        for symbol in image.symbols:
            break

        if not self.source_id and not self.isFlipQR(symbol.data):
            self.result = str(symbol.data)
            self.progress_bar.setValue(100)
            self.is_done = True
            self.is_success = True
            self.lbl_status.setText('Done')
            self.btn_scan_finish.setText('Finish')

            QtGui.qApp.processEvents()
            return

        # meta format: FLIPQR:source_id:frame number:total
        # frames:md5:source_type:file name
        try:
            frame_data = str(symbol.data).split("\n", 1)
            meta = frame_data[0].split(":")
            if len(meta) < 4:
                return

            if self.source_id and self.source_id != meta[1]:
                return

            content = frame_data[1]
            frame_number = int(meta[2])

            if frame_number == 1:
                self.source_md5 = meta[4]
                self.source_type = int(meta[5])
                self.source_filename = meta[6] if int(
                    meta[5]) != const.TYPE_RAW_TEXT else ""

            if not self.source_id:
                self.source_id = meta[1]
                self.total_frames = int(meta[3])
                self.todo_list = range(1, self.total_frames + 1)
                self.done_list = ['' for i in range(1, self.total_frames + 1)]
                self.progress_bar.setMaximum(self.total_frames)

            if self.done_list[frame_number - 1] != '':
                return

            self.todo_list.remove(frame_number)
            self.done_list[frame_number - 1] = content

            self.progress_bar.setValue(self.total_frames - len(self.todo_list))

            status_text = "Required Frames:" if len(
                self.todo_list) > 1 else "Required Frame:"
            status_text += " %s ..." if len(self.todo_list) > 3 else " %s "
            requires = ",".join(str(i) for i in self.todo_list[0:3])
            self.lbl_status.setText(status_text % requires)

            QtGui.qApp.processEvents()

            # all frames were scanned
            if not self.todo_list and self.source_id:
                self.is_done = True
                self.lbl_status.setText('Done')
                self.btn_scan_finish.setText('Finish')

                QtGui.qApp.processEvents()

                if self.source_type == const.TYPE_RAW_TEXT:
                    self.result = "".join(self.done_list)
                    if hashlib.md5(self.result).hexdigest() == self.source_md5:
                        self.is_success = True
                        self.stopScan()
                        return
                    else:
                        QtGui.QMessageBox.information(
                            self, 'FlipQR', 'md5 verify failed,please rescan')
                        self.stopScan()
                        return

                else:
                    result = "".join(self.done_list)
                    try:
                        result = base64.b64decode(result)
                        if self.source_type == const.TYPE_ZIP_BASE64_FILE:
                            result = zlib.decompress(result)
                        self.result = result
                    except:
                        QtGui.QMessageBox.information(
                            self, 'FlipQR', 'Decode failed')
                        self.stopScan()
                        return

                    if hashlib.md5(self.result).hexdigest() == self.source_md5:
                        self.is_success = True
                        self.stopScan()
                        return
                    else:
                        QtGui.QMessageBox.information(
                            self, 'FlipQR', 'md5 verify failed,please rescan')
                        self.stopScan()
                        return

        except Exception, e:
            pass
            # print traceback.print_exc()

    def saveFile(self):
        fd = QtGui.QFileDialog(self)
        savefile = unicode(
            fd.getSaveFileName(self, '', unicode(self.source_filename, "utf-8")))
        if savefile:
            fh = open(savefile, 'wb')
            fh.write(self.result)
            fh.close()
        self.accept()

    def initScan(self):

        if not hasattr(self, 'proc'):
            self.proc = zbar.Processor()
            self.proc.parse_config('enable')
            self.device = ''
            try:
                self.proc.init(self.device)
                self.proc.set_data_handler(self.dataHandler)
                self.proc.active = True
            except:
                QtGui.QMessageBox.information(self, 'FlipQR',
                                              "Scan process initialize failed")
        else:
            pass

    def startScan(self):
        self.proc.visible = True
        self.setEnabled(False)
        QtGui.qApp.processEvents()
        try:
            ret = self.proc.user_wait()
        except:
            pass

        self.proc.visible = False
        self.setEnabled(True)

        if self.is_done and not self.is_success:
            self.reject()

    def stopScan(self):
        if hasattr(self.proc, 'cancel_process'):
            self.proc.cancel_process()
        else:
            pass

    def onScanFinish(self):
        if self.is_done:
            if self.source_type == const.TYPE_RAW_TEXT:
                self.accept()
            else:
                self.saveFile()
        else:
            self.scan()

    def scan(self):
        self.setEnabled(False)
        self.initScan()
        self.startScan()

    def onCancel(self):
        if self.source_id or self.is_done:
            reply = QtGui.QMessageBox.question(self, "FlipQR",
                                               "Are you sure to cancel?\n discarge unsaved data?",
                                               QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.Yes:
                self.reject()
            else:
                pass
        else:
            self.reject()

    def closeEvent(self, event):
        event.ignore()
