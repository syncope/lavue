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


#: (:obj:`float`) refresh rate if the data source is running in seconds
GLOBALREFRESHRATE = .1  


class ExchangeList(object):

    """  subclass for data caching """
    
    def __init__(self):
        """ constructor
        """
        #: (:obj:`list` <:obj:`str`, :class:`numpy.ndarray`, :obj:`str` >)
        #:      exchange object
        self.__elist = [None, None, None]
        #: (:obj:`PyQt4.QtCore.QMutex`) mutex lock
        self.__mutex = QtCore.QMutex()

    def addData(self, name, data, metadata=""):
        """ write data into exchange object

        :param name: image name
        :type name: :obj:`str` 
        :param data: image data
        :type data: :class:`numpy.ndarray`
        :param metadata: json dictionary with image metadata
        :type metadata: :obj:`str` 
        """
        with QtCore.QMutexLocker(self.__mutex):
            self.__elist[0] = name
            self.__elist[1] = data
            self.__elist[2] = metadata

    def readData(self):
        """ write data into exchange object

        :returns: tuple of exchange object (name, data, metadata)
        :rtype: :obj:`list` <:obj:`str`, :class:`numpy.ndarray`, :obj:`str` >
        """
        with QtCore.QMutexLocker(self.__mutex):
            a, b, c = self.__elist[0], self.__elist[1], self.__elist[2]
        return a, b, c


# subclass for threading
class DataFetchThread(QtCore.QThread):

    
    #: (:class:`PyQt4.QtCore.pyqtSignal`) new data name signal
    newDataName = QtCore.pyqtSignal(str, str)

    def __init__(self, datasource, alist):
        """ constructor
        
        :param datasource: image datasource
        :type datasource: :class:`lavuelib.imageSource.GeneralSource`
        :param alist: exchange object
        :type alist: :class:`ExchangeList`
        """
        QtCore.QThread.__init__(self)
        self.data_source = datasource
        self.__list = alist
        self.__isConnected = False
        self.__loop = True

    def run(self):
        """ runner of the fetching thread
        """
        while self.__loop:
            if time:
                time.sleep(GLOBALREFRESHRATE)
            if self.__isConnected:
                try:
                    img, name, metadata = self.data_source.getData()
                except Exception as e:
                    name = "__ERROR__"
                    img = str(e)
                    metadata = ""
                if name is not None:
                    self.__list.addData(name, img, metadata)
                    self.newDataName.emit(name, metadata)
            else:
                pass

    @QtCore.pyqtSlot(int)
    def changeStatus(self, status):
        """ change connection status

        :param status: connection status
        :type status: :obj:`bool`
        """
        self.__isConnected = status

    def stop(self):
        """ stop the thread
        """
        self.__loop = False
        self.__isConnected = False
