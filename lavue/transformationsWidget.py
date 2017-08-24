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


class TransformationsWidget(QtGui.QGroupBox):
    # still pending implemntation -> needs scipy, probably
    """
    Select how an image should be transformed.
    """
    changeFlip = QtCore.pyqtSignal(int)
    changeMirror = QtCore.pyqtSignal(int)
    changeRotate = QtCore.pyqtSignal(int)


    def __init__(self, parent=None):
        super(TransformationsWidget, self).__init__(parent)

        self.setTitle("Image transformations")
        
        layout = QtGui.QHBoxLayout()
        self.cb = QtGui.QComboBox()        
        self.cb.addItem("None")
        self.cb.addItem("flip")
        self.cb.addItem("mirror")
        self.cb.addItem("rotate")
        #~ layout.addStretch(1)
        layout.addWidget(self.cb)
        self.setLayout(layout)
        
        #~ horizontallayout.addWidget(self.flip)
        #~ horizontallayout.addWidget(self.mirror)
        #~ horizontallayout.addWidget(self.rotate90)
        #~ 
        #~ self.setLayout(horizontallayout)
        #~ 
        #~ # signals:
        #~ self.flip.stateChanged.connect(self.changeFlip.emit)
        #~ self.mirror.stateChanged.connect(self.changeMirror.emit)
        #~ self.rotate90.stateChanged.connect(self.changeRotate.emit)
#~ 
