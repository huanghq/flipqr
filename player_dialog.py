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
from os.path import isfile
import codecs
import qrcode
import math

from PyQt4 import QtGui, QtCore
from image_factory import ImageFactory
import constants as const


class PlayerDialog(QtGui.QDialog):

    def __init__(self, parent, source):
        QtGui.QDialog.__init__(self, parent)
        self.setModal(True)
        self.source = source

        self.ecc_dict = {
            '7%': qrcode.constants.ERROR_CORRECT_L,
            '15%': qrcode.constants.ERROR_CORRECT_M,
            '25%': qrcode.constants.ERROR_CORRECT_Q,
            '30%': qrcode.constants.ERROR_CORRECT_H
        }

        self.options = {
            "ecc": ["7%", "15%", "25%", "30%"],
            "image_size":  [str(i) for i in range(1, 11)],
            "frame_size": [str(i * 100) for i in range(1, 21)],
            "fps":  [str(i) for i in range(1, 11)],
        }

        self.settings = {
            "ecc": "7%",
            "image_size": "5",
            "frame_size": "100",
            "fps": "1",
        }
        self.timer = QtCore.QBasicTimer()
        self.setupUI()
        self.updateSettings()

    def setupUI(self):

        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()

        hbox.addWidget(QtGui.QLabel(' ECC: '))

        combo = QtGui.QComboBox()
        combo.addItems(self.options["ecc"])
        ci = self.options["ecc"].index(self.settings["ecc"])
        combo.setCurrentIndex(ci)
        combo.activated[str].connect(self.onSetEcc)
        hbox.addWidget(combo)

        hbox.addWidget(QtGui.QLabel(' Image Pixels: '))
        combo = QtGui.QComboBox()
        combo.addItems(self.options["image_size"])
        ci = self.options["image_size"].index(self.settings["image_size"])
        combo.setCurrentIndex(ci)
        combo.activated[str].connect(self.onSetImageSize)
        hbox.addWidget(combo)

        hbox.addWidget(QtGui.QLabel(' Frame Bytes: '))

        combo = QtGui.QComboBox()
        combo.addItems(self.options["frame_size"])
        ci = self.options["frame_size"].index(self.settings["frame_size"])
        combo.setCurrentIndex(ci)
        combo.activated[str].connect(self.onSetFrameSize)
        hbox.addWidget(combo)

        hbox.addWidget(QtGui.QLabel(' FPS: '))
        self.combo_fps = QtGui.QComboBox()
        self.combo_fps.addItems(self.options["fps"])
        ci = self.options["fps"].index(self.settings["fps"])
        self.combo_fps.setCurrentIndex(ci)
        self.combo_fps.activated[str].connect(self.onSetFPS)
        hbox.addWidget(self.combo_fps)

        self.icon_play = QtGui.QIcon(":icons/play.png")
        self.icon_pause = QtGui.QIcon(":icons/pause.png")

        self.btn_play_pause = QtGui.QPushButton()
        self.btn_play_pause.setIcon(self.icon_play)

        self.btn_play_pause.clicked.connect(self.onPlayPause)

        self.btn_next = QtGui.QPushButton()
        self.btn_next.setIcon(QtGui.QIcon(":icons/next.png"))
        self.btn_next.clicked.connect(self.onNext)

        self.btn_prev = QtGui.QPushButton()
        self.btn_prev.setIcon(QtGui.QIcon(":icons/previous.png"))
        self.btn_prev.clicked.connect(self.onPrevious)
        hbox.addWidget(self.btn_prev)
        hbox.addWidget(self.btn_play_pause)
        hbox.addWidget(self.btn_next)

        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.setMinimum(1)
        self.slider.setMaximum(1)
        self.slider.valueChanged[int].connect(self.sliderValueChanged)

        hbox.addWidget(self.slider)
        vbox.addLayout(hbox)

        vbox.setAlignment(QtCore.Qt.AlignTop)

        self.lbl_qr = QtGui.QLabel('')
        self.lbl_qr.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(self.lbl_qr)

        self.lbl_info = QtGui.QLabel('')
        self.lbl_info.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(self.lbl_info)

        self.setLayout(vbox)
        if self.source['type'] == 0:
            title = 'FlipQR text'
        else:
            title = 'FlipQR file:' + self.source['filename']

        self.setWindowTitle(title)
        self.show()

    def timerEvent(self, e):
        self.onNext()

    def sliderValueChanged(self, value):
        self.paintQR(value)

    def updateSettings(self):
        self.current_frame = 1

        self.timer.stop()
        self.btn_play_pause.setIcon(self.icon_play)

        total = float(len(self.source['data'])) / \
            int(self.settings['frame_size'])

        self.total_frame = int(math.ceil(total))
        self.is_static = int(self.settings['frame_size']) >= len(
            self.source['data'])
        self.slider.setMaximum(self.total_frame)
        self.updateUIStatus()
        self.paintQR(self.current_frame)

    def updateUIStatus(self):
        if self.is_static:
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            self.btn_play_pause.setEnabled(False)
            self.combo_fps.setEnabled(False)
            self.slider.setEnabled(False)
        else:
            self.btn_prev.setEnabled(True)
            self.btn_next.setEnabled(True)
            self.btn_play_pause.setEnabled(True)
            self.combo_fps.setEnabled(True)
            self.slider.setEnabled(True)

    def onSetEcc(self, text):
        self.settings['ecc'] = str(text)
        self.updateSettings()

    def onSetImageSize(self, text):
        self.settings['image_size'] = str(text)
        self.updateSettings()

    def onSetFrameSize(self, text):
        self.settings['frame_size'] = str(text)
        self.updateSettings()

    def onSetFPS(self, text):
        self.settings['fps'] = str(text)
        self.updateSettings()

    def onPlayPause(self):
        delay = 1000 / int(self.settings['fps'])
        if self.timer.isActive():
            self.timer.stop()
            self.btn_play_pause.setIcon(self.icon_play)

        else:
            self.timer.start(delay, self)
            self.btn_play_pause.setIcon(self.icon_pause)

    def onNext(self):
        if self.current_frame == self.total_frame:
            self.current_frame = 1
        else:
            self.current_frame += 1

        self.paintQR(self.current_frame)

    def onPrevious(self):
        if self.current_frame == 1:
            self.current_frame = self.total_frame
        else:
            self.current_frame -= 1

        self.paintQR(self.current_frame)

    def paintQR(self, number):
        self.current_frame = number
        self.slider.setValue(number)

        if self.is_static and self.source['type'] == 0:
            qrtext = self.source['data'].encode('utf-8')
        else:
            from_ = (self.current_frame - 1) * int(self.settings['frame_size'])
            to = min(len(self.source['data']),
                     from_ + int(self.settings['frame_size']))
            qrtext = self.source['data'][from_:to].encode('utf-8')

            if self.current_frame == 1:
                # convert file
                if self.source["type"] == const.TYPE_RAW_TEXT:
                    meta = "FLIPQR:%s:%d:%d:%s:%d\n" % (self.source["id"], self.current_frame,
                                                        self.total_frame, self.source["md5"], self.source["type"])
                else:
                    meta = "FLIPQR:%s:%d:%d:%s:%d:%s\n" % (self.source["id"], self.current_frame,
                                                           self.total_frame, self.source["md5"], self.source["type"], self.source["filename"])
            else:
                meta = "FLIPQR:%s:%d:%d\n" % (
                    self.source["id"], self.current_frame, self.total_frame)

            qrtext = meta + qrtext

        ecc = self.ecc_dict[self.settings['ecc']]
        qr = qrcode.QRCode(
            error_correction=ecc,
            box_size=int(self.settings['image_size']),
            border=4,
            image_factory=ImageFactory
        )

        qr.add_data(qrtext)
        qr.make(fit=True)

        self.lbl_qr.setPixmap(
            qr.make_image().pixmap())

        info = "%d / %d" % (self.current_frame, self.total_frame)
        self.lbl_info.setText(info)
