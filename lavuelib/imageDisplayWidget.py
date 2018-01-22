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

""" image display widget """

import pyqtgraph as pg
import numpy as np
import math
from pyqtgraph.graphicsItems.ROI import ROI, LineROI
from PyQt4 import QtCore, QtGui

VMAJOR, VMINOR, VPATCH = pg.__version__.split(".") \
    if pg.__version__ else ("0", "9", "0")


class SimpleLineROI(LineROI):
    def __init__(self, pos1, pos2, **args):
        pos1 = pg.Point(pos1)
        pos2 = pg.Point(pos2)
        d = pos2 - pos1
        l = d.length()
        ang = pg.Point(1, 0).angle(d)

        ROI.__init__(self, pos1, size=pg.Point(l, 1), angle=ang, **args)
        self.addScaleRotateHandle([0, 0.5], [1, 0.5])
        self.addScaleRotateHandle([1, 0.5], [0, 0.5])

    def getCoordinates(self):
        ang = self.state['angle']
        pos1 = self.state['pos']
        size = self.state['size']
        ra = ang * np.pi / 180.
        pos2 = pos1 + pg.Point(size.x() * math.cos(ra),
                               size.x() * math.sin(ra))
        return [pos1.x(), pos1.y(), pos2.x(), pos2.y()]


