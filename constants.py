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

# constants
MAX_FILE_SIZE = 2 * 1000 * 1000
TYPE_RAW_TEXT = 0
TYPE_BASE64_FILE = 1
TYPE_ZIP_BASE64_FILE = 2
ZIP_RATIO_THRESHOLD = 0.9

FLIPQR_VERSION = 0.1
