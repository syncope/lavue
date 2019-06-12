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

""" filter widget """


from .qtuic import uic
from pyqtgraph import QtCore, QtGui
import os

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "FiltersWidget.ui"))


class FiltersWidget(QtGui.QWidget):
    """
    Select how an image should be transformed.
    """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) filter changed signal
    filtersChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtGui.QWidget.__init__(self, parent)

        #: (:class:`Ui_FiltersWidget') ui_widget object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        self.__ui.checkBox.stateChanged.connect(
            self._onFilterChanged)

    @QtCore.pyqtSlot(int)
    def _onFilterChanged(self, state):
        """ emits filter changed

        :param state: filter state
        :type state: :obj:`int`
        """
        self.filtersChanged.emit(state)
