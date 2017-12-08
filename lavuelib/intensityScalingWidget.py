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

""" intensityScalingWidget """

from PyQt4 import QtCore, QtGui


class IntensityScalingWidget(QtGui.QGroupBox):

    """
    Select how the image intensity is supposed to be scaled.
    """
    changedScaling = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        QtGui.QGroupBox.__init__(self, parent)

        self.setTitle("Intensity display scaling")
        self.current = "sqrt"
        horizontallayout = QtGui.QHBoxLayout()

        self.sqrtbutton = QtGui.QRadioButton(u"sqrt")
        self.sqrtbutton.setToolTip("aply sqrt function on pixel intensity")
        self.linbutton = QtGui.QRadioButton(u"linear")
        self.linbutton.setToolTip("do not apply function on pixel intensity")
        self.logbutton = QtGui.QRadioButton(u"log")
        self.logbutton.setToolTip("aply log10 function on pixel intensity")

        self.linbutton.clicked.connect(self.setCurrentScaling)
        self.logbutton.clicked.connect(self.setCurrentScaling)
        self.sqrtbutton.clicked.connect(self.setCurrentScaling)
        self.sqrtbutton.setChecked(True)

        horizontallayout.addWidget(self.sqrtbutton)
        horizontallayout.addWidget(self.linbutton)
        horizontallayout.addWidget(self.logbutton)

        self.setLayout(horizontallayout)

    def getCurrentScaling(self):
        return self.current

    @QtCore.pyqtSlot()
    def setCurrentScaling(self):
        if self.linbutton.isChecked():
            self.current = "lin"
        elif self.logbutton.isChecked():
            self.current = "log"
        else:
            self.current = "sqrt"
        self.changedScaling.emit(self.current)
