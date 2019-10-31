# Copyright (C) 2017  DESY, Notkestr. 85, D-22607 Hamburg
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
#     Jan Kotanski <jan.kotanski@desy.de>
#

""" Memory Buffer widget """

import numpy as np
import sys
from .qtuic import uic
from pyqtgraph import QtCore, QtGui
import os


if sys.version_info > (3,):
    unicode = str
else:
    bytes = str

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "MemoryBufferGroupBox.ui"))


class MemoryBufferGroupBox(QtGui.QGroupBox):

    """
    Set circular memory buffer for images
    """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtGui.QGroupBox.__init__(self, parent)

        #: (:class:`Ui_MemoryBufferGroupBox')
        #      ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`int`) number of frames in memory buffer
        self.__maxindex = 10
        #: (:obj:`bool`) is on status
        self.__isOn = False
        #: (:obj:`bool`) is buffer full
        self.__full = False

        #: (:class:`numpy.ndarray`) image stack
        self.__imagestack = None
        #: (:obj:`int`) the current size
        self.__current = 1
        #: (:class:`numpy.ndarray`) the last imaste
        self.__lastimage = None
        #: (:obj:`bool`)
        self.__first = True
        try:
            self.__fullicon = QtGui.QIcon.fromTheme("starred")
        except Exception:
            self.__fullicon = QtGui.QIcon(":/star2.png")
        
        self.__ui.statusPushButton.setIcon(self.__fullicon)
        self.__ui.sizeSpinBox.setEnabled(False)
        self.__ui.resetPushButton.setEnabled(False)
        self.__ui.sizeSpinBox.valueChanged.connect(self._onBufferSizeChanged)
        self.__ui.onoffCheckBox.stateChanged.connect(self._onOff)
        self.__ui.resetPushButton.clicked.connect(self._onBufferSizeChanged)

    @QtCore.pyqtSlot(int)
    @QtCore.pyqtSlot()
    def _onBufferSizeChanged(self, size=None):
        """ set size of image buffer in frame numbers

        :param size: buffer size
        :type size: :obj:`int`
        """
        if size is not None:
            self.__maxindex = size
        self.initialize()

    @QtCore.pyqtSlot(int)
    def _onOff(self, status):
        """
        """
        self.__isOn = True if status else False
        self.initialize()
        self.__ui.sizeSpinBox.setEnabled(status)
        self.__ui.resetPushButton.setEnabled(status)
        self.__ui.statusPushButton.setEnabled(False)

    def initialize(self):
        """ initialize the filter
        """
        self.__imagestack = None
        self.__lastimage = None
        self.__current = 1
        self.__first = True
        self.__full = False
        self.__ui.statusPushButton.setEnabled(self.__full)
        
    def process(self, image, imagename):
        """ append image to the buffer and returns image buffer and metadata

        :param image: numpy array with an image
        :type image: :class:`numpy.ndarray`
        :param imagename: image name
        :type imagename: :obj:`str`
        :returns: numpy array with an image
        :rtype: (:class:`numpy.ndarray`, :obj`dict`<:obj:`str`, :obj:`str`>)
                 or `None`
        """
        if self.__isOn:
            mdata = {}
            if self.__lastimage is None or \
               not np.array_equal(self.__lastimage, image):
                shape = image.shape
                dtype = image.dtype

                if self.__imagestack is not None:
                    if self.__imagestack.shape[1:] != shape or \
                       self.__imagestack.dtype != dtype:
                        self.__imagestack = None

                if self.__imagestack is None:
                    newshape = np.concatenate(
                        ([self.__maxindex + 1], list(shape)))
                    self.__imagestack = np.zeros(dtype=dtype, shape=newshape)

                if self.__current > self.__maxindex:
                    self.__current = 1
                if self.__current >= self.__maxindex:
                    self.__full = True
                    self.__ui.statusPushButton.setEnabled(self.__full)
                lshape = len(self.__imagestack.shape)
                if lshape == 3:
                    self.__imagestack[self.__current, :, :] = image
                    self.__imagestack[0, :, :] = image
                elif lshape == 2:
                    self.__imagestack[self.__current, :] = image
                    self.__imagestack[0, :] = image
                elif lshape == 1:
                    self.__imagestack[self.__current] = image
                    self.__imagestack[0] = image

                self.__current += 1
                self.__lastimage = image

                if self.__first:
                    cblbl = {key: None for key in range(self.__maxindex)}
                else:
                    cblbl = {}
                mdata["channellabels"] = cblbl
                mdata["skipfirst"] = True
                cblbl[0] = "0: the last image"
                cblbl[self.__current - 1] = "%s: %s" % (
                    self.__current - 1, imagename)
                self.__first = False

            if self.__imagestack is not None:
                return (self.__imagestack, mdata)

    def changeView(self, show=False):
        """ shows or hides the histogram widget

        :param show: if histogram should be shown
        :type show: :obj:`bool`
        """
        if show:
            self.show()
        else:
            self.hide()
