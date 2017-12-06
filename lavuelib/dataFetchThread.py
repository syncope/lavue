# Copyright (C) 2017  DESY, Christoph Rosemann, Notkestr. 85, D-22607 Hamburg
#
# lavue is an image viewing program for photon science imaging detectors.
# Its usual application is as a live viewer using hidra as data source.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation in  version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
#
# Authors:
#     Christoph Rosemann <christoph.rosemann@desy.de>
#     Jan Kotanski <jan.kotanski@desy.de>
#

""" data fetch thread """

from __future__ import print_function
from __future__ import unicode_literals

import time

from PyQt4 import QtCore


# magic numbers:
GLOBALREFRESHRATE = .1  # refresh rate if the data source is running in seconds


# subclass for data caching
class ExchangeList(object):

    def __init__(self):
        self.__elist = [None, None]
        self.__mutex = QtCore.QMutex()

    def addData(self, name, data):
        with QtCore.QMutexLocker(self.__mutex):
            self.__elist[0] = name
            self.__elist[1] = data

    def readData(self):
        with QtCore.QMutexLocker(self.__mutex):
            a, b = self.__elist[0], self.__elist[1]
        return a, b


# subclass for threading
class DataFetchThread(QtCore.QThread):
    newDataName = QtCore.pyqtSignal(str)

    def __init__(self, datasource, alist):
        QtCore.QThread.__init__(self)
        self.data_source = datasource
        self.__list = alist
        self.__isConnected = False
        self.__loop = True

    def run(self):
        while self.__loop:
            if time:
                time.sleep(GLOBALREFRESHRATE)
            if self.__isConnected:
                try:
                    img, name = self.data_source.getData()
                except Exception as e:
                    name = "__ERROR__"
                    img = str(e)
                if name is not None:
                    self.__list.addData(name, img)
                    self.newDataName.emit(name)
            else:
                pass

    @QtCore.pyqtSlot(int)
    def changeStatus(self, status):
        self.__isConnected = status

    def stop(self):
        self.__loop = False
        self.__isConnected = False
