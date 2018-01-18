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

""" gradient choice widget """

from PyQt4 import QtCore, QtGui


class GradientChoiceWidget(QtGui.QGroupBox):

    """
    Select how an image should be transformed.
    """

    chosenGradient = QtCore.pyqtSignal(str)
    channelChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtGui.QGroupBox.__init__(self, parent)

        self.setTitle("Gradient choice")
        self.colorchannel = 0
        self.numberofchannels = 0

        vlayout = QtGui.QVBoxLayout()
        hlayout = QtGui.QHBoxLayout()
        self.cb = QtGui.QComboBox()
        self.cb.addItem("reversegrey")
        self.cb.addItem("highcontrast")
        self.cb.addItem("thermal")
        self.cb.addItem("flame")
        self.cb.addItem("bipolar")
        self.cb.addItem("spectrum")
        self.cb.addItem("spectrumclip")
        self.cb.addItem("greyclip")
        self.cb.addItem("grey")
        self.cb.addItem("cyclic")
        self.cb.addItem("yellowy")
        self.cb.addItem("inverted")
        self.cb.setToolTip("gradient for the color distribution of the image")
        vlayout.addWidget(self.cb)
        self.channelLabel = QtGui.QLabel("Color channel:")
        self.channelComboBox = QtGui.QComboBox()
        hlayout.addWidget(self.channelLabel)
        hlayout.addWidget(self.channelComboBox)
        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)
        self.cb.activated.connect(self.emitText)
        self.setNumberOfChannels(-1)
        self.channelComboBox.currentIndexChanged.connect(self.setChannel)

    @QtCore.pyqtSlot(int)
    def setChannel(self, channel):
        if self.colorchannel != channel:
            if channel >= 0 and channel <= self.numberofchannels + 1:
                self.colorchannel = channel
                self.channelChanged.emit()

    def setNumberOfChannels(self, number):
        if number != self.numberofchannels:
            self.numberofchannels = int(max(number, 0))
            if self.numberofchannels > 0:
                for i in reversed(range(0, self.channelComboBox.count())):
                    self.channelComboBox.removeItem(i)
                self.channelComboBox.addItem("Sum")

                self.channelComboBox.addItems(
                    ["Channel %s" % (ch + 1)
                     for ch in range(self.numberofchannels)])

                self.channelComboBox.addItem("Mean")
                self.channelLabel.show()
                self.channelComboBox.show()
            else:
                self.channelLabel.hide()
                self.channelComboBox.hide()

    @QtCore.pyqtSlot(int)
    def emitText(self, index):
        self.chosenGradient.emit(self.cb.itemText(index))

    @QtCore.pyqtSlot(str)
    def changeGradient(self, name):
        text = self.cb.currentText()
        if text != name:
            cid = self.cb.findText(name)
            if cid > -1:
                self.cb.setCurrentIndex(cid)
            else:
                print("Error %s" % name)
