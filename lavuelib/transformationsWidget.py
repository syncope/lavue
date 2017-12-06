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

""" transformation widget """


from PyQt4 import QtCore, QtGui


class TransformationsWidget(QtGui.QWidget):
    # still pending implemntation -> needs scipy, probably

    """
    Select how an image should be transformed.
    """
    activatedTransformation = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.cb = QtGui.QComboBox()
        self.cb.addItem("None")
        self.cb.addItem("flip (ud)")
        self.cb.addItem("flip (lr)")
        self.cb.addItem("transpose")
        self.cb.addItem("rot90 (cw)")
        self.cb.addItem("rot180")
        self.cb.addItem("rot270 (cw)")
        self.cb.addItem("rot180 + transpose")

        layout = QtGui.QHBoxLayout()
        self.label = QtGui.QLabel("Transformation:")
        layout.addWidget(self.label)
        layout.addWidget(self.cb)
        self.setLayout(layout)
        self.cb.currentIndexChanged.connect(self.broadcastTransformation)

    def broadcastTransformation(self, index):
        self.activatedTransformation.emit(self.cb.itemText(index))
