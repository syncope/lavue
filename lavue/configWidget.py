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

from PyQt4 import QtGui


class ConfigWidget(QtGui.QDialog):

    def __init__(self, parent=None):
        super(ConfigWidget, self).__init__(parent)

        self.door = ""
        self.addrois = True

    def createGUI(self):

        self.setWindowTitle("Configuration")

        gridlayout = QtGui.QGridLayout()
        vlayout = QtGui.QVBoxLayout()

        self.doorLabel = QtGui.QLabel(u"Sardana Door:")
        self.doorLineEdit = QtGui.QLineEdit(self.door)
        self.addroisLabel = QtGui.QLabel(u"Add ROIs to Active MG:")
        self.addroisCheckBox = QtGui.QCheckBox()
        self.addroisCheckBox.setChecked(self.addrois)
        gridlayout.addWidget(self.doorLabel, 0, 0)
        gridlayout.addWidget(self.doorLineEdit, 0, 1)
        gridlayout.addWidget(self.addroisLabel, 1, 0)
        gridlayout.addWidget(self.addroisCheckBox, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok
            | QtGui.QDialogButtonBox.Cancel)
        vlayout.addLayout(gridlayout)
        vlayout.addWidget(self.buttonBox)
        self.setLayout(vlayout)
        self.buttonBox.button(
            QtGui.QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.buttonBox.button(
            QtGui.QDialogButtonBox.Ok).clicked.connect(self.accept)

    def accept(self):
        """ updates class variables with the form content
        """

        self.door = str(self.doorLineEdit.text()).strip()
        self.addrois = self.addroisCheckBox.isChecked()
        QtGui.QDialog.accept(self)
