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

from PyQt4 import QtGui, QtCore, uic
import os
import json


class ConfigWidget(QtGui.QDialog):

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        QtGui.QDialog.__init__(self, parent)
        self.__ui = uic.loadUi(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "ui", "ConfigWidget.ui"), self)

        self.door = ""
        self.sardana = True
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

        self.zmqtopics = []
        self.autozmqtopics = False

        self.dirtrans = '{"/ramdisk/": "/gpfs/"}'

    def createGUI(self):

        self.__ui.rateDoubleSpinBox.setValue(self.refreshrate)
        self.__ui.aspectlockedCheckBox.setChecked(self.aspectlocked)
        self.__ui.statsscaleCheckBox.setChecked(not self.statswoscaling)
        self.__ui.sardanaCheckBox.setChecked(self.sardana)
        self.__ui.doorLineEdit.setText(self.door)
        self.__ui.addroisCheckBox.setChecked(self.addrois)
        self.__ui.secstreamCheckBox.setChecked(self.secstream)
        self.__ui.secautoportCheckBox.setChecked(self.secautoport)
        self.__ui.secportLineEdit.setText(self.secport)
        self.autoportChanged(self.secautoport)
        self.__ui.secautoportCheckBox.stateChanged.connect(self.autoportChanged)

        self.__ui.showhistoCheckBox.setChecked(self.showhisto)
        self.__ui.showmaskCheckBox.setChecked(self.showmask)

        self.__ui.timeoutLineEdit.setText(str(self.timeout))
        self.__ui.zmqtopicsLineEdit.setText(" ".join(self.zmqtopics))
        self.__ui.autozmqtopicsCheckBox.setChecked(self.autozmqtopics)

        self.__ui.dirtransLineEdit.setText(self.dirtrans)
        
        self.buttonBox.button(
            QtGui.QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.buttonBox.button(
            QtGui.QDialogButtonBox.Ok).clicked.connect(self.accept)

    @QtCore.pyqtSlot(int)
    def autoportChanged(self, value):
        if value:
            self.__ui.secportLineEdit.setEnabled(False)
        else:
            self.__ui.secportLineEdit.setEnabled(True)

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """

        self.sardana = self.__ui.sardanaCheckBox.isChecked()
        self.door = str(self.__ui.doorLineEdit.text()).strip()
        self.addrois = self.__ui.addroisCheckBox.isChecked()
        self.secport = str(self.__ui.secportLineEdit.text()).strip()
        self.secstream = self.__ui.secstreamCheckBox.isChecked()
        self.secautoport = self.__ui.secautoportCheckBox.isChecked()
        self.refreshrate = float(self.__ui.rateDoubleSpinBox.value())
        self.showhisto = self.__ui.showhistoCheckBox.isChecked()
        self.showmask = self.__ui.showmaskCheckBox.isChecked()
        self.aspectlocked = self.__ui.aspectlockedCheckBox.isChecked()
        self.statswoscaling = not self.__ui.statsscaleCheckBox.isChecked()
        zmqtopics = str(self.__ui.zmqtopicsLineEdit.text()).strip().split(" ")
        try:
            dirtrans = str(self.__ui.dirtransLineEdit.text()).strip()
            mytr = json.loads(dirtrans)
            if isinstance(mytr, dict):
                self.dirtrans = dirtrans
        except Exception as e:
            print(str(e))
        self.zmqtopics = [tp for tp in zmqtopics if tp]
        self.autozmqtopics = self.__ui.autozmqtopicsCheckBox.isChecked()
        try:
            self.timeout = int(self.__ui.timeoutLineEdit.text())
        except:
            pass
        QtGui.QDialog.accept(self)
