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


class image_widget(QtGui.QWidget):

    """
    The part of the GUI that incorporates the image view.
    """

     #~ = QtCore.pyqtSignal(bool)
    #~ initialLevels = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        super(image_widget, self).__init__(parent)

        self.nparray = None
        self.imageItem = None

        self.img_widget = ImageDisplay(parent=self)

        verticallayout = QtGui.QVBoxLayout()

        filenamelayout = QtGui.QHBoxLayout()

        filelabel = QtGui.QLabel("Image/File name: ")
        filenamelayout.addWidget(filelabel)
        self.filenamedisplay = QtGui.QLineEdit()
        filenamelayout.addWidget(self.filenamedisplay)

        verticallayout.addLayout(filenamelayout)
        verticallayout.addWidget(self.img_widget)

        pixelvaluelayout = QtGui.QHBoxLayout()
        pixellabel = QtGui.QLabel("Pixel position and intensity: ")
        pixelvaluelayout.addWidget(pixellabel)

        self.infodisplay = QtGui.QLineEdit()
        pixelvaluelayout.addWidget(self.infodisplay)
        verticallayout.addLayout(pixelvaluelayout)
        
        self.setLayout(verticallayout)
        self.img_widget.currentMousePosition.connect(self.infodisplay.setText)

    def plot(self, array, name=None):
        if array is None:
            return
        if name is not None:
            self.filenamedisplay.setText(name)

        self.img_widget.updateImage(array)

    def setAutoLevels(self, autoLvls):
        self.img_widget.setAutoLevels(autoLvls)

    def setMinLevel(self, level = None):
        self.img_widget.setDisplayMinLevel(level)

    def setMaxLevel(self, level = None):
        self.img_widget.setDisplayMaxLevel(level)

    def changeGradient(self, name):
        self.img_widget.updateGradient(name)
