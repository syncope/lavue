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
from pyqtgraph.graphicsItems.ROI import ROI, LineROI, Handle
from PyQt4 import QtCore, QtGui

from . import axesDialog
from . import displayParameters

_VMAJOR, _VMINOR, _VPATCH = _pg.__version__.split(".") \
    if _pg.__version__ else ("0", "9", "0")


class HandleWithSignals(Handle):
    """ handle with signals

    """
    #: (:class:`PyQt4.QtCore.pyqtSignal`) hover event emitted
    hovered = QtCore.pyqtSignal()

    def __init__(self, pos, center, parent):
        """ constructor

        :param pos: position of handle
        :type pos: [float, float]
        :param pos: center of handle
        :type pos: [float, float]
        :param parent: roi object
        :type parent: :class:`pyqtgraph.graphicsItems.ROI.ROI`
        """
        pos = _pg.Point(pos)
        center = _pg.Point(center)
        if pos[0] != center[0] and pos[1] != center[1]:
            raise Exception(
                "Scale/rotate handles must have either the same x or y "
                "coordinate as their center point.")
        Handle.__init__(self, parent.handleSize, typ='sr',
                        pen=parent.handlePen, parent=parent)
        self.setPos(pos * parent.state['size'])

    def hoverEvent(self, ev):
        """ hover event

        :param ev: close event
        :type ev: :class:`PyQt4.QtCore.QEvent`:
        """
        Handle.hoverEvent(self, ev)
        self.hovered.emit()


class SimpleLineROI(LineROI):
    """ simple line roi """

    def __init__(self, pos1, pos2, width=0.00001, **args):
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

        ROI.__init__(self, pos1, size=_pg.Point(l, width), angle=ang, **args)
        h1pos = [0, 0.0]
        h1center = [1, 0.0]
        h2pos = [1, 0.0]
        h2center = [0, 0.0]
        vpos = [0.5, 1]
        vcenter = [0.5, 0]
        self.handle1 = HandleWithSignals(h1pos, h1center, self)
        self.handle2 = HandleWithSignals(h2pos, h2center, self)
        self.vhandle = HandleWithSignals(vcenter, vpos, self)
        self.addHandle(
            {'name': 'handle1', 'type': 'sr', 'center': h1center,
             'pos': h1pos, 'item': self.handle1})
        self.addHandle(
            {'name': 'handle2', 'type': 'sr', 'center': h2center,
             'pos': h2pos, 'item': self.handle2})
        self.addHandle(
            {'name': 'vhandle', 'type': 'sr', 'center': vcenter,
             'pos': vpos, 'item': self.vhandle})
        # self.handle1 = self.addScaleRotateHandle([0, 0.5], [1, 0.5])
        # self.handle2 = self.addScaleRotateHandle([1, 0.5], [0, 0.5])

    def getCoordinates(self):
        """ provides the roi coordinates

        :returns: x1, y1, x2, y2 positions of the roi
        :rtype: [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`]
        """
        ang = self.state['angle']
        pos1 = self.state['pos']
        size = self.state['size']
        ra = ang * np.pi / 180.
        pos2 = pos1 + _pg.Point(
            size.x() * math.cos(ra),
            size.x() * math.sin(ra))
        return [pos1.x(), pos1.y(), pos2.x(), pos2.y(), size.y()]


