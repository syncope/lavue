# Copyright (C) 2017  Christoph Rosemann, DESY, Notkestr. 85, D-22607 Hamburg
# email contact: christoph.rosemann@desy.de
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
        super(levels_widget, self).__init__(parent)

        self.setTitle("Set display levels")

        # keep internal var for auto levelling toggle
        self.auto = True
        
        self.autoLevelBox = QtGui.QCheckBox(u"Automatic levels")
        self.autoLevelBox.setChecked(True)
       
        #~ informLabel = QtGui.QLabel("Linear scale, affects only display!")
        minLabel = QtGui.QLabel("minimum value: ")
        maxLabel = QtGui.QLabel("maximum value: ")

        self.minVal = 0.1
        self.maxVal = 1.

        self.minValSB = QtGui.QDoubleSpinBox()
        self.minValSB.setMinimum(0.)
        self.maxValSB = QtGui.QDoubleSpinBox()
        self.maxValSB.setMinimum(1.)
        self.maxValSB.setMaximum(10e20)
        self.applyButton = QtGui.QPushButton("Apply levels")

        layout = QtGui.QGridLayout()
        #~ layout.addWidget(informLabel, 0, 0)
        layout.addWidget(self.autoLevelBox, 0,1)
        layout.addWidget(minLabel, 1, 0)
        layout.addWidget(self.minValSB, 1, 1)
        layout.addWidget(maxLabel, 2, 0)
        layout.addWidget(self.maxValSB, 2, 1)
        layout.addWidget(self.applyButton, 3, 1)

        self.setLayout(layout)
        self.applyButton.clicked.connect(self.check_and_emit)
        self.autoLevelBox.stateChanged.connect(self.autoLevelChange)

        self.updateLevels(self.minVal, self.maxVal)

    def isAutoLevel(self):
        return self.auto

    def autoLevelChange(self, value):
        if( value is 2):
            self.auto = True
            self.autoLevels.emit(1)
        else:
            self.auto = False
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

