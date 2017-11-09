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


class BkgSubtractionkWidget(QtGui.QWidget):

    """
    Define bkg image and subtract from displayed image.
    """

    bkgFileSelection = QtCore.pyqtSignal(str)
    useCurrentImageAsBKG = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(BkgSubtractionkWidget, self).__init__(parent)

        self.fileName = ""
        
        # one checkbox to choose whether the mask is applied
        self.applyBkgSubtractBox = QtGui.QCheckBox(u"Subtract Bkg")
        self.applyBkgSubtractBox.setChecked(False)
        self.applyBkgSubtractBox.setEnabled(False)
        
        label = QtGui.QLabel("Current image:")
        self.fileLabel = QtGui.QLabel("No image selected")
        
        # the dialog to select the mask file 
        self.selectButton = QtGui.QPushButton("Select")
        self.selectButton.clicked.connect(self.showImageSelection)
            
        self.selectCurrentButton = QtGui.QPushButton("Use current")
        self.selectCurrentButton.hide()
        self.selectCurrentButton.clicked.connect(self.useCurrent)
        
        self.selectFileButton = QtGui.QPushButton("Choose file")
        self.selectFileButton.hide()
        self.selectFileButton.clicked.connect(self.showFileDialog)
        
        selectlayout = QtGui.QHBoxLayout()
        selectlayout.addWidget(self.selectButton)
        selectlayout.addWidget(self.selectCurrentButton)
        selectlayout.addWidget(self.selectFileButton)
        
        layout = QtGui.QGridLayout()
        layout.addWidget(self.applyBkgSubtractBox, 0 ,0)
        layout.addLayout(selectlayout, 0, 1)
        layout.addWidget(label, 1, 0)
        layout.addWidget(self.fileLabel, 1, 1)
        
        self.setLayout(layout)

    def showFileDialog(self):
        self.fileDialog = QtGui.QFileDialog()

        self.fileName = str(self.fileDialog.getOpenFileName(self, 'Open file', '.'))
        self.setDisplayedName(self.fileName)
        self.bkgFileSelection.emit(self.fileName)
        self.hideImageSelection()

    def useCurrent(self):
        self.useCurrentImageAsBKG.emit()
        self.hideImageSelection()

    def setDisplayedName(self, name):
        if name == "":
            self.fileLabel.setText("No Image selected")
            self.applyBkgSubtractBox.setEnabled(False)
        else:
            self.fileLabel.setText("..." + str(name)[-24:])
            self.applyBkgSubtractBox.setEnabled(True)

    def showImageSelection(self):
        self.selectCurrentButton.show()
        self.selectFileButton.show()
        self.selectButton.hide()

    def hideImageSelection(self):
        self.selectCurrentButton.hide()
        self.selectFileButton.hide()
        self.selectButton.show()


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    myapp = BkgSubtractionkWidget()
    myapp.show()
    sys.exit(app.exec_())

