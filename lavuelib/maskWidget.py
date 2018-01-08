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

""" mask widget """

from PyQt4 import QtCore, QtGui


class MaskWidget(QtGui.QWidget):

    """
    Define and apply masking of the displayed image.
    """

    maskFileSelection = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.fileName = "No Image selected"
        self.fileDialog = None
        # one checkbox to choose whether the mask is applied
        self.applyMaskBox = QtGui.QCheckBox(u"Apply mask")
        self.applyMaskBox.setChecked(False)
        self.applyMaskBox.setChecked(False)
        self.applyMaskBox.setEnabled(False)
        self.applyMaskBox.setToolTip("apply mask to the image")

        # the dialog to select the mask file
        self.fileNameLabel = QtGui.QLabel("Mask image:")
        self.fileNameLabel.setToolTip("mask image file name")
        self.fileNameDisplay = QtGui.QLabel(str(self.fileName))
        self.fileNameDisplay.setToolTip("mask image file name")
        self.fileSelectButton = QtGui.QPushButton("Select")
        self.fileSelectButton.clicked.connect(self.showFileDialog)
        self.fileSelectButton.setToolTip("select file for the mask")

        masterlayout = QtGui.QVBoxLayout()
        layout = QtGui.QGridLayout()
        layout.addWidget(self.applyMaskBox, 0, 0)
        layout.addWidget(self.fileSelectButton, 0, 1)
        layout.addWidget(self.fileNameLabel, 1, 0)
        layout.addWidget(self.fileNameDisplay, 1, 1)

        masterlayout.addItem(layout)

        self.setLayout(masterlayout)

    @QtCore.pyqtSlot()
    def showFileDialog(self):
        self.fileDialog = QtGui.QFileDialog()
        self.fileName = str(
            self.fileDialog.getOpenFileName(
                self, 'Open mask file', '/ramdisk/'))
        if fileName:
            self.fileName = fileName
            self.setDisplayedName(self.fileName)
            self.maskFileSelection.emit(self.fileName)

    def setDisplayedName(self, name):
        if name == "":
            self.fileNameDisplay.setText("No Image selected")
            self.applyMaskBox.setEnabled(False)
        else:
            self.fileNameDisplay.setText("..." + str(name)[-24:])
            self.applyMaskBox.setEnabled(True)

    def setFileName(self, fname):
        if len(fname) > 4 and fname != "NO IMAGE":
            self.fileSelectButton.setText("Mask selected")
        else:
            self.noImage()

    def noImage(self):
        self.fileName = "NO IMAGE"
        self.applyMaskBox.setChecked(False)

    def showMinimum(self):
        self.fileSelectButton.hide()

    def showAll(self):
        self.fileSelectButton.show()


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    myapp = MaskWidget()
    myapp.show()
    sys.exit(app.exec_())
