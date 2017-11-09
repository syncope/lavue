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

from . import transformationsWidget
#~ from . import maskWidget
from . import bkgSubtractionWidget

    
class QHLine(QtGui.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtGui.QFrame.HLine)
        self.setFrameShadow(QtGui.QFrame.Sunken)


class PreparationBoxWidget(QtGui.QGroupBox):
    
    def __init__(self, parent=None):
        super(PreparationBoxWidget, self).__init__(parent)
        self.setTitle("Image preparation")

        #~ self.maskW = maskWidget.MaskWidget(parent=self)
        self.bkgSubW = bkgSubtractionWidget.BkgSubtractionkWidget(parent=self)

        hline = QHLine()

        self.trafoW = transformationsWidget.TransformationsWidget(parent=self)

        vlayout = QtGui.QVBoxLayout()
        #~ vlayout.addWidget(self.maskW)
        vlayout.addWidget(self.bkgSubW)
        vlayout.addWidget(hline)
        vlayout.addWidget(self.trafoW)

        self.setLayout(vlayout)
