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

""" detector range widget """

from PyQt4 import QtGui, QtCore, uic
import os

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "RangeDialog.ui"))


class RangeDialog(QtGui.QDialog):

    """ detector range widget class"""

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        QtGui.QDialog.__init__(self, parent)

        #: (:class:`Ui_Dialog') ui_dialog object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`float`) start position of radial coordinate
        self.radstart = None
        #: (:obj:`float`) end position of radial coordinate
        self.radend = None
        #: (:obj:`int`) grid size of radial coordinate
        self.radsize = None
        #: (:obj:`float`) start position of polar angle
        self.polstart = None
        #: (:obj:`float`) end position of polar angle
        self.polend = None
        #: (:obj:`int`) grid size of polar angle
        self.polsize = None

    def createGUI(self):
        """ create GUI
        """
        self.__ui.polstartLineEdit.setText(
            str(self.polstart if self.polstart is not None else ""))
        self.__ui.polendLineEdit.setText(
            str(self.polend if self.polend is not None else ""))
        self.__ui.polsizeLineEdit.setText(
            str(self.polsize if self.polsize is not None else ""))
        self.__ui.radstartLineEdit.setText(
            str(self.radstart if self.radstart is not None else ""))
        self.__ui.radendLineEdit.setText(
            str(self.radend if self.radend is not None else ""))
        self.__ui.radsizeLineEdit.setText(
            str(self.radsize if self.radsize is not None else ""))

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        try:
            self.polstart = float(self.__ui.polstartLineEdit.text())
        except:
            self.polstart = None
        try:
            self.polend = float(self.__ui.polendLineEdit.text())
        except:
            self.polend = None
        try:
            self.polsize = int(self.__ui.polsizeLineEdit.text())
        except:
            self.polsize = None

        try:
            self.radstart = float(self.__ui.radstartLineEdit.text())
        except:
            self.radstart = None
        try:
            self.radend = float(self.__ui.radendLineEdit.text())
        except:
            self.radend = None
        try:
            self.radsize = int(self.__ui.radsizeLineEdit.text())
        except:
            self.radsize = None


        QtGui.QDialog.accept(self)
