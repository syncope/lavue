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


class GradientChoiceWidget(QtGui.QGroupBox):
    """
    Select how an image should be transformed.
    """
    
    chosenGradient = QtCore.pyqtSignal(QtCore.QString)

    def __init__(self, parent=None):
        super(gradientChooser_widget, self).__init__(parent)

        self.setTitle("Gradient choice")
        
        layout = QtGui.QHBoxLayout()
        self.cb = QtGui.QComboBox()        
        self.cb.addItem("reverseGrayscale")
        self.cb.addItem("highContrast")
        self.cb.addItem("thermal")
        self.cb.addItem("flame")
        self.cb.addItem("bipolar")
        self.cb.addItem("spectrum")
        self.cb.addItem("greyclip")
        self.cb.addItem("grey")
        layout.addWidget(self.cb)
        self.setLayout(layout)
        self.cb.activated.connect(self.emitText)
        
    def emitText(self, index):
        self.chosenGradient.emit(self.cb.itemText(index))
