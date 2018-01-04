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

""" configuration widget """

from PyQt4 import QtGui, QtCore


class ConfigWidget(QtGui.QDialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.door = ""
        self.addrois = True
        self.secstream = False
        self.secport = "5657"
        self.secautoport = True
        self.refreshrate = 0.1
        self.showhisto = True
        self.showmask = False
        self.timeout = 3000

        self.doorLineEdit = None
        self.addroisCheckBox = None
        self.secportLineEdit = None
        self.secstreamCheckBox = None
        self.secautoportCheckBox = None
        self.rateDoubleSpinBox = None
        self.showhistoCheckBox = None
        self.showmaskCheckBox = None
        self.buttonBox = None

    def createGUI(self):

        self.setWindowTitle("Configuration")

        gridlayout = QtGui.QGridLayout()
        vlayout = QtGui.QVBoxLayout()

        rateLabel = QtGui.QLabel(u"Refresh rate:")
        rateLabel.setToolTip(
            "refresh rate of the image in seconds")
        self.rateDoubleSpinBox = QtGui.QDoubleSpinBox()
        self.rateDoubleSpinBox.setValue(self.refreshrate)
        self.rateDoubleSpinBox.setSingleStep(0.01)
        self.rateDoubleSpinBox.setToolTip(
            "refresh rate of the image in seconds")
        doorLabel = QtGui.QLabel(u"Sardana Door:")
        doorLabel.setToolTip(
            "tango server device name of the Sarana Door")
        self.doorLineEdit = QtGui.QLineEdit(self.door)
        self.doorLineEdit.setToolTip(
            "tango server device name of the Sarana Door")
        addroisLabel = QtGui.QLabel(u"Add ROIs to Active MG:")
        addroisLabel.setToolTip(
            "add ROI aliases to the Active Measurement Group")
        self.addroisCheckBox = QtGui.QCheckBox()
        self.addroisCheckBox.setChecked(self.addrois)
        self.addroisCheckBox.setToolTip(
            "add ROI aliases to the Active Measurement Group")
        secstreamLabel = QtGui.QLabel(u"ZMQ secure stream:")
        secstreamLabel.setToolTip(
            "send the zmq security stream with the main image parameters")
        self.secstreamCheckBox = QtGui.QCheckBox()
        self.secstreamCheckBox.setChecked(self.secstream)
        self.secstreamCheckBox.setToolTip(
            "send the zmq security stream with the main image parameters")
        secautoportLabel = QtGui.QLabel(u"ZMQ secure automatic port:")
        secautoportLabel.setToolTip(
            "select port automatically for the zmq security stream")
        self.secautoportCheckBox = QtGui.QCheckBox()
        self.secautoportCheckBox.setToolTip(
            "select port automatically for the zmq security stream")
        self.secautoportCheckBox.setChecked(self.secautoport)
        secportLabel = QtGui.QLabel(u"ZMQ secure port:")
        secportLabel.setToolTip(
            "port for the zmq security stream")
        self.secportLineEdit = QtGui.QLineEdit(self.secport)
        self.secportLineEdit.setToolTip(
            "port for the zmq security stream")
        self.autoportChanged(self.secautoport)
        self.secautoportCheckBox.stateChanged.connect(self.autoportChanged)
        showhistoLabel = QtGui.QLabel(u"Show histogram:")
        showhistoLabel.setToolTip(
            "show histogram to set range and color distribution")
        self.showhistoCheckBox = QtGui.QCheckBox()
        self.showhistoCheckBox.setToolTip(
            "show histogram to set range and color distribution")
        self.showhistoCheckBox.setChecked(self.showhisto)
        showmaskLabel = QtGui.QLabel(u"Show mask widget:")
        showmaskLabel.setToolTip(
            "show widgets to select the image mask")
        self.showmaskCheckBox = QtGui.QCheckBox()
        self.showmaskCheckBox.setToolTip(
            "show widgets to select the image mask")
        self.showmaskCheckBox.setChecked(self.showmask)

        timeoutLabel = QtGui.QLabel(u"Source timeout in ms:")
        timeoutLabel.setToolTip(
            "Source timeout in ms")
        self.timeoutLineEdit = QtGui.QLineEdit(str(self.timeout))
        self.timeoutLineEdit.setToolTip(
            "Source timeout in ms")

        gridlayout.addWidget(rateLabel, 0, 0)
        gridlayout.addWidget(self.rateDoubleSpinBox, 0, 1)
        gridlayout.addWidget(doorLabel, 1, 0)
        gridlayout.addWidget(self.doorLineEdit, 1, 1)
        gridlayout.addWidget(addroisLabel, 2, 0)
        gridlayout.addWidget(self.addroisCheckBox, 2, 1)
        gridlayout.addWidget(secstreamLabel, 3, 0)
        gridlayout.addWidget(self.secstreamCheckBox, 3, 1)
        gridlayout.addWidget(secautoportLabel, 4, 0)
        gridlayout.addWidget(self.secautoportCheckBox, 4, 1)
        gridlayout.addWidget(secportLabel, 5, 0)
        gridlayout.addWidget(self.secportLineEdit, 5, 1)
        gridlayout.addWidget(showhistoLabel, 6, 0)
        gridlayout.addWidget(self.showhistoCheckBox, 6, 1)
        gridlayout.addWidget(showmaskLabel, 7, 0)
        gridlayout.addWidget(self.showmaskCheckBox, 7, 1)
        gridlayout.addWidget(timeoutLabel, 8, 0)
        gridlayout.addWidget(self.timeoutLineEdit, 8, 1)
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

    @QtCore.pyqtSlot(int)
    def autoportChanged(self, value):
        if value:
            self.secportLineEdit.setEnabled(False)
        else:
            self.secportLineEdit.setEnabled(True)

    @QtCore.pyqtSlot()
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
        self.showmask = self.showmaskCheckBox.isChecked()
        try:
            self.timeout = int(self.timeoutLineEdit.text())
        except:
            pass
        QtGui.QDialog.accept(self)
