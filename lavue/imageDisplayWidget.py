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

import pyqtgraph as pg
import math

from PyQt4 import QtCore, QtGui

from . import GradientItem as GI

class ImageDisplayWidget(pg.GraphicsLayoutWidget):
    
    currentMousePosition = QtCore.pyqtSignal(QtCore.QString)

    def __init__(self, parent = None):
        super(ImageDisplayWidget, self).__init__(parent)
        self.layout = self.ci
        self.crosshair_locked = False
        self.data = None
        self.autoDisplayLevels = True
        self.displayLevels = [None, None]

        self.viewbox = self.layout.addViewBox(row=0, col=1)

        self.image = pg.ImageItem()
        self.viewbox.addItem(self.image)
        
        leftAxis = pg.AxisItem('left')
        leftAxis.linkToView(self.viewbox)
        self.layout.addItem(leftAxis, row=0, col=0)
        
        bottomAxis = pg.AxisItem('bottom')
        bottomAxis.linkToView(self.viewbox)
        self.layout.addItem(bottomAxis, row=1, col =1)
        
        self.graditem = GI.GradientItem()
        self.graditem.setImageItem(self.image)
        
        self.layout.addItem(self.graditem, row = 0, col=2)
        
        self.layout.scene().sigMouseMoved.connect(self.mouse_position)
        self.layout.scene().sigMouseClicked.connect(self.mouse_click)
        
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=(255, 0, 0))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=(255, 0, 0))
        self.viewbox.addItem(self.vLine, ignoreBounds=True)
        self.viewbox.addItem(self.hLine, ignoreBounds=True)

    def addItem(self, item):
        self.image.additem(item)

    def updateImage(self, img=None):
        if(self.autoDisplayLevels):
            self.image.setImage(img, autoLevels = True)
        else:
            self.image.setImage(img, autoLevels = False, levels=self.displayLevels)
        self.data = img
    
    def updateGradient(self, name):
        self.graditem.setGradientByName(name)
    
    def mouse_position(self, event):
        try:
            mousePoint = self.image.mapFromScene(event)
            xdata = math.floor(mousePoint.x())
            ydata = math.floor(mousePoint.y())

            if not self.crosshair_locked:
                self.vLine.setPos(xdata+.5)
                self.hLine.setPos(ydata+.5)

            intensity = self.data[math.floor(xdata), math.floor(ydata)]
            self.currentMousePosition.emit("x=%.2f, y=%.2f, intensity=%.4f" % (xdata, ydata, intensity))
        except:
            pass

    def mouse_click(self, event):

        mousePoint = self.image.mapFromScene(event.scenePos())

        xdata = mousePoint.x()
        ydata = mousePoint.y()

        # if double click: fix mouse crosshair
        # another double click releases the crosshair again
        if event.double():
            self.crosshair_locked = not self.crosshair_locked
            if not self.crosshair_locked:
                self.vLine.setPos(xdata+.5)
                self.hLine.setPos(ydata+.5)

    def setAutoLevels(self, autoLvls):
        if(autoLvls):
            self.autoDisplayLevels = True
        else:
            self.autoDisplayLevels = False

    def setDisplayMinLevel(self, level = None ):
        if ( level is not None):
            self.displayLevels[0] = level
    
    def setDisplayMaxLevel(self, level = None ):
        if ( level is not None):
            self.displayLevels[1] = level
    
