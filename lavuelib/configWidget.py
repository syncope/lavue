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
        self.secstream = False
        self.secport = "5657"
        self.secautoport = True
        self.refreshrate = 0.1
        self.showhisto = True

    def createGUI(self):

        self.setWindowTitle("Configuration")

        gridlayout = QtGui.QGridLayout()
        vlayout = QtGui.QVBoxLayout()

        self.rateLabel = QtGui.QLabel(u"Refresh rate:")
        self.rateDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.rateDoubleSpinBox.setValue(self.refreshrate)
        self.rateDoubleSpinBox.setSingleStep(0.01)
        self.doorLabel = QtGui.QLabel(u"Sardana Door:")
        self.doorLineEdit = QtGui.QLineEdit(self.door)
        self.addroisLabel = QtGui.QLabel(u"Add ROIs to Active MG:")
        self.addroisCheckBox = QtGui.QCheckBox()
        self.addroisCheckBox.setChecked(self.addrois)
        self.secstreamLabel = QtGui.QLabel(u"ZMQ secure stream:")
        self.secstreamCheckBox = QtGui.QCheckBox()
        self.secstreamCheckBox.setChecked(self.secstream)
        self.secautoportLabel = QtGui.QLabel(u"ZMQ secure automatic port:")
        self.secautoportCheckBox = QtGui.QCheckBox()
        self.secautoportCheckBox.setChecked(self.secautoport)
        self.secportLabel = QtGui.QLabel(u"ZMQ secure port:")
        self.secportLineEdit = QtGui.QLineEdit(self.secport)
        self.autoportChanged(self.secautoport)
        self.secautoportCheckBox.stateChanged.connect(self.autoportChanged)
        self.showhistoLabel = QtGui.QLabel(u"Show histogram:")
        self.showhistoCheckBox = QtGui.QCheckBox()
        self.showhistoCheckBox.setChecked(self.showhisto)

        gridlayout.addWidget(self.rateLabel, 0, 0)
        gridlayout.addWidget(self.rateDoubleSpinBox, 0, 1)
        gridlayout.addWidget(self.doorLabel, 1, 0)
        gridlayout.addWidget(self.doorLineEdit, 1, 1)
        gridlayout.addWidget(self.addroisLabel, 2, 0)
        gridlayout.addWidget(self.addroisCheckBox, 2, 1)
        gridlayout.addWidget(self.secstreamLabel, 3, 0)
        gridlayout.addWidget(self.secstreamCheckBox, 3, 1)
        gridlayout.addWidget(self.secautoportLabel, 4, 0)
        gridlayout.addWidget(self.secautoportCheckBox, 4, 1)
        gridlayout.addWidget(self.secportLabel, 5, 0)
        gridlayout.addWidget(self.secportLineEdit, 5, 1)
        gridlayout.addWidget(self.showhistoLabel, 6, 0)
        gridlayout.addWidget(self.showhistoCheckBox, 6, 1)
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

    def autoportChanged(self, value):
        if value:
            self.secportLineEdit.setEnabled(False)
        else:
            self.secportLineEdit.setEnabled(True)

    def accept(self):
        """ updates class variables with the form content
        """

        self.door = str(self.doorLineEdit.text()).strip()
        self.addrois = self.addroisCheckBox.isChecked()
        self.secport = str(self.secportLineEdit.text()).strip()
        self.secstream = self.secstreamCheckBox.isChecked()
        self.secautoport = self.secautoportCheckBox.isChecked()
        self.refreshrate = float(self.rateDoubleSpinBox.value())
        self.showhisto = self.showhistoCheckBox.isChecked()
        QtGui.QDialog.accept(self)
