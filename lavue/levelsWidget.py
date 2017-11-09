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


class LevelsWidget(QtGui.QGroupBox):

    """
    Set minimum and maximum displayed values.
    """

    changeMinLevel = QtCore.pyqtSignal(float)
    changeMaxLevel = QtCore.pyqtSignal(float)
    autoLevels = QtCore.pyqtSignal(int) # bool does not work...
    levelsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(LevelsWidget, self).__init__(parent)

        self.setTitle("Set display levels")

        # keep internal var for auto levelling toggle
        self.auto = True
        
        self.autoLevelBox = QtGui.QCheckBox(u"Automatic levels")
        self.autoLevelBox.setChecked(True)
       
        #~ informLabel = QtGui.QLabel("Linear scale, affects only display!")
        self.minLabel = QtGui.QLabel("minimum value: ")
        self.maxLabel = QtGui.QLabel("maximum value: ")

        self.scalingLabel = QtGui.QLabel("sqrt scale!")
        self.minVal = 0.1
        self.maxVal = 1.

        self.minValSB = QtGui.QDoubleSpinBox()
        self.minValSB.setMinimum(-2.)
        self.maxValSB = QtGui.QDoubleSpinBox()
        self.maxValSB.setMinimum(-1.)
        self.maxValSB.setMaximum(10e20)
        self.applyButton = QtGui.QPushButton("Apply levels")

        layout = QtGui.QGridLayout()
        #~ layout.addWidget(informLabel, 0, 0)
        layout.addWidget(self.autoLevelBox, 0,1)
        layout.addWidget(self.minLabel, 1, 0)
        layout.addWidget(self.minValSB, 1, 1)
        layout.addWidget(self.maxLabel, 2, 0)
        layout.addWidget(self.maxValSB, 2, 1)
        layout.addWidget(self.scalingLabel, 3, 0)
        layout.addWidget(self.applyButton, 3, 1)

        self.hideControls()
        self.setLayout(layout)
        self.applyButton.clicked.connect(self.check_and_emit)
        self.autoLevelBox.stateChanged.connect(self.autoLevelChange)

        self.updateLevels(self.minVal, self.maxVal)

    def isAutoLevel(self):
        return self.auto

    def autoLevelChange(self, value):
        if( value is 2):
            self.auto = True
            self.hideControls()
            self.autoLevels.emit(1)
        else:
            self.auto = False
            self.showControls()
            self.autoLevels.emit(0)
            self.check_and_emit()
        self.levelsChanged.emit()

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

    def hideControls(self):
        self.minValSB.setEnabled(False)
        self.maxValSB.setEnabled(False)
        self.applyButton.setEnabled(False)

    def showControls(self):
        self.minValSB.setEnabled(True)
        self.maxValSB.setEnabled(True)
        self.applyButton.setEnabled(True)

    def setScalingLabel(self, scalingType):
        if scalingType == "log":
            self.scalingLabel.setText("log scale!")
        elif  scalingType == "lin":
            self.scalingLabel.setText("lin scale!")
        elif  scalingType == "sqrt":
            self.scalingLabel.setText("sqrt scale!")

