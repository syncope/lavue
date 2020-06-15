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

""" detector range widget """

from .qtuic import uic
from pyqtgraph import QtCore, QtGui
import os

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "DiffRangeDialog.ui"))


class DiffRangeDialog(QtGui.QDialog):

    """ diffractogram range widget class"""

    def __init__(self, parent=None):
        """ constructort

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtGui.QDialog.__init__(self, parent)

        #: (:class:`Ui_Dialog') ui_dialog object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`float`) start position of radial coordinate
        self.radstart = None
        #: (:obj:`float`) end position of radial coordinate
        self.radend = None
        #: (:obj:`float`) start position of azimuth angle
        self.azstart = None
        #: (:obj:`float`) end position of azimuth angle
        self.azend = None
        #: (:obj:`int`) radial angle index
        self.radunitindex = 2
        #: (:obj:`list` <:obj:`unicode`>) list of units
        self.radunits = [u"1/nm", u"1/\u212B", u"deg", u"rad", u"mm"]

    def createGUI(self):
        """ create GUI
        """
        self.__ui.azstartLineEdit.setText(
            str(self.azstart if self.azstart is not None else ""))
        self.__ui.azendLineEdit.setText(
            str(self.azend if self.azend is not None else ""))
        self.__ui.radstartLineEdit.setText(
            str(self.radstart if self.radstart is not None else ""))
        self.__ui.radendLineEdit.setText(
            str(self.radend if self.radend is not None else ""))
        self.__ui.radendLabel.setText("End [%s]:" %
                                      self.radunits[self.radunitindex])
        self.__ui.radstartLabel.setText("Start [%s]:" %
                                        self.radunits[self.radunitindex])

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        try:
            self.azstart = float(self.__ui.azstartLineEdit.text())
        except Exception:
            self.azstart = None
        try:
            self.azend = float(self.__ui.azendLineEdit.text())
        except Exception:
            self.azend = None
        try:
            self.radstart = float(self.__ui.radstartLineEdit.text())
        except Exception:
            self.radstart = None
        try:
            self.radend = float(self.__ui.radendLineEdit.text())
        except Exception:
            self.radend = None

        QtGui.QDialog.accept(self)
