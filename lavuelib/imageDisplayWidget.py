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

import pyqtgraph as _pg
import numpy as np
import math
from pyqtgraph.graphicsItems.ROI import ROI, LineROI
from PyQt4 import QtCore, QtGui

from . import axesDialog
from . import geometryDialog
from . import displayParameters

_VMAJOR, _VMINOR, _VPATCH = _pg.__version__.split(".") \
    if _pg.__version__ else ("0", "9", "0")


class SimpleLineROI(LineROI):
    """ simple line roi """

    def __init__(self, pos1, pos2, **args):
        """ constructor

        :param pos1: start position
        :type pos1: [float, float]
        :param pos2: end position
        :type pos2: [float, float]
        :param args: dictionary with ROI parameters
        :type args: :obj:`dict`<:obj:`str`, :obj:`any`>
        """

        pos1 = _pg.Point(pos1)
        pos2 = _pg.Point(pos2)
        d = pos2 - pos1
        l = d.length()
        ang = _pg.Point(1, 0).angle(d)

        ROI.__init__(self, pos1, size=_pg.Point(l, 1), angle=ang, **args)
        self.addScaleRotateHandle([0, 0.5], [1, 0.5])
        self.addScaleRotateHandle([1, 0.5], [0, 0.5])

    def getCoordinates(self):
        """ provides the roi coordinates

        :returns: x1, y1, x2, y2 positions of the roi
        :rtype: [float, float, float, float]
        """
        ang = self.state['angle']
        pos1 = self.state['pos']
        size = self.state['size']
        ra = ang * np.pi / 180.
        pos2 = pos1 + _pg.Point(
            size.x() * math.cos(ra),
            size.x() * math.sin(ra))
        return [pos1.x(), pos1.y(), pos2.x(), pos2.y()]


