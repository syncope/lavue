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
import json


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
        self.aspectlocked = False
        self.statswoscaling = False

        self.doorLineEdit = None
        self.addroisCheckBox = None
        self.secportLineEdit = None
        self.secstreamCheckBox = None
        self.secautoportCheckBox = None
        self.rateDoubleSpinBox = None
        self.showhistoCheckBox = None
        self.showmaskCheckBox = None
        self.timeoutLineEdit = None
        self.aspectlockedCheckBox = None
        self.buttonBox = None
        self.zmqtopics = []
        self.dirtrans = '{"/ramdisk/": "/gpfs/"}'

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

        aspectlockedLabel = QtGui.QLabel(u"Aspect Ratio locked:")
        aspectlockedLabel.setToolTip(
            "lock the aspect ration of the image")
        self.aspectlockedCheckBox = QtGui.QCheckBox()
        self.aspectlockedCheckBox.setChecked(self.aspectlocked)
        self.aspectlockedCheckBox.setToolTip(
            "lock the aspect ration of the image")

        statsscaleLabel = QtGui.QLabel(u"Statistics with scaling:")
        statsscaleLabel.setToolTip(
            "statistics values with scaling")
        self.statsscaleCheckBox = QtGui.QCheckBox()
        self.statsscaleCheckBox.setChecked(not self.statswoscaling)
        self.statsscaleCheckBox.setToolTip(
            "statistics values with scaling")

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

        zmqtopicsLabel = QtGui.QLabel(u"ZMQ Source topics:")
        zmqtopicsLabel.setToolTip(
            "ZMQ Source topics separated by spaces")
        self.zmqtopicsLineEdit = QtGui.QLineEdit(" ".join(self.zmqtopics))
        self.zmqtopicsLineEdit.setToolTip(
            "ZMQ Source topics separated by spaces")

        dirtransLabel = QtGui.QLabel(u"ZMQ Source topics:")
        dirtransLabel.setToolTip(
            "ZMQ Source topics separated by spaces")
        self.dirtransLineEdit = QtGui.QLineEdit(self.dirtrans)
        self.dirtransLineEdit.setToolTip(
            "ZMQ Source topics separated by spaces")

        gridlayout.addWidget(rateLabel, 0, 0)
        gridlayout.addWidget(self.rateDoubleSpinBox, 0, 1)
        gridlayout.addWidget(aspectlockedLabel, 1, 0)
        gridlayout.addWidget(self.aspectlockedCheckBox, 1, 1)
        gridlayout.addWidget(doorLabel, 2, 0)
        gridlayout.addWidget(self.doorLineEdit, 2, 1)
        gridlayout.addWidget(addroisLabel, 3, 0)
        gridlayout.addWidget(self.addroisCheckBox, 3, 1)
        gridlayout.addWidget(secstreamLabel, 4, 0)
        gridlayout.addWidget(self.secstreamCheckBox, 4, 1)
        gridlayout.addWidget(secautoportLabel, 5, 0)
        gridlayout.addWidget(self.secautoportCheckBox, 5, 1)
        gridlayout.addWidget(secportLabel, 6, 0)
        gridlayout.addWidget(self.secportLineEdit, 6, 1)
        gridlayout.addWidget(showhistoLabel, 7, 0)
        gridlayout.addWidget(self.showhistoCheckBox, 7, 1)
        gridlayout.addWidget(showmaskLabel, 8, 0)
        gridlayout.addWidget(self.showmaskCheckBox, 8, 1)
        gridlayout.addWidget(timeoutLabel, 9, 0)
        gridlayout.addWidget(self.timeoutLineEdit, 9, 1)
        gridlayout.addWidget(statsscaleLabel, 10, 0)
        gridlayout.addWidget(self.statsscaleCheckBox, 10, 1)
        gridlayout.addWidget(zmqtopicsLabel, 11, 0)
        gridlayout.addWidget(self.zmqtopicsLineEdit, 11, 1)
        gridlayout.addWidget(dirtransLabel, 11, 0)
        gridlayout.addWidget(self.dirtransLineEdit, 11, 1)
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
        self.aspectlocked = self.aspectlockedCheckBox.isChecked()
        self.statswoscaling = not self.statsscaleCheckBox.isChecked()
        zmqtopics = str(self.zmqtopicsLineEdit.text()).strip().split(" ")
        try:
            dirtrans = str(self.dirtransLineEdit.text()).strip()
            mytr = json.loads(dirtrans)
            if isinstance(mytr, dict):
                self.dirtrans = dirtrans
        except Exception as e:
            print(str(e))
        self.zmqtopics = [tp for tp in zmqtopics if tp]
        try:
            self.timeout = int(self.timeoutLineEdit.text())
        except:
            pass
        QtGui.QDialog.accept(self)