class ImageDisplayWidget(pg.GraphicsLayoutWidget):

    currentMousePosition = QtCore.pyqtSignal(QtCore.QString)
    centerAngleChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        pg.GraphicsLayoutWidget.__init__(self, parent)
        self.layout = self.ci
        self.crosshair_locked = False
        self.roienable = False
        self.cutenable = False
        self.qenable = False
        self.roicoords = [[10, 10, 60, 60]]
        self.currentroi = 0
        self.currentcut = 0
        self.cutcoords = [[10, 10, 60, 10]]
        self.data = None
        self.rawdata = None
        self.autoDisplayLevels = True
        self.displayLevels = [None, None]
        self.viewbox = self.layout.addViewBox(row=0, col=1)
        self.doBkgSubtraction = False
        self.scaling = "sqrt"
        self.image = pg.ImageItem()
        self.viewbox.addItem(self.image)
        self.xdata = 0
        self.ydata = 0
        self.statswoscaling = False

        #: (:obj:`tuple` <:obj:`float`, :obj:`float`> ) image scale (x,y)
        self.scale = None
        #: (:obj:`tuple` <:obj:`float`, :obj:`float`> )
        #    position of the first pixel
        self.position = None

        #: (:obj:`float`) x-coordinates of the center of the image
        self.centerx = 0.0
        #: (:obj:`float`) y-coordinates of the center of the image
        self.centery = 0.0
        #: (:obj:`float`) energy in eV
        self.energy = 0.0
        #: (:obj:`float`) pixel x-size in um
        self.pixelsizex = 0.0
        #: (:obj:`float`) pixel y-size in um
        self.pixelsizey = 0.0
        #: (:obj:`float`) detector distance in mm
        self.detdistance = 0.0
        #: (:obj:`int`) geometry space index -> 0: angle, 1 q-space
        self.gspaceindex = 0

        self.viewonetoone = QtGui.QAction(
            "View 1:1 pixels", self.viewbox.menu)
        self.viewonetoone.triggered.connect(self.oneToOneRange)
        if VMAJOR == '0' and int(VMINOR) < 10 and int(VPATCH) < 9:
            self.viewbox.menu.axes.insert(0, self.viewonetoone)
        self.viewbox.menu.addAction(self.viewonetoone)

        leftAxis = pg.AxisItem('left')
        leftAxis.linkToView(self.viewbox)
        self.layout.addItem(leftAxis, row=0, col=0)

        bottomAxis = pg.AxisItem('bottom')
        bottomAxis.linkToView(self.viewbox)
        self.layout.addItem(bottomAxis, row=1, col=1)

        self.layout.scene().sigMouseMoved.connect(self.mouse_position)
        self.layout.scene().sigMouseClicked.connect(self.mouse_click)

        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=(255, 0, 0))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=(255, 0, 0))
        self.viewbox.addItem(self.vLine, ignoreBounds=True)
        self.viewbox.addItem(self.hLine, ignoreBounds=True)

        self.roi = []
        self.roi.append(ROI(0, pg.Point(50, 50)))
        self.roi[0].addScaleHandle([1, 1], [0, 0])
        self.roi[0].addScaleHandle([0, 0], [1, 1])
        self.viewbox.addItem(self.roi[0])
        self.roi[0].hide()

        self.cut = []
        self.cut.append(SimpleLineROI([10, 10], [60, 10], pen='r'))
        self.viewbox.addItem(self.cut[0])
        self.cut[0].hide()

    def setAspectLocked(self, flag):
        self.viewbox.setAspectLocked(flag)

    def addItem(self, item, **args):
        self.image.additem(item)

    def addROI(self, coords=None):
        if not coords or not isinstance(coords, list) or len(coords) != 4:
            pnt = 10 * len(self.roi)
            sz = 50
            coords = [pnt, pnt, pnt + sz, pnt + sz]
            spnt = pg.Point(sz, sz)
        else:
            pnt = pg.Point(coords[0], coords[1])
            spnt = pg.Point(coords[2] - coords[0], coords[3] - coords[1])
        self.roi.append(ROI(pnt, spnt))
        self.roi[-1].addScaleHandle([1, 1], [0, 0])
        self.roi[-1].addScaleHandle([0, 0], [1, 1])
        self.viewbox.addItem(self.roi[-1])

        self.roicoords.append(coords)

    def removeROI(self):
        roi = self.roi.pop()
        roi.hide()
        self.viewbox.removeItem(roi)
        self.roicoords.pop()

    def addCut(self, coords=None):
        if not coords or not isinstance(coords, list) or len(coords) != 4:
            pnt = 10 * (len(self.cut) + 1)
            sz = 50
            coords = [pnt, pnt, pnt + sz, pnt]
        self.cut.append(SimpleLineROI(coords[:2], coords[2:], pen='r'))
        self.viewbox.addItem(self.cut[-1])
        self.cutcoords.append(coords)

    def removeCut(self):
        cut = self.cut.pop()
        cut.hide()
        self.viewbox.removeItem(cut)
        self.cutcoords.pop()

    def oneToOneRange(self):
        ps = self.image.pixelSize()
        currange = self.viewbox.viewRange()
        xrg = currange[0][1] - currange[0][0]
        yrg = currange[1][1] - currange[1][0]
        if self.scale is not None and self.position is not None:
            self.viewbox.setRange(
                QtCore.QRectF(
                    self.position[0],
                    self.position[1],
                    xrg * ps[0],
                    yrg * ps[1]),
                padding=0)
        else:
            self.viewbox.setRange(
                QtCore.QRectF(0, 0, xrg * ps[0], yrg * ps[1]),
                padding=0)

    def setScale(self, position, scale):
        self.position = tuple(position)
        self.scale = tuple(scale)
        self.image.resetTransform()
        self.image.scale(*scale)
        self.image.setPos(*position)

    def updateImage(self, img=None, rawimg=None):
        # print("H %s" % str(self.image.height()))
        # print("W %s" % str(self.image.width()))
        self.setScale((100, -100), (0.01, 0.02))
        if self.autoDisplayLevels:
            self.image.setImage(img, autoLevels=True)
        else:
            self.image.setImage(
                img, autoLevels=False, levels=self.displayLevels)
        # self.image.setRect(QtCore.QRectF(-100, 100, self.image.width() * 0.1, self.image.height() * 0.1))
        self.data = img
        self.rawdata = rawimg
        self.mouse_position()

    @QtCore.pyqtSlot(object)
    def mouse_position(self, event=None):
        try:
            if event is not None:
                mousePoint = self.image.mapFromScene(event)
                self.xdata = math.floor(mousePoint.x())
                self.ydata = math.floor(mousePoint.y())
            if not self.roienable and not self.cutenable:
                if not self.crosshair_locked:
                    if self.scale is not None and self.position is not None:
                        self.vLine.setPos((self.xdata + .5) * self.scale[0] \
                                          + self.position[0])
                        self.hLine.setPos((self.ydata + .5) * self.scale[1] \
                                          + self.position[1])
                    else:
                        self.vLine.setPos(self.xdata + .5)
                        self.hLine.setPos(self.ydata + .5)

            if self.rawdata is not None:
                try:
                    xf = int(math.floor(self.xdata))
                    yf = int(math.floor(self.ydata))
                    if xf >= 0 and yf >= 0 and  xf < self.rawdata.shape[0] \
                       and yf < self.rawdata.shape[1]:
                        intensity = self.rawdata[xf, yf]
                    else:
                        intensity = 0.
                except Exception:
                    intensity = 0.
            else:
                intensity = 0.
            scaling = self.scaling if not self.statswoscaling else "linear"
            ilabel = "intensity"
            if not self.roienable:
                if self.doBkgSubtraction:
                    ilabel = "%s(intensity-background)" % (
                        scaling if scaling != "linear" else "")
                else:
                    if scaling == "linear":
                        ilabel = "intensity"
                    else:
                        ilabel = "%s(intensity)" % scaling
            if not self.roienable and not self.cutenable and not self.qenable:
                self.currentMousePosition.emit(
                    "x=%i, y=%i, %s=%.2f" % (
                        self.xdata, self.ydata, ilabel,
                        intensity))
            elif self.roienable and self.currentroi > -1:
                if event:
                    self.currentMousePosition.emit(
                        "%s" % self.roicoords[self.currentroi])
            elif self.cutenable:
                if self.currentcut > -1:
                    crds = self.cutcoords[self.currentcut]
                    crds = "[[%.2f, %.2f], [%.2f, %.2f]]" % tuple(crds)
                else:
                    crds = "[[0, 0], [0, 0]]"
                self.currentMousePosition.emit(
                    "%s, x=%i, y=%i, %s(intensity-background)=%.2f" % (
                        crds, self.xdata, self.ydata, ilabel,
                        intensity))
            elif self.qenable and self.energy > 0 and self.detdistance > 0:
                if self.gspaceindex == 0:
                    thetax, thetay, thetatotal = self.pixel2theta(
                        self.xdata, self.ydata)
                    self.currentMousePosition.emit(
                        "th_x=%.5f deg, th_y=%.5f deg,"
                        " th_tot=%.5f deg, %s=%.2f"
                        % (thetax, thetay, thetatotal, ilabel, intensity))
                else:
                    qx, qz, q = self.pixel2q(self.xdata, self.ydata)
                    self.currentMousePosition.emit(
                        "q_x=%.5f 1/A, q_z=%.5f 1/A, q=%.5f 1/A, %s=%.2f"
                        % (qx, qz, q, ilabel, intensity))

            else:
                self.currentMousePosition.emit("")

        except Exception:
            # print("Warning: %s" % str(e))
            pass

    def pixel2theta(self, xdata, ydata):
        xcentered = xdata - self.centerx
        ycentered = ydata - self.centery
        thetax = math.atan(
            xcentered * self.pixelsizex/1000. / self.detdistance)
        thetay = math.atan(
            ycentered * self.pixelsizey/1000. / self.detdistance)
        r = math.sqrt((xcentered * self.pixelsizex / 1000.) ** 2
                      + (ycentered * self.pixelsizex / 1000.) ** 2)
        thetatotal = math.atan(r/self.detdistance)*180/math.pi
        return thetax, thetay, thetatotal

    def pixel2q(self, xdata, ydata):
        thetax, thetay, thetatotal = self.pixel2theta(
            self.xdata, self.ydata)
        wavelength = 12400./self.energy
        qx = 4 * math.pi / wavelength * math.sin(thetax/2.)
        qz = 4 * math.pi / wavelength * math.sin(thetay/2.)
        q = 4 * math.pi / wavelength * math.sin(thetatotal/2.)
        return qx, qz, q

    @QtCore.pyqtSlot(object)
    def mouse_click(self, event):

        mousePoint = self.image.mapFromScene(event.scenePos())

        xdata = mousePoint.x()
        ydata = mousePoint.y()

        # if double click: fix mouse crosshair
        # another double click releases the crosshair again
        if event.double():
            if not self.roienable and not self.cutenable and not self.qenable:
                self.crosshair_locked = not self.crosshair_locked
                if not self.crosshair_locked:
                    self.vLine.setPos(xdata + .5)
                    self.hLine.setPos(ydata + .5)
            if self.qenable:
                self.crosshair_locked = False
                self.centerx = float(xdata)
                self.centery = float(ydata)
                self.centerAngleChanged.emit()

    def setAutoLevels(self, autoLvls):
        if autoLvls:
            self.autoDisplayLevels = True
        else:
            self.autoDisplayLevels = False

    def setDisplayMinLevel(self, level=None):
        if level is not None:
            self.displayLevels[0] = level

    def setDisplayMaxLevel(self, level=None):
        if level is not None:
            self.displayLevels[1] = level
