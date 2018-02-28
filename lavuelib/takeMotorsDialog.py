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
#     Christoph Rosemann <christoph.rosemann@desy.de>
#

""" motor device widget """

from PyQt4 import QtGui, QtCore, uic
import os

try:
    import PyTango
    #: (:obj:`bool`) PyTango imported
    PYTANGO = True
except ImportError:
    #: (:obj:`bool`) PyTango imported
    PYTANGO = False


_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "TakeMotorsDialog.ui"))


class TakeMotorsDialog(QtGui.QDialog):

    """ detector geometry widget class"""

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        QtGui.QDialog.__init__(self, parent)

        #: (:class:`Ui_Dialog') ui_dialog object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`str`) horizontal motor name
        self.hmotorname = ""
        #: (:obj:`str`) vertical motor name
        self.vmotorname = ""
        #: (:class:`PyTango.DeviceProxy`) horizontal motor device
        self.hmotordevice = None
        #: (:class:`PyTango.DeviceProxy`) vertical motor device
        self.vmotordevice = None
        
    def createGUI(self):
        """ create GUI
        """
        self.__ui.horizontalLineEdit.setText(str(self.hmotorname))
        self.__ui.verticalLineEdit.setText(str(self.vmotorname))

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        try:
            self.hmotorname = str(self.__ui.horizontalLineEdit.text())
            self.hmotordevice = PyTango.DeviceProxy(self.hmotorname)
        except:
            self.__ui.horizontalLineEdit.setFocus()
            return
        try:
            self.vmotorname = str(self.__ui.verticalLineEdit.text())
            self.vmotordevice = PyTango.DeviceProxy(self.vmotorname)
        except:
            self.__ui.verticalLineEdit.setFocus()
            return


        QtGui.QDialog.accept(self)