class ImageDisplayWidget(_pg.GraphicsLayoutWidget):

    #: (:class:`PyQt4.QtCore.pyqtSignal`) roi coordinate changed signal
    roiCoordsChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) cut coordinate changed signal
    cutCoordsChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) aspect locked toggled signal
    aspectLockedToggled = QtCore.pyqtSignal(bool)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) mouse position changed signal
    mousePositionChanged = QtCore.pyqtSignal(QtCore.QString)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) angle chenter changed signal
    angleCenterChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        _pg.GraphicsLayoutWidget.__init__(self, parent)
        self.__layout = self.ci

        #: (:class:`lavuelib.displayParameters.AxesParameters`)
        #:            axes parameters
        self.__axes = displayParameters.AxesParameters()
        #: (:class:`lavuelib.displayParameters.ROIsParameters`)
        #:                rois parameters
        self.__rois = displayParameters.ROIsParameters()
        #: (:class:`lavuelib.displayParameters.CutsParameters`)
        #:                 cuts parameters
        self.__cuts = displayParameters.CutsParameters()
        #: (:class:`lavuelib.displayParameters.GeometryParameters`)
        #:         geometry parameters
        self.__geometry = displayParameters.GeometryParameters()
        #: (:class:`lavuelib.displayParameters.IntensityParameters`)
        #:                  intensity parameters
        self.__intensity = displayParameters.IntensityParameters()

        self.__data = None
        self.__rawdata = None

        self.__image = _pg.ImageItem()

        self.__viewbox = self.__layout.addViewBox(row=0, col=1)
        self.__crosshairlocked = False
        self.__viewbox.addItem(self.__image)
        self.__xdata = 0
        self.__ydata = 0
        self.__autodisplaylevels = True
        self.__displaylevels = [None, None]

        self.__currentroimapper = QtCore.QSignalMapper(self)
        self.__roiregionmapper = QtCore.QSignalMapper(self)
        self.__currentcutmapper = QtCore.QSignalMapper(self)
        self.__cutregionmapper = QtCore.QSignalMapper(self)

        self.__setaspectlocked = QtGui.QAction(
            "Set Aspect Locked", self.__viewbox.menu)
        self.__setaspectlocked.setCheckable(True)
        if _VMAJOR == '0' and int(_VMINOR) < 10 and int(_VPATCH) < 9:
            self.__viewbox.menu.axes.insert(0, self.__setaspectlocked)
        self.__viewbox.menu.addAction(self.__setaspectlocked)

        self.__viewonetoone = QtGui.QAction(
            "View 1:1 pixels", self.__viewbox.menu)
        self.__viewonetoone.triggered.connect(self.oneToOneRange)
        if _VMAJOR == '0' and int(_VMINOR) < 10 and int(_VPATCH) < 9:
            self.__viewbox.menu.axes.insert(0, self.__viewonetoone)
        self.__viewbox.menu.addAction(self.__viewonetoone)

        self.__leftaxis = _pg.AxisItem('left')
        self.__leftaxis.linkToView(self.__viewbox)
        self.__layout.addItem(self.__leftaxis, row=0, col=0)

        self.__bottomAxis = _pg.AxisItem('bottom')
        self.__bottomAxis.linkToView(self.__viewbox)
        self.__layout.addItem(self.__bottomAxis, row=1, col=1)

        self.__layout.scene().sigMouseMoved.connect(self.mouse_position)
        self.__layout.scene().sigMouseClicked.connect(self.mouse_click)

        self.__vLine = _pg.InfiniteLine(
            angle=90, movable=False, pen=(255, 0, 0))
        self.__hLine = _pg.InfiniteLine(
            angle=0, movable=False, pen=(255, 0, 0))
        self.__viewbox.addItem(self.__vLine, ignoreBounds=True)
        self.__viewbox.addItem(self.__hLine, ignoreBounds=True)

        self.__roi = []
        self.__roi.append(ROI(0, _pg.Point(50, 50)))
        self.__roi[0].addScaleHandle([1, 1], [0, 0])
        self.__roi[0].addScaleHandle([0, 0], [1, 1])
        self.__viewbox.addItem(self.__roi[0])
        self.__roi[0].hide()

        self.__cut = []
        self.__cut.append(SimpleLineROI([10, 10], [60, 10], pen='r'))
        self.__viewbox.addItem(self.__cut[0])
        self.__cut[0].hide()

        self.__setaspectlocked.triggered.connect(self.emitAspectLockedToggled)

        self.__roiregionmapper.mapped.connect(self.roiRegionChanged)
        self.__currentroimapper.mapped.connect(self.currentROIChanged)
        self.getROI().sigHoverEvent.connect(
            self.__currentroimapper.map)
        self.getROI().sigRegionChanged.connect(
            self.__roiregionmapper.map)
        self.__currentroimapper.setMapping(self.getROI(), 0)
        self.__roiregionmapper.setMapping(self.getROI(), 0)

        self.__cutregionmapper.mapped.connect(self.cutRegionChanged)
        self.__currentcutmapper.mapped.connect(self.currentCutChanged)
        self.getCut().sigHoverEvent.connect(
            self.__currentcutmapper.map)
        self.getCut().sigRegionChanged.connect(
            self.__cutregionmapper.map)
        self.__currentcutmapper.setMapping(self.getCut(), 0)
        self.__cutregionmapper.setMapping(self.getCut(), 0)

    def showLines(self, status):
        if status:
            self.__vLine.show()
            self.__hLine.show()
        else:
            self.__vLine.hide()
            self.__hLine.hide()

    def setAspectLocked(self, flag):
        """sets aspectLocked

        :param status: state to set
        :type status: :obj:`bool`
        """
        if flag != self.__setaspectlocked.isChecked():
            self.__setaspectlocked.setChecked(flag)
        self.__viewbox.setAspectLocked(flag)

    def addItem(self, item, **args):
        self.__image.additem(item)

    def addROI(self, coords=None):
        if not coords or not isinstance(coords, list) or len(coords) != 4:
            pnt = 10 * len(self.__roi)
            sz = 50
            coords = [pnt, pnt, pnt + sz, pnt + sz]
            spnt = _pg.Point(sz, sz)
        else:
            pnt = _pg.Point(coords[0], coords[1])
            spnt = _pg.Point(coords[2] - coords[0], coords[3] - coords[1])
        self.__roi.append(ROI(pnt, spnt))
        self.__roi[-1].addScaleHandle([1, 1], [0, 0])
        self.__roi[-1].addScaleHandle([0, 0], [1, 1])
        self.__viewbox.addItem(self.__roi[-1])

        self.__rois.coords.append(coords)

    def removeROI(self):
        roi = self.__roi.pop()
        roi.hide()
        self.__viewbox.removeItem(roi)
        self.__rois.coords.pop()

    def getROI(self, rid=-1):
        if self.__roi and len(self.__roi) > rid:
            return self.__roi[rid]
        else:
            return None

    def countROIs(self):
        return len(self.__roi)

    def showROIs(self, status):
        if status:
            for roi in self.__roi:
                roi.show()
        else:
            for roi in self.__roi:
                roi.hide()

    def addROICoords(self, coords):
        if coords:
            for i, crd in enumerate(self.__roi):
                if i < len(coords):
                    self.__rois.coords[i] = coords[i]
                    crd.setPos([coords[i][0], coords[i][1]])
                    crd.setSize(
                        [coords[i][2] - coords[i][0],
                         coords[i][3] - coords[i][1]])

    def addCutCoords(self, coords):
        if coords:
            for i, crd in enumerate(self.__cut):
                if i < len(coords):
                    self.__cuts.coords[i] = coords[i]
                    crd.setPos([coords[i][0], coords[i][1]])
                    crd.setSize(
                        [coords[i][2] - coords[i][0],
                         coords[i][3] - coords[i][1]])

    def addCut(self, coords=None):
        if not coords or not isinstance(coords, list) or len(coords) != 4:
            pnt = 10 * (len(self.__cut) + 1)
            sz = 50
            coords = [pnt, pnt, pnt + sz, pnt]
        self.__cut.append(SimpleLineROI(coords[:2], coords[2:], pen='r'))
        self.__viewbox.addItem(self.__cut[-1])
        self.__cuts.coords.append(coords)

    def removeCut(self):
        cut = self.__cut.pop()
        cut.hide()
        self.__viewbox.removeItem(cut)
        self.__cuts.coords.pop()

    def getCut(self, cid=-1):
        if self.__cut and len(self.__cut) > cid:
            return self.__cut[cid]
        else:
            return None

    def countCuts(self):
        return len(self.__cut)

    def showCuts(self, status):
        if status:
            for cut in self.__cut:
                cut.show()
        else:
            for cut in self.__cut:
                cut.hide()

    def oneToOneRange(self):
        ps = self.__image.pixelSize()
        currange = self.__viewbox.viewRange()
        xrg = currange[0][1] - currange[0][0]
        yrg = currange[1][1] - currange[1][0]
        if self.__axes.position is not None and \
           not self.__rois.enabled and not self.__cuts.enabled and \
           not self.__geometry.enabled:
            self.__viewbox.setRange(
                QtCore.QRectF(self.__axes.position[0], self.__axes.position[1],
                              xrg * ps[0], yrg * ps[1]),
                padding=0)
        else:
            self.__viewbox.setRange(
                QtCore.QRectF(0, 0, xrg * ps[0], yrg * ps[1]),
                padding=0)
        if self.__setaspectlocked.isChecked():
            self.__setaspectlocked.setChecked(False)
            self.__setaspectlocked.triggered.emit(False)

    def setScale(self, position=None, scale=None, update=True):
        if update:
            self.setLabels(
                self.__axes.xtext, self.__axes.ytext,
                self.__axes.xunits, self.__axes.yunits)
        if self.__axes.position == position and \
           self.__axes.scale == scale and \
           position is None and scale is None:
            return
        self.__axes.position = position
        self.__axes.scale = scale
        self.__image.resetTransform()
        if self.__axes.scale is not None and update:
            self.__image.scale(*self.__axes.scale)
        else:
            self.__image.scale(1, 1)
        if self.__axes.position is not None and update:
            self.__image.setPos(*self.__axes.position)
        else:
            self.__image.setPos(0, 0)
        if self.__rawdata is not None and update:
            self.__viewbox.autoRange()

    def resetScale(self):
        if self.__axes.scale is not None or self.__axes.position is not None:
            self.__image.resetTransform()
        if self.__axes.scale is not None:
            self.__image.scale(1, 1)
        if self.__axes.position is not None:
            self.__image.setPos(0, 0)
        if self.__axes.scale is not None or self.__axes.position is not None:
            if self.__rawdata is not None:
                self.__viewbox.autoRange()
            self.setLabels()

    def updateImage(self, img=None, rawimg=None):
        if self.__autodisplaylevels:
            self.__image.setImage(img, autoLevels=True)
        else:
            self.__image.setImage(
                img, autoLevels=False, levels=self.__displaylevels)
        self.__data = img
        self.__rawdata = rawimg
        self.mouse_position()

    @QtCore.pyqtSlot(object)
    def mouse_position(self, event=None):
        try:
            if event is not None:
                mousePoint = self.__image.mapFromScene(event)
                self.__xdata = math.floor(mousePoint.x())
                self.__ydata = math.floor(mousePoint.y())
            if not self.__rois.enabled and not self.__cuts.enabled:
                if not self.__crosshairlocked:
                    if self.__axes.scale is not None and \
                       self.__axes.position is not None:
                        self.__vLine.setPos(
                            (self.__xdata + .5) * self.__axes.scale[0]
                            + self.__axes.position[0])
                        self.__hLine.setPos(
                            (self.__ydata + .5) * self.__axes.scale[1]
                            + self.__axes.position[1])
                    else:
                        self.__vLine.setPos(self.__xdata + .5)
                        self.__hLine.setPos(self.__ydata + .5)

            if self.__rawdata is not None:
                try:
                    xf = int(math.floor(self.__xdata))
                    yf = int(math.floor(self.__ydata))
                    if xf >= 0 and yf >= 0 and xf < self.__rawdata.shape[0] \
                       and yf < self.__rawdata.shape[1]:
                        intensity = self.__rawdata[xf, yf]
                    else:
                        intensity = 0.
                except Exception:
                    intensity = 0.
            else:
                intensity = 0.
            scaling = self.__intensity.scaling \
                if not self.__intensity.statswoscaling else "linear"
            ilabel = "intensity"
            if not self.__rois.enabled:
                if self.__intensity.dobkgsubtraction:
                    ilabel = "%s(intensity-background)" % (
                        scaling if scaling != "linear" else "")
                else:
                    if scaling == "linear":
                        ilabel = "intensity"
                    else:
                        ilabel = "%s(intensity)" % scaling
            if not self.__rois.enabled and not self.__cuts.enabled and \
               not self.__geometry.enabled:
                if self.__axes.scale is not None:
                    txdata = self.__xdata * self.__axes.scale[0]
                    tydata = self.__ydata * self.__axes.scale[1]
                    if self.__axes.position is not None:
                        txdata = txdata + self.__axes.position[0]
                        tydata = tydata + self.__axes.position[1]
                    self.mousePositionChanged.emit(
                        "x = %f%s, y = %f%s, %s = %.2f" % (
                            txdata,
                            (" %s" % self.__axes.xunits)
                            if self.__axes.xunits else "",
                            tydata,
                            (" %s" % self.__axes.yunits)
                            if self.__axes.yunits else "",
                            ilabel, intensity))
                elif self.__axes.position is not None:
                    txdata = self.__xdata + self.__axes.position[0]
                    tydata = self.__ydata + self.__axes.position[1]
                    self.mousePositionChanged.emit(
                        "x = %f%s, y = %f%s, %s = %.2f" % (
                            txdata,
                            (" %s" % self.__axes.xunits)
                            if self.__axes.xunits else "",
                            tydata,
                            (" %s" % self.__axes.yunits)
                            if self.__axes.yunits else "",
                            ilabel, intensity))
                else:
                    self.mousePositionChanged.emit(
                        "x = %i, y = %i, %s = %.2f" % (
                            self.__xdata, self.__ydata, ilabel,
                            intensity))
            elif self.__rois.enabled and self.__rois.current > -1:
                if event:
                    self.mousePositionChanged.emit(
                        "%s" % self.__rois.coords[self.__rois.current])
            elif self.__cuts.enabled:
                if self.__cuts.current > -1:
                    crds = self.__cuts.coords[self.__cuts.current]
                    crds = "[[%.2f, %.2f], [%.2f, %.2f]]" % tuple(crds)
                else:
                    crds = "[[0, 0], [0, 0]]"
                self.mousePositionChanged.emit(
                    "%s, x = %i, y = %i, %s = %.2f" % (
                        crds, self.__xdata, self.__ydata, ilabel,
                        intensity))
            elif self.__geometry.enabled and self.__geometry.energy > 0 and self.__geometry.detdistance > 0:
                if self.__geometry.gspaceindex == 0:
                    thetax, thetay, thetatotal = self.pixel2theta(
                        self.__xdata, self.__ydata)
                    self.mousePositionChanged.emit(
                        "th_x = %f deg, th_y = %f deg,"
                        " th_tot = %f deg, %s = %.2f"
                        % (thetax, thetay, thetatotal, ilabel, intensity))
                else:
                    qx, qz, q = self.pixel2q(self.__xdata, self.__ydata)
                    self.mousePositionChanged.emit(
                        u"q_x = %f 1/\u212B, q_z = %f 1/\u212B, "
                        u"q = %f 1/\u212B, %s = %.2f"
                        % (qx, qz, q, ilabel, intensity))

            else:
                self.mousePositionChanged.emit("")

        except Exception:
            # print("Warning: %s" % str(e))
            pass

    def pixel2theta(self, xdata, ydata):
        xcentered = xdata - self.__geometry.centerx
        ycentered = ydata - self.__geometry.centery
        thetax = math.atan(
            xcentered * self.__geometry.pixelsizex/1000.
            / self.__geometry.detdistance)
        thetay = math.atan(
            ycentered * self.__geometry.pixelsizey/1000.
            / self.__geometry.detdistance)
        r = math.sqrt((xcentered * self.__geometry.pixelsizex / 1000.) ** 2
                      + (ycentered * self.__geometry.pixelsizex / 1000.) ** 2)
        thetatotal = math.atan(r/self.__geometry.detdistance)*180/math.pi
        return thetax, thetay, thetatotal

    def pixel2q(self, xdata, ydata):
        thetax, thetay, thetatotal = self.pixel2theta(
            self.__xdata, self.__ydata)
        wavelength = 12400./self.__geometry.energy
        qx = 4 * math.pi / wavelength * math.sin(thetax/2.)
        qz = 4 * math.pi / wavelength * math.sin(thetay/2.)
        q = 4 * math.pi / wavelength * math.sin(thetatotal/2.)
        return qx, qz, q

    def setLabels(self, xtext=None, ytext=None, xunits=None, yunits=None):
        # print "set", xtext, ytext, xunits, yunits
        self.__bottomAxis.autoSIPrefix = False
        self.__leftaxis.autoSIPrefix = False
        self.__bottomAxis.setLabel(text=xtext, units=xunits)
        self.__leftaxis.setLabel(text=ytext, units=yunits)
        if xunits is None:
            self.__bottomAxis.labelUnits = ''
        if yunits is None:
            self.__leftaxis.labelUnits = ''
        if xtext is None:
            self.__bottomAxis.label.setVisible(False)
        if ytext is None:
            self.__leftaxis.label.setVisible(False)

    @QtCore.pyqtSlot(object)
    def mouse_click(self, event):

        mousePoint = self.__image.mapFromScene(event.scenePos())

        xdata = mousePoint.x()
        ydata = mousePoint.y()

        # if double click: fix mouse crosshair
        # another double click releases the crosshair again
        if event.double():
            if not self.__rois.enabled and not self.__cuts.enabled and not self.__geometry.enabled:
                self.__crosshairlocked = not self.__crosshairlocked
                if not self.__crosshairlocked:
                    self.__vLine.setPos(xdata + .5)
                    self.__hLine.setPos(ydata + .5)
            if self.__geometry.enabled:
                self.__crosshairlocked = False
                self.__geometry.centerx = float(xdata)
                self.__geometry.centery = float(ydata)
                self.angleCenterChanged.emit()

    def setAutoLevels(self, autolevels):
        """ sets auto levels

        :param autolevels: auto levels enabled
        :type autolevels: :obj:`bool`
        """
        if autolevels:
            self.__autodisplaylevels = True
        else:
            self.__autodisplaylevels = False

    def setDisplayMinLevel(self, level=None):
        """ sets minimum intensity level

        :param level: minimum intensity
        :type level: :obj:`float`
        """
        if level is not None:
            self.__displaylevels[0] = level

    def setDisplayMaxLevel(self, level=None):
        """ sets maximum intensity level

        :param level: maximum intensity
        :type level: :obj:`float`
        """
        if level is not None:
            self.__displaylevels[1] = level

    def setSubWidgets(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """

        if parameters.scale is False:
            doreset = not (self.__cuts.enabled or
                           self.__rois.enabled or
                           self.__geometry.enabled)

        if parameters.lines is not None:
            self.showLines(parameters.lines)
        if parameters.rois is not None:
            self.showROIs(parameters.rois)
            self.__rois.enabled = parameters.rois
        if parameters.cuts is not None:
            self.showCuts(parameters.cuts)
            self.__cuts.enabled = parameters.cuts
        if parameters.qspace is not None:
            self.__geometry.enabled = parameters.qspace

        if parameters.scale is False and doreset:
            self.resetScale()
        if parameters.scale is True:
            self.setScale(self.__axes.position, self.__axes.scale)

    def setGSpaceIndex(self, gindex):
        """ set gspace index

        :param gspace: g-space index, i.e. angle or q-space
        :type gspace: :obj:`int`
        """
        self.__geometry.gspaceindex = gindex

    def geometryMessage(self):
        return u"geometry:\n" \
            u"  center = (%s, %s) pixels\n" \
            u"  pixel_size = (%s, %s) \u00B5m\n" \
            u"  detector_distance = %s mm\n" \
            u"  energy = %s eV" % (
                self.__geometry.centerx,
                self.__geometry.centery,
                self.__geometry.pixelsizex,
                self.__geometry.pixelsizey,
                self.__geometry.detdistance,
                self.__geometry.energy
            )

    @QtCore.pyqtSlot(bool)
    def emitAspectLockedToggled(self, status):
        self.aspectLockedToggled.emit(status)

    def setTicks(self):
        """ launch axes widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        cnfdlg = axesDialog.AxesDialog(self)
        if self.__axes.position is None:
            cnfdlg.xposition = None
            cnfdlg.yposition = None
        else:
            cnfdlg.xposition = self.__axes.position[0]
            cnfdlg.yposition = self.__axes.position[1]
        if self.__axes.scale is None:
            cnfdlg.xscale = None
            cnfdlg.yscale = None
        else:
            cnfdlg.xscale = self.__axes.scale[0]
            cnfdlg.yscale = self.__axes.scale[1]

        cnfdlg.xtext = self.__axes.xtext
        cnfdlg.ytext = self.__axes.ytext

        cnfdlg.xunits = self.__axes.xunits
        cnfdlg.yunits = self.__axes.yunits

        cnfdlg.createGUI()
        if cnfdlg.exec_():
            if cnfdlg.xposition is not None and cnfdlg.yposition is not None:
                position = tuple([cnfdlg.xposition, cnfdlg.yposition])
            else:
                position = None
            if cnfdlg.xscale is not None and cnfdlg.yscale is not None:
                scale = tuple([cnfdlg.xscale, cnfdlg.yscale])
            else:
                scale = None
            self.__axes.xtext = cnfdlg.xtext or None
            self.__axes.ytext = cnfdlg.ytext or None

            self.__axes.xunits = cnfdlg.xunits or None
            self.__axes.yunits = cnfdlg.yunits or None
            self.setScale(position, scale)
            self.updateImage(self.__data, self.__rawdata)
            return True
        return False

    def setGeometry(self):
        """ launches geometry widget
        """
        cnfdlg = geometryDialog.GeometryDialog(self)
        cnfdlg.centerx = self.__geometry.centerx
        cnfdlg.centery = self.__geometry.centery
        cnfdlg.energy = self.__geometry.energy
        cnfdlg.pixelsizex = self.__geometry.pixelsizex
        cnfdlg.pixelsizey = self.__geometry.pixelsizey
        cnfdlg.detdistance = self.__geometry.detdistance
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__geometry.centerx = cnfdlg.centerx
            self.__geometry.centery = cnfdlg.centery
            self.__geometry.energy = cnfdlg.energy
            self.__geometry.pixelsizex = cnfdlg.pixelsizex
            self.__geometry.pixelsizey = cnfdlg.pixelsizey
            self.__geometry.detdistance = cnfdlg.detdistance
            return True
        return False

    def calcROIsum(self):
        if self.__rois.enabled and self.getROI() is not None:
            rid = self.__rois.current
            if rid >= 0:
                image = self.__rawdata
                if image is not None:
                    if self.__rois.enabled:
                        if rid >= 0:
                            roicoords = self.__rois.coords
                            rcrds = list(roicoords[rid])
                            for i in [0, 2]:
                                if rcrds[i] > image.shape[0]:
                                    rcrds[i] = image.shape[0]
                                elif rcrds[i] < -i / 2:
                                    rcrds[i] = -i / 2
                            for i in [1, 3]:
                                if rcrds[i] > image.shape[1]:
                                    rcrds[i] = image.shape[1]
                                elif rcrds[i] < - (i - 1) / 2:
                                    rcrds[i] = - (i - 1) / 2
                            roival = np.sum(image[
                                int(rcrds[0]):(int(rcrds[2]) + 1),
                                int(rcrds[1]):(int(rcrds[3]) + 1)
                            ])
                        else:
                            roival = 0.
                    else:
                        roival = 0.
                    return str("%.4f" % roival), rid
                else:
                    return "0.", rid
        return "", None

    def cutData(self):
        cid = self.__cuts.current
        if cid > -1 and self.countCuts() > cid:
            cut = self.getCut(cid)
            if self.__rawdata is not None:
                dt = cut.getArrayRegion(
                    self.__rawdata,
                    self.__image, axes=(0, 1))
                while dt.ndim > 1:
                    dt = dt.mean(axis=1)
                return dt
        return None

    @QtCore.pyqtSlot(int)
    def roiRegionChanged(self, _=None):
        try:
            rid = self.__rois.current
            state = self.getROI(rid).state
            ptx = int(math.floor(state['pos'].x()))
            pty = int(math.floor(state['pos'].y()))
            szx = int(math.floor(state['size'].x()))
            szy = int(math.floor(state['size'].y()))
            self.__rois.coords[rid] = [
                ptx, pty, ptx + szx, pty + szy]
            self.roiCoordsChanged.emit()
        except Exception as e:
            print("Warning: %s" % str(e))

    @QtCore.pyqtSlot(int)
    def currentROIChanged(self, rid):
        oldrid = self.__rois.current
        if rid != oldrid:
            self.__rois.current = rid
            self.roiCoordsChanged.emit()

    @QtCore.pyqtSlot(int)
    def cutRegionChanged(self, _=None):
        try:
            cid = self.__cuts.current
            self.__cuts.coords[cid] = \
                self.getCut(cid).getCoordinates()
            self.cutCoordsChanged.emit()
        except Exception as e:
            print("Warning: %s" % str(e))

    @QtCore.pyqtSlot(int)
    def currentCutChanged(self, cid):
        oldcid = self.__cuts.current
        if cid != oldcid:
            self.__cuts.current = cid
            self.cutCoordsChanged.emit()

    def updateROIs(self, rid, coords):
        """ update ROIs

        :param rid: roi id
        :type rid: :obj:`int`
        :param coords: roi coordinates
        :type coords: :obj:`list` < [float, float, float, float] >
        """
        self.addROICoords(coords)
        while rid > self.countROIs():
            if coords and len(coords) >= self.countROIs():
                self.addROI(
                    coords[self.countROIs()])
            else:
                self.addROI()
            self.getROI().sigHoverEvent.connect(
                self.__currentroimapper.map)
            self.getROI().sigRegionChanged.connect(
                self.__roiregionmapper.map)
            self.__currentroimapper.setMapping(
                self.getROI(),
                self.countROIs() - 1)
            self.__roiregionmapper.setMapping(
                self.getROI(),
                self.countROIs() - 1)
        if rid <= 0:
            self.__rois.current = -1
        elif self.__rois.current >= rid:
            self.__rois.current = 0
        while self.getROI(max(rid, 0)) is not None:
            self.__currentroimapper.removeMappings(
                self.getROI())
            self.__roiregionmapper.removeMappings(
                self.getROI())
            self.removeROI()

    def updateCuts(self, cid, coords):
        self.addCutCoords(coords)
        while cid > self.countCuts():
            if coords and len(coords) >= self.countCuts():
                self.addCut(
                    coords[self.countCuts()])
            else:
                self.addCut()
            self.getCut().sigHoverEvent.connect(
                self.__currentcutmapper.map)
            self.getCut().sigRegionChanged.connect(
                self.__cutregionmapper.map)
            self.__currentcutmapper.setMapping(
                self.getCut(),
                self.countCuts() - 1)
            self.__cutregionmapper.setMapping(
                self.getCut(),
                self.countCuts() - 1)
        if cid <= 0:
            self.__cuts.current = -1
        elif self.__cuts.current >= cid:
            self.__cuts.current = 0
        while max(cid, 0) < self.countCuts():
            self.__currentcutmapper.removeMappings(
                self.getCut())
            self.__cutregionmapper.removeMappings(
                self.getCut())
            self.removeCut()

    def updateMetaData(self, axisscales=None, axislabels=None):
        """ update Metadata informations

        :param axisscales: [xstart, ystart, xscale, yscale]
        :type axisscales: [float, float, float, float]
        :param axislabels: [xtext, ytext, xunits, yunits]
        :type axislabels: [float, float, float, float]
        """
        if axislabels is not None:
            self.__axes.xtext = str(axislabels[0]) \
                if axislabels[0] is not None else None
            self.__axes.ytext = str(axislabels[1]) \
                if axislabels[0] is not None else None
            self.__axes.xunits = str(axislabels[2]) \
                if axislabels[0] is not None else None
            self.__axes.yunits = str(axislabels[3]) \
                if axislabels[0] is not None else None
        position = None
        scale = None
        if axisscales is not None:
            try:
                position = (float(axisscales[0]), float(axisscales[1]))
            except:
                position = None
            try:
                scale = (float(axisscales[2]), float(axisscales[3]))
            except:
                scale = None
        self.setScale(position, scale,
                      not self.__rois.enabled
                      and not self.__cuts.enabled
                      and not self.__geometry.enabled)

    def setStatsWOScaling(self, status):
        """ sets statistics without scaling flag

        :param status: statistics without scaling flag
        :type status: :obj:`bool`
        """
        if self.__intensity.statswoscaling != status:
            self.__intensity.statswoscaling = status
            return True
        return False

    def setScalingType(self, scalingtype):
        """ sets intensity scaling types

        :param scalingtype: intensity scaling type
        :type scalingtype: :obj:`str`
        """
        self.__intensity.scaling = scalingtype

    def setDoBkgSubtraction(self, state):
        """ sets do background subtraction flag

        :param status: do background subtraction flag
        :type status: :obj:`bool`
        """
        self.__intensity.dobkgsubtraction = state

    def isCutsEnabled(self):
        return self.__cuts.enabled

    def isROIsEnabled(self):
        return self.__rois.enabled

    def roiCoords(self):
        return self.__rois.coords

    def image(self):
        """ provides imageItem object

        :returns: image object
        :rtype: :class:`pyqtgraph.imageItem.ImageItem`
        """
        return self.__image