class ImageDisplayWidget(_pg.GraphicsLayoutWidget):

    #: (:class:`PyQt4.QtCore.pyqtSignal`) roi coordinate changed signal
    roiCoordsChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) cut coordinate changed signal
    cutCoordsChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) aspect locked toggled signal
    aspectLockedToggled = QtCore.pyqtSignal(bool)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) mouse position changed signal
    mouseImagePositionChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) mouse double clicked
    mouseImageDoubleClicked = QtCore.pyqtSignal(float, float)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) mouse single clicked
    mouseImageSingleClicked = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        _pg.GraphicsLayoutWidget.__init__(self, parent)
        #: (:class:`PyQt4.QtGui.QLayout`) the main layout
        self.__layout = self.ci

        #: (:class:`lavuelib.displayParameters.AxesParameters`)
        #:            axes parameters
        self.__lines = displayParameters.CrossLinesParameters()
        #: (:class:`lavuelib.displayParameters.AxesParameters`)
        #:            axes parameters
        self.__axes = displayParameters.AxesParameters()
        #: (:class:`lavuelib.displayParameters.ROIsParameters`)
        #:                rois parameters
        self.__rois = displayParameters.ROIsParameters()
        #: (:class:`lavuelib.displayParameters.CutsParameters`)
        #:                 cuts parameters
        self.__cuts = displayParameters.CutsParameters()
        #: (:class:`lavuelib.displayParameters.IntensityParameters`)
        #:                  intensity parameters
        self.__intensity = displayParameters.IntensityParameters()

        #: (:class:`numpy.ndarray`) data to displayed in 2d widget
        self.__data = None
        #: (:class:`numpy.ndarray`) raw data to cut plots
        self.__rawdata = None

        #: (:class:`pyqtgraph.ImageItem`) image item
        self.__image = _pg.ImageItem()

        #: (:class:`pyqtgraph.ViewBox`) viewbox item
        self.__viewbox = self.__layout.addViewBox(row=0, col=1)
        #: (:obj:`bool`) crooshair locked flag
        self.__crosshairlocked = False
        #: ([:obj:`float`, :obj:`float`]) center coordinates
        self.__centercoordinates = None
        #: ([:obj:`float`, :obj:`float`]) position mark coordinates
        self.__markcoordinates = None

        self.__viewbox.addItem(self.__image)
        #: (:obj:`float`) current floar x-position
        self.__xfdata = 0
        #: (:obj:`float`) current floar y-position
        self.__yfdata = 0
        #: (:obj:`float`) current x-position
        self.__xdata = 0
        #: (:obj:`float`) current y-position
        self.__ydata = 0
        #: (:obj:`bool`) auto display level flag
        self.__autodisplaylevels = True
        #: (:obj:`bool`) auto down sample
        self.__autodownsample = True
        #: ([:obj:`float`, :obj:`float`]) minimum and maximum intensity levels
        self.__displaylevels = [None, None]

        #: (:class:`PyQt4.QtCore.QSignalMapper`) current roi mapper
        self.__currentroimapper = QtCore.QSignalMapper(self)
        #: (:class:`PyQt4.QtCore.QSignalMapper`) roi region mapper
        self.__roiregionmapper = QtCore.QSignalMapper(self)
        #: (:class:`PyQt4.QtCore.QSignalMapper`) current cut mapper
        self.__currentcutmapper = QtCore.QSignalMapper(self)
        #: (:class:`PyQt4.QtCore.QSignalMapper`) cut region mapper
        self.__cutregionmapper = QtCore.QSignalMapper(self)

        #: (:class:`PyQt4.QtGui.QAction`) set aspect ration locked action
        self.__setaspectlocked = QtGui.QAction(
            "Set Aspect Locked", self.__viewbox.menu)
        self.__setaspectlocked.setCheckable(True)
        if _VMAJOR == '0' and int(_VMINOR) < 10 and int(_VPATCH) < 9:
            self.__viewbox.menu.axes.insert(0, self.__setaspectlocked)
        self.__viewbox.menu.addAction(self.__setaspectlocked)

        #: (:class:`PyQt4.QtGui.QAction`) view one to one pixel action
        self.__viewonetoone = QtGui.QAction(
            "View 1:1 pixels", self.__viewbox.menu)
        self.__viewonetoone.triggered.connect(self._oneToOneRange)
        if _VMAJOR == '0' and int(_VMINOR) < 10 and int(_VPATCH) < 9:
            self.__viewbox.menu.axes.insert(0, self.__viewonetoone)
        self.__viewbox.menu.addAction(self.__viewonetoone)

        #: (:class:`pyqtgraph.AxisItem`) left axis
        self.__leftaxis = _pg.AxisItem('left')
        self.__leftaxis.linkToView(self.__viewbox)
        self.__layout.addItem(self.__leftaxis, row=0, col=0)

        #: (:class:`pyqtgraph.AxisItem`) bottom axis
        self.__bottomAxis = _pg.AxisItem('bottom')
        self.__bottomAxis.linkToView(self.__viewbox)
        self.__layout.addItem(self.__bottomAxis, row=1, col=1)

        self.__layout.scene().sigMouseMoved.connect(self.mouse_position)
        self.__layout.scene().sigMouseClicked.connect(self.mouse_click)

        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                 vertical locker line of the mouse position
        self.__lockerVLine = _pg.InfiniteLine(
            angle=90, movable=False, pen=(255, 0, 0))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                   horizontal locker line of the mouse position
        self.__lockerHLine = _pg.InfiniteLine(
            angle=0, movable=False, pen=(255, 0, 0))
        self.__viewbox.addItem(self.__lockerVLine, ignoreBounds=True)
        self.__viewbox.addItem(self.__lockerHLine, ignoreBounds=True)

        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                 vertical center line of the mouse position
        self.__centerVLine = _pg.InfiniteLine(
            angle=90, movable=False, pen=(255, 255, 0))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                   horizontal center line of the mouse position
        self.__centerHLine = _pg.InfiniteLine(
            angle=0, movable=False, pen=(255, 255, 0))
        self.__viewbox.addItem(self.__centerVLine, ignoreBounds=True)
        self.__viewbox.addItem(self.__centerHLine, ignoreBounds=True)

        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                 vertical mark line of the mouse position
        self.__markVLine = _pg.InfiniteLine(
            angle=90, movable=False, pen=(0, 0, 255))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                   horizontal mark line of the mouse position
        self.__markHLine = _pg.InfiniteLine(
            angle=0, movable=False, pen=(0, 0, 255))
        self.__viewbox.addItem(self.__markVLine, ignoreBounds=True)
        self.__viewbox.addItem(self.__markHLine, ignoreBounds=True)

        #: (:obj:`list` <:class:`pyqtgraph.graphicsItems.ROI`>)
        #:            list of roi widgets
        self.__roi = []
        self.__roi.append(ROI(0, _pg.Point(50, 50)))
        self.__roi[0].addScaleHandle([1, 1], [0, 0])
        self.__roi[0].addScaleHandle([0, 0], [1, 1])
        self.__viewbox.addItem(self.__roi[0])
        self.__roi[0].hide()

        #: (:obj:`list` <:class:`pyqtgraph.graphicsItems.ROI`>)
        #:        list of cut widgets
        self.__cut = []
        self.__cut.append(SimpleLineROI([10, 10], [60, 10], pen='r'))
        self.__viewbox.addItem(self.__cut[0])
        self.__cut[0].hide()

        self.__setaspectlocked.triggered.connect(self.emitAspectLockedToggled)

        self.__roiregionmapper.mapped.connect(self.changeROIRegion)
        self.__currentroimapper.mapped.connect(self._emitROICoordsChanged)
        self._getROI().sigHoverEvent.connect(
            self.__currentroimapper.map)
        self._getROI().sigRegionChanged.connect(
            self.__roiregionmapper.map)
        self.__currentroimapper.setMapping(self._getROI(), 0)
        self.__roiregionmapper.setMapping(self._getROI(), 0)

        self.__cutregionmapper.mapped.connect(self.changeCutRegion)
        self.__currentcutmapper.mapped.connect(self._emitCutCoordsChanged)
        self._getCut().sigHoverEvent.connect(
            self.__currentcutmapper.map)
        self._getCut().sigRegionChanged.connect(
            self.__cutregionmapper.map)
        self._getCut().handle1.hovered.connect(
            self.__currentcutmapper.map)
        self._getCut().handle2.hovered.connect(
            self.__currentcutmapper.map)
        self._getCut().vhandle.hovered.connect(
            self.__currentcutmapper.map)
        self.__currentcutmapper.setMapping(self._getCut().handle1, 0)
        self.__currentcutmapper.setMapping(self._getCut().handle2, 0)
        self.__currentcutmapper.setMapping(self._getCut().vhandle, 0)
        self.__currentcutmapper.setMapping(self._getCut(), 0)
        self.__cutregionmapper.setMapping(self._getCut(), 0)

    def __showLockerLines(self, status):
        """ shows or hides HV locker mouse lines

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            self.__lockerVLine.show()
            self.__lockerHLine.show()
        else:
            self.__lockerVLine.hide()
            self.__lockerHLine.hide()

    def __showCenterLines(self, status):
        """ shows or hides HV center mouse lines

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            self.__centerVLine.show()
            self.__centerHLine.show()
        else:
            self.__centerVLine.hide()
            self.__centerHLine.hide()

    def __showMarkLines(self, status):
        """ shows or hides HV mark mouse lines

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            self.__markVLine.show()
            self.__markHLine.show()
        else:
            self.__markVLine.hide()
            self.__markHLine.hide()

    def setAspectLocked(self, flag):
        """sets aspectLocked

        :param status: state to set
        :type status: :obj:`bool`
        """
        if flag != self.__setaspectlocked.isChecked():
            self.__setaspectlocked.setChecked(flag)
        self.__viewbox.setAspectLocked(flag)

    def __addROI(self, coords=None):
        """ adds ROIs

        :param coords: roi coordinates
        :type coords: :obj:`list`
                 < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
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

    def __removeROI(self):
        """ removes the last roi
        """
        roi = self.__roi.pop()
        roi.hide()
        self.__viewbox.removeItem(roi)
        self.__rois.coords.pop()

    def _getROI(self, rid=-1):
        """ get the given or the last ROI

        :param rid: roi id
        :type rid: :obj:`int`
        """
        if self.__roi and len(self.__roi) > rid:
            return self.__roi[rid]
        else:
            return None

    def __showROIs(self, status):
        """ shows or hides rois

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            for roi in self.__roi:
                roi.show()
        else:
            for roi in self.__roi:
                roi.hide()

    def __addROICoords(self, coords):
        """ adds ROI coorinates

        :param coords: roi coordinates
        :type coords: :obj:`list`
                < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if coords:
            for i, crd in enumerate(self.__roi):
                if i < len(coords):
                    self.__rois.coords[i] = coords[i]
                    crd.setPos([coords[i][0], coords[i][1]])
                    crd.setSize(
                        [coords[i][2] - coords[i][0],
                         coords[i][3] - coords[i][1]])

    def __addCutCoords(self, coords):
        """ adds Cut coorinates

        :param coords: cut coordinates
        :type coords: :obj:`list`
                  < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if coords:
            for i, crd in enumerate(self.__cut):
                if i < len(coords):
                    self.__cuts.coords[i] = coords[i]
                    crd.setPos([coords[i][0], coords[i][1]])
                    crd.setSize(
                        [coords[i][2] - coords[i][0],
                         coords[i][3] - coords[i][1]])

    def __addCut(self, coords=None):
        """ adds Cuts

        :param coords: cut coordinates
        :type coords: :obj:`list`
                  < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if not coords or not isinstance(coords, list) or len(coords) != 5:
            pnt = 10 * (len(self.__cut) + 1)
            sz = 50
            coords = [pnt, pnt, pnt + sz, pnt, 0.00001]
        self.__cut.append(SimpleLineROI(
            coords[:2], coords[2:4], width=coords[4], pen='r'))
        self.__viewbox.addItem(self.__cut[-1])
        self.__cuts.coords.append(coords)

    def __removeCut(self):
        """ removes the last cut
        """
        cut = self.__cut.pop()
        cut.hide()
        self.__viewbox.removeItem(cut)
        self.__cuts.coords.pop()

    def _getCut(self, cid=-1):
        """ get the given or the last Cut

        :param cid: roi id
        :type cid: :obj:`int`
        """
        if self.__cut and len(self.__cut) > cid:
            return self.__cut[cid]
        else:
            return None

    def __showCuts(self, status):
        """ shows or hides cuts

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            for cut in self.__cut:
                cut.show()
        else:
            for cut in self.__cut:
                cut.hide()

    def _oneToOneRange(self):
        """ set one to one range
        """
        ps = self.__image.pixelSize()
        currange = self.__viewbox.viewRange()
        xrg = currange[0][1] - currange[0][0]
        yrg = currange[1][1] - currange[1][0]
        if self.__axes.position is not None and self.__axes.enabled:
            self.__viewbox.setRange(
                QtCore.QRectF(
                    self.__axes.position[0], self.__axes.position[1],
                    xrg * ps[0], yrg * ps[1]),
                padding=0)
        else:
            self.__viewbox.setRange(
                QtCore.QRectF(0, 0, xrg * ps[0], yrg * ps[1]),
                padding=0)
        if self.__setaspectlocked.isChecked():
            self.__setaspectlocked.setChecked(False)
            self.__setaspectlocked.triggered.emit(False)

    def __setScale(self, position=None, scale=None, update=True):
        """ set axes scales

        :param position: start position of axes
        :type position: [:obj:`float`, :obj:`float`]
        :param scale: scale axes
        :type scale: [:obj:`float`, :obj:`float`]
        :param update: update scales on image
        :type updatescale: :obj:`bool`
        """
        if update:
            self.__setLabels(
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

    def __resetScale(self):
        """ reset axes scales
        """
        if self.__axes.scale is not None or self.__axes.position is not None:
            self.__image.resetTransform()
        if self.__axes.scale is not None:
            self.__image.scale(1, 1)
        if self.__axes.position is not None:
            self.__image.setPos(0, 0)
        if self.__axes.scale is not None or self.__axes.position is not None:
            if self.__rawdata is not None:
                self.__viewbox.autoRange()
            self.__setLabels()

    def updateImage(self, img=None, rawimg=None):
        """ updates the image to display

        :param img: 2d image array
        :type img: :class:`numpy.ndarray`
        :param rawimg: 2d raw image array
        :type rawimg: :class:`numpy.ndarray`
        """
        if self.__autodisplaylevels:
            self.__image.setImage(
                img, autoLevels=True,
                autoDownsample=self.__autodownsample)
        else:
            self.__image.setImage(
                img, autoLevels=False,
                levels=self.__displaylevels,
                autoDownsample=self.__autodownsample)
        self.__data = img
        self.__rawdata = rawimg
        self.mouse_position()

    def __setLockerLines(self):
        """  sets vLine and hLine positions
        """
        if self.__axes.scale is not None and \
           self.__axes.enabled is True:
            position = [0, 0] \
                if self.__axes.position is None \
                else self.__axes.position

            self.__lockerVLine.setPos(
                (self.__xfdata + .5) * self.__axes.scale[0]
                + position[0])
            self.__lockerHLine.setPos(
                (self.__yfdata + .5) * self.__axes.scale[1]
                + position[1])
        else:
            self.__lockerVLine.setPos(self.__xfdata + .5)
            self.__lockerHLine.setPos(self.__yfdata + .5)

    def __setCenterLines(self):
        """  sets vLine and hLine positions
        """
        self.__centerVLine.setPos(self.__xdata)
        self.__centerHLine.setPos(self.__ydata)

    def __setMarkLines(self):
        """  sets vLine and hLine positions
        """
        self.__markVLine.setPos(self.__xdata)
        self.__markHLine.setPos(self.__ydata)

    def currentIntensity(self):
        """ provides intensity for current mouse position

        :returns: x position, y position, pixel intensity
        :rtype: (`obj`:float:, `obj`:float:, `obj`:float:)
        """
        if self.__rawdata is not None:
            try:
                xf = int(math.floor(self.__xfdata))
                yf = int(math.floor(self.__yfdata))
                if xf >= 0 and yf >= 0 and xf < self.__rawdata.shape[0] \
                   and yf < self.__rawdata.shape[1]:
                    intensity = self.__rawdata[xf, yf]
                else:
                    intensity = 0.
            except Exception:
                intensity = 0.
        else:
            intensity = 0.
        return self.__xfdata, self.__yfdata, intensity, self.__xdata, self.__ydata

    def scalingLabel(self):
        """ provides scaling label

        :returns:  scaling label
        :rtype: `obj`:str:
        """
        ilabel = "intensity"
        scaling = self.__intensity.scaling \
            if not self.__intensity.statswoscaling else "linear"
        if not self.__rois.enabled:
            if self.__intensity.dobkgsubtraction:
                ilabel = "%s(intensity-background)" % (
                    scaling if scaling != "linear" else "")
            else:
                if scaling == "linear":
                    ilabel = "intensity"
                else:
                    ilabel = "%s(intensity)" % scaling
        return ilabel

    def axesunits(self):
        """ return axes units
        :returns: x,y units
        :rtype: (:obj:`str`, :obj:`str`)
        """
        return (self.__axes.xunits, self.__axes.yunits)

    def scaledxy(self, x, y):
        """ provides scaled x,y positions

        :param x: x pixel coordinate
        :type x: :obj:`float`
        :param y: y pixel coordinate
        :type y: :obj:`float`
        :returns: scaled x,y position
        :rtype: (:obj:`float`, :obj:`float`)
        """
        txdata = None
        tydata = None
        if self.__axes.scale is not None:
            txdata = x * self.__axes.scale[0]
            tydata = y * self.__axes.scale[1]
            if self.__axes.position is not None:
                txdata = txdata + self.__axes.position[0]
                tydata = tydata + self.__axes.position[1]
        elif self.__axes.position is not None:
            txdata = x + self.__axes.position[0]
            tydata = y + self.__axes.position[1]
        return (txdata, tydata)

    @QtCore.pyqtSlot(object)
    def mouse_position(self, event=None):
        """ updates image widget after mouse position change

        :param event: mouse move event
        :type event: :class:`PyQt4.QtCore.QEvent`
        """
        try:
            if event is not None:
                mousePoint = self.__image.mapFromScene(event)
                self.__xdata = mousePoint.x()
                self.__ydata = mousePoint.y()
                self.__xfdata = math.floor(self.__xdata)
                self.__yfdata = math.floor(self.__ydata)
            if self.__lines.locker:
                if not self.__crosshairlocked:
                    self.__setLockerLines()
            if self.__lines.center:
                if not self.__centercoordinates:
                    self.__setCenterLines()
            if self.__lines.positionmark:
                if not self.__markcoordinates:
                    self.__setMarkLines()
            self.mouseImagePositionChanged.emit()
        except Exception:
            # print("Warning: %s" % str(e))
            pass

    def __setLabels(self, xtext=None, ytext=None, xunits=None, yunits=None):
        """ sets labels and units

        :param xtext: x-label text
        :param type: :obj:`str`
        :param ytext: y-label text
        :param type: :obj:`str`
        :param xunits: x-units text
        :param type: :obj:`str`
        :param yunits: y-units text
        :param type: :obj:`str`
        """
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
        """ updates image widget after mouse click

        :param event: mouse click event
        :type event: :class:`PyQt4.QtCore.QEvent`
        """

        mousePoint = self.__image.mapFromScene(event.scenePos())

        xdata = mousePoint.x()
        ydata = mousePoint.y()

        # if double click: fix mouse crosshair
        # another double click releases the crosshair again
        if event.double():
            if self.__lines.locker:
                self.__crosshairlocked = not self.__crosshairlocked
                if not self.__crosshairlocked:
                    self.__lockerVLine.setPos(xdata + .5)
                    self.__lockerHLine.setPos(ydata + .5)
            if self.__lines.center:
                self.updateCenter(xdata, ydata)
            if self.__lines.positionmark:
                self.updatePositionMark(xdata, ydata)
            self.mouseImageDoubleClicked.emit(xdata, ydata)
        else:
            self.mouseImageSingleClicked.emit(xdata, ydata)

    def setAutoLevels(self, autolevels):
        """ sets auto levels

        :param autolevels: auto levels enabled
        :type autolevels: :obj:`bool`
        """
        if autolevels:
            self.__autodisplaylevels = True
        else:
            self.__autodisplaylevels = False

    def setAutoDownSample(self, autodownsample):
        """ sets auto levels

        :param autolevels: auto down sample enabled
        :type autolevels: :obj:`bool`
        """
        if autodownsample:
            self.__autodownsample = True
        else:
            self.__autodownsample = False

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

        doreset = False
        if parameters.scale is not None:
            if parameters.scale is False:
                doreset = self.__axes.enabled
            self.__axes.enabled = parameters.scale

        # if parameters.lines is not None:
        if parameters.crosshairlocker is not None:
            self.__showLockerLines(parameters.crosshairlocker)
            self.__lines.locker = parameters.crosshairlocker
        if parameters.centerlines is not None:
            self.__showCenterLines(parameters.centerlines)
            self.__lines.center = parameters.centerlines
        if parameters.marklines is not None:
            self.__showMarkLines(parameters.marklines)
            self.__lines.positionmark = parameters.marklines
        if parameters.rois is not None:
            self.__showROIs(parameters.rois)
            self.__rois.enabled = parameters.rois
        if parameters.cuts is not None:
            self.__showCuts(parameters.cuts)
            self.__cuts.enabled = parameters.cuts
        if doreset:
            self.__resetScale()
        if parameters.scale is True:
            self.__setScale(self.__axes.position, self.__axes.scale)

    @QtCore.pyqtSlot(bool)
    def emitAspectLockedToggled(self, status):
        """ emits aspectLockedToggled

        :param status: aspectLockedToggled status
        :type status: :obj:`bool`
        """
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
            self.__setScale(position, scale)
            self.updateImage(self.__data, self.__rawdata)
            return True
        return False

    def calcROIsum(self):
        """ calculates the current roi sum

        :returns: sum roi value, roi id
        :rtype: (:obj:`str`, :obj:`int`)
        """
        if self.__rois.enabled and self._getROI() is not None:
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
                                elif rcrds[i] < -i // 2:
                                    rcrds[i] = -i // 2
                            for i in [1, 3]:
                                if rcrds[i] > image.shape[1]:
                                    rcrds[i] = image.shape[1]
                                elif rcrds[i] < - (i - 1) // 2:
                                    rcrds[i] = - (i - 1) // 2
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
        """ provides the current cut data

        :returns: current cut data
        :rtype: :class:`numpy.ndarray`
        """
        cid = self.__cuts.current
        if cid > -1 and len(self.__cut) > cid:
            cut = self._getCut(cid)
            if self.__rawdata is not None:
                dt = cut.getArrayRegion(
                    self.__rawdata, self.__image, axes=(0, 1))
                while dt.ndim > 1:
                    dt = dt.mean(axis=1)
                return dt
        return None

    def rawData(self):
        """ provides the raw data

        :returns: current raw data
        :rtype: :class:`numpy.ndarray`
        """
        return self.__rawdata

    @QtCore.pyqtSlot(int)
    def changeROIRegion(self, _=None):
        """ changes the current roi region
        """
        try:
            rid = self.__rois.current
            roi = self._getROI(rid)
            if roi is not None:
                state = roi.state
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
    def _emitROICoordsChanged(self, rid):
        """ emits roiCoordsChanged signal

        :param rid: roi id
        :type rid: :obj:`int`
        """
        oldrid = self.__rois.current
        if rid != oldrid:
            self.__rois.current = rid
            self.roiCoordsChanged.emit()

    @QtCore.pyqtSlot(int)
    def changeCutRegion(self, _=None):
        """ changes the current roi region
        """
        try:
            cid = self.__cuts.current
            self.__cuts.coords[cid] = self._getCut(cid).getCoordinates()
            self.cutCoordsChanged.emit()
        except Exception as e:
            print("Warning: %s" % str(e))

    @QtCore.pyqtSlot(int)
    def _emitCutCoordsChanged(self, cid):
        """ emits cutCoordsChanged signal

        :param cid: cut id
        :type cid: :obj:`int`
        """
        oldcid = self.__cuts.current
        if cid != oldcid:
            self.__cuts.current = cid
            self.cutCoordsChanged.emit()

    def updateROIs(self, rid, coords):
        """ update ROIs

        :param rid: roi id
        :type rid: :obj:`int`
        :param coords: roi coordinates
        :type coords: :obj:`list`
                 < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        self.__addROICoords(coords)
        while rid > len(self.__roi):
            if coords and len(coords) >= len(self.__roi):
                self.__addROI(coords[len(self.__roi)])
            else:
                self.__addROI()
            self._getROI().sigHoverEvent.connect(self.__currentroimapper.map)
            self._getROI().sigRegionChanged.connect(self.__roiregionmapper.map)
            self.__currentroimapper.setMapping(
                self._getROI(), len(self.__roi) - 1)
            self.__roiregionmapper.setMapping(
                self._getROI(), len(self.__roi) - 1)
        if rid <= 0:
            self.__rois.current = -1
        elif self.__rois.current >= rid:
            self.__rois.current = 0
        while self._getROI(max(rid, 0)) is not None:
            self.__currentroimapper.removeMappings(self._getROI())
            self.__roiregionmapper.removeMappings(self._getROI())
            self.__removeROI()

    def updateCuts(self, cid, coords):
        """ update Cuts

        :param rid: cut id
        :type rid: :obj:`int`
        :param coords: cut coordinates
        :type coords: :obj:`list`
                < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        self.__addCutCoords(coords)
        while cid > len(self.__cut):
            if coords and len(coords) >= len(self.__cut):
                self.__addCut(coords[len(self.__cut)])
            else:
                self.__addCut()
            self._getCut().sigHoverEvent.connect(self.__currentcutmapper.map)
            self._getCut().sigRegionChanged.connect(self.__cutregionmapper.map)
            self._getCut().handle1.hovered.connect(self.__currentcutmapper.map)
            self._getCut().handle2.hovered.connect(self.__currentcutmapper.map)
            self._getCut().vhandle.hovered.connect(self.__currentcutmapper.map)
            self.__currentcutmapper.setMapping(
                self._getCut(), len(self.__cut) - 1)
            self.__currentcutmapper.setMapping(
                self._getCut().handle1, len(self.__cut) - 1)
            self.__currentcutmapper.setMapping(
                self._getCut().handle2, len(self.__cut) - 1)
            self.__currentcutmapper.setMapping(
                self._getCut().vhandle, len(self.__cut) - 1)
            self.__cutregionmapper.setMapping(
                self._getCut(), len(self.__cut) - 1)
        if cid <= 0:
            self.__cuts.current = -1
        elif self.__cuts.current >= cid:
            self.__cuts.current = 0
        while max(cid, 0) < len(self.__cut):
            self.__currentcutmapper.removeMappings(self._getCut())
            self.__currentcutmapper.removeMappings(self._getCut().handle1)
            self.__currentcutmapper.removeMappings(self._getCut().handle2)
            self.__cutregionmapper.removeMappings(self._getCut())
            self.__removeCut()

    def updateMetaData(self, axisscales=None, axislabels=None):
        """ update Metadata informations

        :param axisscales: [xstart, ystart, xscale, yscale]
        :type axisscales:
                  [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`]
        :param axislabels: [xtext, ytext, xunits, yunits]
        :type axislabels:
                  [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`]
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
        self.__setScale(position, scale, self.__axes.enabled)

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
        """ provides flag cuts enabled

        :return: cut enabled flag
        :rtype: :obj:`bool`
        """
        return self.__cuts.enabled

    def isROIsEnabled(self):
        """ provides flag rois enabled

        :return: roi enabled flag
        :rtype: :obj:`bool`
        """
        return self.__rois.enabled

    def roiCoords(self):
        """ provides rois coordinates

        :return: rois coordinates
        :rtype: :obj:`list`
               < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        return self.__rois.coords

    def cutCoords(self):
        """ provides cuts coordinates

        :return: cuts coordinates
        :rtype: :obj:`list`
               < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        return self.__cuts.coords

    def currentROI(self):
        """ provides current roi id

        :return: roi id
        :rtype: :obj:`int`
        """
        return self.__rois.current

    def currentCut(self):
        """ provides current cut id

        :return: cut id
        :rtype: :obj:`int`
        """
        return self.__cuts.current

    def image(self):
        """ provides imageItem object

        :returns: image object
        :rtype: :class:`pyqtgraph.imageItem.ImageItem`
        """
        return self.__image

    @QtCore.pyqtSlot(float, float)
    def updateCenter(self, xdata, ydata):
        """ updates the image center

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        self.__centercoordinates = [xdata, ydata]
        self.__centerVLine.setPos(xdata)
        self.__centerHLine.setPos(ydata)

    @QtCore.pyqtSlot(float, float)
    def updatePositionMark(self, xdata, ydata):
        """ updates the position mark

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        self.__markcoordinates = [xdata, ydata]
        self.__markVLine.setPos(xdata)
        self.__markHLine.setPos(ydata)
