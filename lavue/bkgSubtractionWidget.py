# Copyright (C) 2017  Christoph Rosemann, DESY, Notkestr. 85, D-22607 Hamburg
# email contact: christoph.rosemann@desy.de
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


from PyQt4 import QtCore, QtGui


class BkgSubtractionkWidget(QtGui.QGroupBox):

    """
    Define bkg image and subtract from displayed image.
    """

    bkgFileSelection = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(BkgSubtractionkWidget, self).__init__(parent)

        self.setTitle("Bkg subtraction")
        self.fileName = ""
        
        # one checkbox to choose whether the mask is applied
        self.applyBkgSubtractBox = QtGui.QCheckBox(u"Subtract")
        self.applyBkgSubtractBox.setChecked(False)
        
        # the dialog to select the mask file 
        self.fileNameLabel = QtGui.QLabel("Bkg file:")
        self.fileNameDisplay = QtGui.QLabel(str(self.fileName))
        self.fileSelectButton = QtGui.QPushButton("Select bkg file")
        self.fileSelectButton.clicked.connect(self.showFileDialog)
        
        masterlayout = QtGui.QVBoxLayout()
        layout = QtGui.QGridLayout()
        layout.addWidget(self.applyBkgSubtractBox, 0,0)
        layout.addWidget(self.fileSelectButton, 0, 1)
        layout.addWidget(self.fileNameLabel, 1, 0)

        masterlayout.addItem(layout)
        masterlayout.addWidget(self.fileNameDisplay)
        
        self.setLayout(masterlayout)

    def showFileDialog(self):
        self.fileDialog = QtGui.QFileDialog()

        self.fileName = str(self.fileDialog.getOpenFileName(self, 'Open file', '.'))
        self.setFileName(self.fileName)
        self.bkgFileSelection.emit(self.fileName)

    def setFileName(self, fname):
        self.fileNameDisplay.setText(str(fname))

if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    myapp = BkgSubtractionkWidget()
    myapp.show()
    sys.exit(app.exec_())

