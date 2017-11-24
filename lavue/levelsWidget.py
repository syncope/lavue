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


from PyQt4 import QtCore, QtGui
from .histogramWidget import HistogramHLUTWidget
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
        super(LevelsWidget, self).__init__(parent)

        self.setTitle("Set display levels")

        # keep internal var for auto levelling toggle
        self.auto = True
        self.histo = True
        self.scaling = ""

        self.autoLevelBox = QtGui.QCheckBox(u"Automatic levels")
        self.autoLevelBox.setChecked(True)

        # informLabel = QtGui.QLabel("Linear scale, affects only display!")
        self.minLabel = QtGui.QLabel("minimum value: ")
        self.maxLabel = QtGui.QLabel("maximum value: ")

        self.scalingLabel = QtGui.QLabel("sqrt scale!")
        self.scalingLabel.setStyleSheet("color: red;")
        self.scaling2Label = QtGui.QLabel("sqrt scale!")
        self.scaling2Label.setStyleSheet("color: red;")
        self.minVal = 0.1
        self.maxVal = 1.

        self.minValSB = QtGui.QDoubleSpinBox()
        self.minValSB.setMinimum(-10e20)
        self.minValSB.setMaximum(10e20)
        self.maxValSB = QtGui.QDoubleSpinBox()
        self.maxValSB.setMinimum(-10e20)
        self.maxValSB.setMaximum(10e20)
        self.applyButton = QtGui.QPushButton("Apply levels")

        self.histogram = HistogramHLUTWidget()

        self.glayout = QtGui.QGridLayout()
        vlayout = QtGui.QVBoxLayout()
        self.glayout.addWidget(self.scaling2Label, 0, 0)
        self.glayout.addWidget(self.autoLevelBox, 0, 1)
        self.glayout.addWidget(self.minLabel, 1, 0)
        self.glayout.addWidget(self.minValSB, 1, 1)
        self.glayout.addWidget(self.maxLabel, 2, 0)
        self.glayout.addWidget(self.maxValSB, 2, 1)
        self.glayout.addWidget(self.scalingLabel, 3, 0)
        self.glayout.addWidget(self.applyButton, 3, 1)
        vlayout.addLayout(self.glayout)
        vlayout.addWidget(self.histogram)

        self.hideControls()
        self.setLayout(vlayout)
        self.applyButton.clicked.connect(self.check_and_emit)
        self.autoLevelBox.stateChanged.connect(self.autoLevelChange)
        self.histogram.item.sigLevelsChanged.connect(self.levelChange)
        self.updateLevels(self.minVal, self.maxVal)

    def changeview(self, showhistogram=False):
        if showhistogram:
            self.histo = True
            self.histogram.show()
            # self.autoLevelBox.hide()
            self.applyButton.hide()
            self.scalingLabel.hide()
            self.scaling2Label.show()
            self.maxValSB.setReadOnly(True)
            self.minValSB.setReadOnly(True)
            self.histogram.fillHistogram(True)
        else:
            self.histo = False
            # self.autoLevelBox.show()
            self.applyButton.show()
            self.scalingLabel.show()
            self.scaling2Label.hide()
            self.histogram.hide()
            self.maxValSB.setReadOnly(False)
            self.minValSB.setReadOnly(False)
            self.histogram.fillHistogram(False)

    def isAutoLevel(self):
        return self.auto

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

    def levelChange(self, histo):
        levels = histo.region.getRegion()
        lowlim = self.minValSB.value()
        uplim = self.maxValSB.value()
        if levels[0] != lowlim or levels[1] != uplim:
            self.minValSB.setValue(levels[0])
            self.maxValSB.setValue(levels[1])
            if not self.auto:
                self.check_and_emit()

    def check_and_emit(self):
        # check if the minimum value is actually smaller than the maximum
        self.minVal = self.minValSB.value()
        self.maxVal = self.maxValSB.value()
        if (self.maxVal - self.minVal) <= 0:
            if(self.minVal >= 1.):
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
        self.applyButton.setEnabled(False)

    def showControls(self):
        self.minValSB.setEnabled(True)
        self.maxValSB.setEnabled(True)
        self.applyButton.setEnabled(True)

    def setScalingLabel(self, scalingType):
        lowlim = float(self.minValSB.value())
        uplim = float(self.maxValSB.value())
        if scalingType == "log":
            if scalingType != self.scaling:
                self.scalingLabel.setText("log scale!")
                self.scaling2Label.setText("log scale!")
                if not self.auto:
                    if self.scaling == "lin":
                        lowlim =  math.log10(lowlim or 10e-3) if lowlim > 0 else -2
                        uplim =  math.log10(uplim or 10e-3 ) if uplim > 0 else -2
                    elif self.scaling == "sqrt":
                        lowlim =  math.log10(lowlim * lowlim or 10e-3) if lowlim > 0 else -2
                        uplim =  math.log10(uplim * uplim or 10e-3) if uplim > 0 else -2
        elif scalingType == "lin":
            if scalingType != self.scaling:
                self.scalingLabel.setText("lin scale!")
                self.scaling2Label.setText("lin scale!")
                if not self.auto:
                    if self.scaling == "log":
                        lowlim =  math.pow(10, lowlim)
                        uplim =  math.pow(10, uplim)
                    elif self.scaling == "sqrt":
                        lowlim = lowlim * lowlim
                        uplim = uplim * uplim
        elif scalingType == "sqrt":
            if scalingType != self.scaling:
                self.scalingLabel.setText("sqrt scale!")
                self.scaling2Label.setText("sqrt scale!")
                if not self.auto:
                    if self.scaling == "lin":
                        lowlim =  math.sqrt(max(lowlim, 0))
                        uplim =  math.sqrt(max(uplim, 0))
                    elif self.scaling == "log":
                        lowlim =  math.sqrt(max(math.pow(10, lowlim), 0))
                        uplim =  math.sqrt(max(math.pow(10, uplim), 0))
        if scalingType != self.scaling:
            self.scaling = scalingType
        if not self.auto:
           if self.histo:
                self.histogram.region.setRegion([lowlim, uplim])
           else:
               self.minValSB.setValue(lowlim)
               self.maxValSB.setValue(uplim)
