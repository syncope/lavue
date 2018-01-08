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

""" levels widget """

from PyQt4 import QtCore, QtGui
from .histogramWidget import HistogramHLUTWidget, HistogramHLUTItem
import math


class LevelsWidget(QtGui.QGroupBox):

    """
    Set minimum and maximum displayed values.
    """

    changeMinLevel = QtCore.pyqtSignal(float)
    changeMaxLevel = QtCore.pyqtSignal(float)
    autoLevels = QtCore.pyqtSignal(int)  # bool does not work...
    levelsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtGui.QGroupBox.__init__(self, parent)

        self.setTitle("Set display levels")

        # keep internal var for auto levelling toggle
        self.auto = True
        self.histo = True
        self.scaling = ""

        self.autoLevelBox = QtGui.QCheckBox(u"Automatic levels")
        self.autoLevelBox.setChecked(True)
        self.autoLevelBox.setToolTip(
            "find mininum and maximum intensity values after scaling"
            " for color distribution of the image")

        # informLabel = QtGui.QLabel("Linear scale, affects only display!")
        self.minLabel = QtGui.QLabel("minimum value: ")
        self.minLabel.setToolTip("mininum intensity values after scaling")
        self.maxLabel = QtGui.QLabel("maximum value: ")
        self.maxLabel.setToolTip("maximum intensity values after scaling")

        self.scalingLabel = QtGui.QLabel("sqrt scale!")
        self.scalingLabel.setStyleSheet("color: red;")
        self.minVal = 0.1
        self.maxVal = 1.

        self.minValSB = QtGui.QDoubleSpinBox()
        self.minValSB.setToolTip("mininum intensity values after scaling")
        self.minValSB.setMinimum(-10e20)
        self.minValSB.setMaximum(10e20)
        self.maxValSB = QtGui.QDoubleSpinBox()
        self.maxValSB.setMinimum(-10e20)
        self.maxValSB.setMaximum(10e20)
        self.maxValSB.setToolTip("maximum intensity values after scaling")

        self.histogram = HistogramHLUTWidget()

        self.glayout = QtGui.QGridLayout()
        vlayout = QtGui.QVBoxLayout()
        self.glayout.addWidget(self.scalingLabel, 0, 0)
        self.glayout.addWidget(self.autoLevelBox, 0, 1)
        self.glayout.addWidget(self.minLabel, 1, 0)
        self.glayout.addWidget(self.minValSB, 1, 1)
        self.glayout.addWidget(self.maxLabel, 2, 0)
        self.glayout.addWidget(self.maxValSB, 2, 1)
        vlayout.addLayout(self.glayout)
        vlayout.addWidget(self.histogram)

        self.hideControls()
        self.setLayout(vlayout)
        self.autoLevelBox.stateChanged.connect(self.autoLevelChange)
        self.histogram.item.sigLevelsChanged.connect(self.levelChange)
        self.updateLevels(self.minVal, self.maxVal)
        self.connectVal()

    def connectVal(self):
        self.minValSB.valueChanged.connect(self.valChanged)
        self.maxValSB.valueChanged.connect(self.valChanged)

    def disconnectVal(self):
        self.minValSB.valueChanged.disconnect(self.valChanged)
        self.maxValSB.valueChanged.disconnect(self.valChanged)

    @QtCore.pyqtSlot(float)
    def valChanged(self, _):
        if not self.auto:
            try:
                self.disconnectVal()
                self.check_and_emit()
                if self.histo:
                    lowlim = self.minValSB.value()
                    uplim = self.maxValSB.value()
                    self.histogram.region.setRegion([lowlim, uplim])
            finally:
                self.connectVal()

    def changeview(self, showhistogram=False):
        if showhistogram:
            self.histo = True
            self.histogram.show()
            self.histogram.fillHistogram(True)
        else:
            self.histo = False
            self.histogram.hide()
            self.histogram.fillHistogram(False)

    def isAutoLevel(self):
        return self.auto

    @QtCore.pyqtSlot(int)
    def autoLevelChange(self, value):
        if value == 2:
            self.auto = True
            self.hideControls()
            self.autoLevels.emit(1)
        else:
            self.auto = False
            self.showControls()
            self.autoLevels.emit(0)
            self.check_and_emit()
        self.levelsChanged.emit()

    @QtCore.pyqtSlot(HistogramHLUTItem)
    def levelChange(self, histo):
        levels = histo.region.getRegion()
        lowlim = self.minValSB.value()
        uplim = self.maxValSB.value()
        if levels[0] != lowlim or levels[1] != uplim:
            self.minValSB.setValue(levels[0])
            self.maxValSB.setValue(levels[1])
            if not self.auto:
                self.check_and_emit()

    @QtCore.pyqtSlot()
    def check_and_emit(self):
        # check if the minimum value is actually smaller than the maximum
        self.minVal = self.minValSB.value()
        self.maxVal = self.maxValSB.value()
        if self.maxVal - self.minVal <= 0:
            if self.minVal >= 1.:
                self.minVal = self.maxVal - 1.
            else:
                self.maxVal = self.minVal + 1

        self.minValSB.setValue(self.minVal)
        self.maxValSB.setValue(self.maxVal)

        self.changeMinLevel.emit(self.minVal)
        self.changeMaxLevel.emit(self.maxVal)
        self.levelsChanged.emit()

    def updateLevels(self, lowlim, uplim):
        self.minValSB.setValue(lowlim)
        self.maxValSB.setValue(uplim)
        if self.histo and self.auto:
            levels = self.histogram.region.getRegion()
            if levels[0] != lowlim or levels[1] != uplim:
                self.histogram.region.setRegion([lowlim, uplim])

    def hideControls(self):
        self.minValSB.setEnabled(False)
        self.maxValSB.setEnabled(False)

    def showControls(self):
        self.minValSB.setEnabled(True)
        self.maxValSB.setEnabled(True)

    @QtCore.pyqtSlot(str)
    def setScalingLabel(self, scalingType):
        lowlim = float(self.minValSB.value())
        uplim = float(self.maxValSB.value())
        if scalingType == "log":
            if scalingType != self.scaling:
                self.scalingLabel.setText("log scale!")
                if not self.auto:
                    if self.scaling == "linear":
                        lowlim = math.log10(
                            lowlim or 10e-3) if lowlim > 0 else -2
                        uplim = math.log10(
                            uplim or 10e-3) if uplim > 0 else -2
                    elif self.scaling == "sqrt":
                        lowlim = math.log10(
                            lowlim * lowlim or 10e-3) if lowlim > 0 else -2
                        uplim = math.log10(
                            uplim * uplim or 10e-3) if uplim > 0 else -2
        elif scalingType == "linear":
            if scalingType != self.scaling:
                self.scalingLabel.setText("linear scale!")
                if not self.auto:
                    if self.scaling == "log":
                        lowlim = math.pow(10, lowlim)
                        uplim = math.pow(10, uplim)
                    elif self.scaling == "sqrt":
                        lowlim = lowlim * lowlim
                        uplim = uplim * uplim
        elif scalingType == "sqrt":
            if scalingType != self.scaling:
                self.scalingLabel.setText("sqrt scale!")
                if not self.auto:
                    if self.scaling == "linear":
                        lowlim = math.sqrt(max(lowlim, 0))
                        uplim = math.sqrt(max(uplim, 0))
                    elif self.scaling == "log":
                        lowlim = math.sqrt(max(math.pow(10, lowlim), 0))
                        uplim = math.sqrt(max(math.pow(10, uplim), 0))
        if scalingType != self.scaling:
            self.scaling = scalingType
        if not self.auto:
            if self.histo:
                self.histogram.region.setRegion([lowlim, uplim])
            else:
                self.minValSB.setValue(lowlim)
                self.maxValSB.setValue(uplim)
