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


import math

from PyQt4 import QtCore, QtGui

from . import imageDisplayWidget


class ImageWidget(QtGui.QWidget):

    """
    The part of the GUI that incorporates the image view.
    """

    roiCoordsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)

        self.nparray = None
        self.imageItem = None

        self.img_widget = imageDisplayWidget.ImageDisplayWidget(parent=self)

        verticallayout = QtGui.QVBoxLayout()

        filenamelayout = QtGui.QHBoxLayout()

        filelabel = QtGui.QLabel("Image/File name: ")
        filenamelayout.addWidget(filelabel)
        self.filenamedisplay = QtGui.QLineEdit()
        filenamelayout.addWidget(self.filenamedisplay)
        self.cnfButton = QtGui.QPushButton("Configuration")
        filenamelayout.addWidget(self.cnfButton)

        verticallayout.addLayout(filenamelayout)
        verticallayout.addWidget(self.img_widget)

        self.pixelComboBox = QtGui.QComboBox()
        self.pixelComboBox.addItem("Intensity")
        self.pixelComboBox.addItem("ROI")

        pixelvaluelayout = QtGui.QHBoxLayout()
        self.pixellabel = QtGui.QLabel("Pixel position and intensity: ")

        self.infodisplay = QtGui.QLineEdit()
        self.infodisplay.setReadOnly(True)

        self.roiLabel = QtGui.QLabel("ROIs label: ")
        self.labelROILineEdit = QtGui.QLineEdit("")
        self.addROIButton = QtGui.QPushButton("Add ROI")
        self.clearAllButton = QtGui.QPushButton("Clear All")

        pixelvaluelayout.addWidget(self.pixellabel)
        pixelvaluelayout.addWidget(self.infodisplay)
        pixelvaluelayout.addWidget(self.roiLabel)
        pixelvaluelayout.addWidget(self.labelROILineEdit)
        pixelvaluelayout.addWidget(self.addROIButton)
        pixelvaluelayout.addWidget(self.clearAllButton)
        pixelvaluelayout.addWidget(self.pixelComboBox)
        verticallayout.addLayout(pixelvaluelayout)

        self.setLayout(verticallayout)
        self.img_widget.currentMousePosition.connect(self.infodisplay.setText)

        self.pixelComboBox.currentIndexChanged.connect(self.onPixelChanged)
        self.img_widget.roi.sigRegionChanged.connect(self.roiChanged)
        self.labelROILineEdit.textEdited.connect(self.updateROIButton)
        self.onPixelChanged()
        self.updateROIButton()

    def updateROIButton(self):
        if not str(self.labelROILineEdit.text()).strip():
            self.addROIButton.setEnabled(False)
            self.clearAllButton.setEnabled(False)
        else:
            self.addROIButton.setEnabled(True)
            self.clearAllButton.setEnabled(True)

    def onPixelChanged(self):
        #        index = self.pixelComboBox.currentIndex()
        text = self.pixelComboBox.currentText()
        if text == "ROI":
            self.img_widget.vLine.hide()
            self.img_widget.hLine.hide()
            self.addROIButton.show()
            self.clearAllButton.show()
            self.labelROILineEdit.show()
            self.pixellabel.setText("[x1, y1, x2, y2]: ")
            self.roiLabel.show()
            self.img_widget.roi.show()
            self.img_widget.roienable = True
            self.img_widget.roi.show()
            self.infodisplay.setText("")
            self.roiChanged()
        else:
            self.pixellabel.setText("Pixel position and intensity: ")
            self.img_widget.roi.hide()
            self.addROIButton.hide()
            self.labelROILineEdit.hide()
            self.clearAllButton.hide()
            self.roiLabel.hide()
            self.img_widget.roienable = False
            self.img_widget.vLine.show()
            self.img_widget.hLine.show()
            self.infodisplay.setText("")
            self.roiCoordsChanged.emit()

    def roiChanged(self):
        try:
            state = self.img_widget.roi.state
            ptx = int(math.floor(state['pos'].x()))
            pty = int(math.floor(state['pos'].y()))
            szx = int(math.floor(state['size'].x()))
            szy = int(math.floor(state['size'].y()))
            self.img_widget.roicoords = [ptx, pty, ptx + szx, pty + szy]
            self.roiCoordsChanged.emit()
        except Exception as e:
            print "Warning: ", str(e)

    def plot(self, array, name=None):
        if array is None:
            return
        if name is not None:
            self.filenamedisplay.setText(name)

        self.img_widget.updateImage(array)

    def setAutoLevels(self, autoLvls):
        self.img_widget.setAutoLevels(autoLvls)

    def setMinLevel(self, level=None):
        self.img_widget.setDisplayMinLevel(level)

    def setMaxLevel(self, level=None):
        self.img_widget.setDisplayMaxLevel(level)

    def changeGradient(self, name):
        self.img_widget.updateGradient(name)
