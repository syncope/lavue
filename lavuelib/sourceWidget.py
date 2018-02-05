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

""" image source selection """

from PyQt4 import QtCore, QtGui, uic
import os

_testformclass, _testbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "TestSourceWidget.ui"))


class GeneralSourceWidget(QtGui.QWidget):

    """ test source widget """
    
    #: (:class:`PyQt4.QtCore.pyqtSignal`) push button enabled signal
    buttonEnabledSignal = QtCore.pyqtSignal(bool)
    
    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        QtGui.QGroupBox.__init__(self, parent)
        
        self.__ui = _testformclass()
        self.__ui.setupUi(self)

        self.name = "Test"
        self.datasource = "GeneralSource"
        self.widgets = []
        self.active = False

        
    def updateButton(self):
        """ update slot for test source
        """
        if not self.active:
            return
        self.buttonEnabledSignal.emit(True)


    def updateMetaData(self, **kargs):
        """ update source input parameters
        """
