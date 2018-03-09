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

""" image widget """


from PyQt4 import QtCore, QtGui, uic

import pyqtgraph as _pg
import re
import os
import json

from . import imageDisplayWidget
from . import messageBox
from . import imageSource as isr
from . import toolWidget


_VMAJOR, _VMINOR, _VPATCH = _pg.__version__.split(".") \
    if _pg.__version__ else ("0", "9", "0")

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ImageWidget.ui"))


class ImageWidget(QtGui.QWidget):

    """
    The part of the GUI that incorporates the image view.
    """

    #: (:class:`PyQt4.QtCore.pyqtSignal`) current tool changed signal
    currentToolChanged = QtCore.pyqtSignal(int)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) cut number changed signal
    cutNumberChanged = QtCore.pyqtSignal(int)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) roi number changed signal
    roiNumberChanged = QtCore.pyqtSignal(int)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) roi coordinate changed signal
    roiCoordsChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) cut coordinate changed signal
    cutCoordsChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) roi Line Edit changed signal
    roiLineEditChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) sardana enabled signal
    sardanaEnabled = QtCore.pyqtSignal(bool)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) aspect locked toggled signal
    aspectLockedToggled = QtCore.pyqtSignal(bool)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) apply tips changed signal
    applyTipsChanged = QtCore.pyqtSignal(int)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) roi aliases changed signal
    roiAliasesChanged = QtCore.pyqtSignal(str)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) roi value changed signal
    roiValueChanged = QtCore.pyqtSignal(str, int, str)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) mouse image position changed signal
    mouseImagePositionChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) mouse double clicked
    mouseImageDoubleClicked = QtCore.pyqtSignal(float, float)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) mouse single clicked
    mouseImageSingleClicked = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None, tooltypes=None, settings=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        :param tooltypes: tool class names
        :type tooltypes: :obj:`list` <:obj:`str`>
        :param settings: lavue configuration settings
        :type settings: :class:`lavuelib.settings.Settings`
        """
        QtGui.QWidget.__init__(self, parent)

        #: (:obj:`list` < :obj:`str` > ) tool class names
        self.__tooltypes = tooltypes or []

        #: (:obj:`list` < :obj:`str` > ) tool names
        self.__toolnames = []
        #: (:obj:`dict` < :obj:`str`,
        #:      :class:`lavuelib.toolWidget.BaseToolWidget` >)
        #:           tool names
        self.__toolwidgets = {}
        #: (:class:`lavuelib.settings.Settings`) settings
        self.__settings = settings
        #: (obj`str`) last text
        self.__lasttext = ""
        #: (:class:`lavuelib.toolWidget.BaseToolWidget`) current tool
        self.__currenttool = None

        #: (:class:`Ui_ImageWidget') ui_imagewidget object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:class:`lavuelib.imageDisplayWidget.ImageDisplayWidget`)
        #:     2D image display widget
        self.__displaywidget = imageDisplayWidget.ImageDisplayWidget(
            parent=self)

        #: (:class:`pyqtgraph.PlotWidget`) 1D plot widget
        self.__cutPlot = _pg.PlotWidget(self)
        #: (:class:`pyqtgraph.PlotDataItem`) 1D plot
        self.__cutCurve = self.__cutPlot.plot()

        self.__ui.twoDVerticalLayout.addWidget(self.__displaywidget)
        self.__ui.oneDVerticalLayout.addWidget(self.__cutPlot)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,
                                       QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(15)
        sizePolicy.setHeightForWidth(
            self.__displaywidget.sizePolicy().hasHeightForWidth())
        self.__displaywidget.setSizePolicy(sizePolicy)

        if _VMAJOR == '0' and int(_VMINOR) < 10 and int(_VPATCH) < 9:
            self.__cutPlot.setMinimumSize(QtCore.QSize(0, 170))

        self.__addToolWidgets()

        self.__ui.plotSplitter.setStretchFactor(0, 20)
        self.__ui.plotSplitter.setStretchFactor(1, 1)
        self.__ui.toolSplitter.setStretchFactor(0, 100)
        self.__ui.toolSplitter.setStretchFactor(1, 1)

        self.cutCoordsChanged.connect(self._plotCut)
        self.__displaywidget.cutCoordsChanged.connect(self._plotCut)
        self.__ui.toolComboBox.currentIndexChanged.connect(
            self.showCurrentTool)
        self.__displaywidget.aspectLockedToggled.connect(
            self.emitAspectLockedToggled)
        self.__displaywidget.mouseImagePositionChanged.connect(
            self._emitMouseImagePositionChanged)
        self.__displaywidget.mouseImageDoubleClicked.connect(
            self._emitMouseImageDoubleClicked)
        self.__displaywidget.mouseImageSingleClicked.connect(
            self._emitMouseImageSingleClicked)

        self.roiLineEditChanged.emit()

    def __addToolWidgets(self):
        """ add tool subwidgets into grid layout
        """
        for tt in self.__tooltypes:
            twg = getattr(toolWidget, tt)(self)
            self.__toolwidgets[twg.name] = twg
            self.__toolnames.append(twg.name)
            self.__ui.toolComboBox.addItem(twg.name)
            self.__ui.toolVerticalLayout.addWidget(twg)

    def __connecttool(self):
        """ connect current tool widget
        """
        if self.__currenttool:
            for signal, slot in self.__currenttool.signal2slot:
                if isinstance(signal, str):
                    signal = getattr(self, signal)
                if isinstance(slot, str):
                    slot = getattr(self, slot)
                signal.connect(slot)
            self.__currenttool.activate()

    def __disconnecttool(self):
        """ disconnect current tool widget
        """
        if self.__currenttool:
            for signal, slot in self.__currenttool.signal2slot:
                if isinstance(signal, str):
                    signal = getattr(self, signal)
                if isinstance(slot, str):
                    slot = getattr(self, slot)
                signal.connect(slot)
            self.__currenttool.disactivate()

    def updateMetaData(self, axisscales=None, axislabels=None):
        """ update Metadata informations

        :param axisscales: [xstart, ystart, xscale, yscale]
        :type axisscales:
                  [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`]
        :param axislabels: [xtext, ytext, xunits, yunits]
        :type axislabels:
                  [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`]
        """
        self.__displaywidget.updateMetaData(axisscales, axislabels)

    @QtCore.pyqtSlot(int)
    def updateROIs(self, rid, coords=None):
        """ update ROIs

        :param rid: roi id
        :type rid: :obj:`int`
        :param coords: roi coordinates
        :type coords: :obj:`list`
                  < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        self.applyTipsChanged.emit(rid)
        self.__displaywidget.updateROIs(rid, coords)
        self.roiCoordsChanged.emit()
        self.roiNumberChanged.emit(rid)

    @QtCore.pyqtSlot(int)
    def updateCuts(self, cid, coords=None):
        """ update Cuts

        :param cid: cut id
        :type cid: :obj:`int`
        :param coords: cut coordinates
        :type coords: :obj:`list`
                  < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        self.__displaywidget.updateCuts(cid, coords)
        self.cutCoordsChanged.emit()
        self.cutNumberChanged.emit(cid)

    @QtCore.pyqtSlot(int)
    def showCurrentTool(self):
        """ shows the current tool
        """
        text = self.__ui.toolComboBox.currentText()
        stwg = None
        for nm, twg in self.__toolwidgets.items():
            if text == nm:
                stwg = twg
            else:
                twg.hide()
        self.__disconnecttool()
        self.__currenttool = stwg
        if stwg is not None:
            stwg.show()
            self.__displaywidget.setSubWidgets(stwg.parameters)
            self.__updateinfowidgets(stwg.parameters)

        self.__connecttool()
        self.currentToolChanged.emit(text)

    def __updateinfowidgets(self, parameters):
        """ update info widgets

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        if parameters.infolabel is None:
            self.__ui.infoLabel.hide()
        else:
            self.__ui.infoLabel.setText(parameters.infolabel)
            if parameters.infotips is not None:
                self.__ui.infoLabel.setToolTip(parameters.infotips)
            self.__ui.infoLabel.show()

        if parameters.infolineedit is None:
            self.__ui.infoLineEdit.hide()
        else:
            self.__ui.infoLineEdit.setText(parameters.infolineedit)
            if parameters.infotips is not None:
                self.__ui.infoLineEdit.setToolTip(parameters.infotips)
            self.__ui.infoLineEdit.show()
        if parameters.cutplot is True:
            self.__cutPlot.show()
            self.__ui.oneDWidget.show()
        elif parameters.cutplot is False:
            self.__cutPlot.hide()
            self.__ui.oneDWidget.hide()

    def plot(self, array, rawarray=None):
        """ plots the image

        :param array: 2d image array
        :type array: :class:`numpy.ndarray`
        :param rawarray: 2d raw image array
        :type rawarray: :class:`numpy.ndarray`
        """
        if array is None:
            return
        if rawarray is None:
            rawarray = array

        self.__displaywidget.updateImage(array, rawarray)
        if self.__displaywidget.isCutsEnabled():
            self._plotCut()

    @QtCore.pyqtSlot()
    def _plotCut(self):
        """ plots the current 1d Cut
        """
        dt = self.__displaywidget.cutData()
        if dt is not None:
            self.__cutCurve.setData(y=dt)
            self.__cutPlot.setVisible(True)
            self.__cutCurve.setVisible(True)
        else:
            self.__cutCurve.setVisible(False)

    @QtCore.pyqtSlot(int)
    def setAutoLevels(self, autolevels):
        """ sets auto levels

        :param autolevels: auto levels enabled
        :type autolevels: :obj:`bool`
        """
        self.__displaywidget.setAutoLevels(autolevels)

    @QtCore.pyqtSlot(int)
    def setAutoDownSample(self, autodownsample):
        """ sets auto down sample

        :param autolevels: auto down sample enabled
        :type autolevels: :obj:`bool`
        """
        self.__displaywidget.setAutoDownSample(autodownsample)

    @QtCore.pyqtSlot(float)
    def setMinLevel(self, level=None):
        """ sets minimum intensity level

        :param level: minimum intensity
        :type level: :obj:`float`
        """
        self.__displaywidget.setDisplayMinLevel(level)

    @QtCore.pyqtSlot(float)
    def setMaxLevel(self, level=None):
        """ sets maximum intensity level

        :param level: maximum intensity
        :type level: :obj:`float`
        """
        self.__displaywidget.setDisplayMaxLevel(level)

    @QtCore.pyqtSlot(str)
    def setDisplayedText(self, text=None):
        """ sets displayed info text and recalculates the current roi sum

        :param text: text to display
        :type text: :obj:`str`
        """
        if text is not None:
            self.__lasttext = text
        else:
            text = self.__lasttext
        roiVal, currentroi = self.__displaywidget.calcROIsum()
        if currentroi is not None:
            self.roiValueChanged.emit(text, currentroi, roiVal)
        else:
            self.__ui.infoLineEdit.setText(text)

    @QtCore.pyqtSlot(str)
    def updateDisplayedText(self, text):
        """ sets displayed info text

        :param text: text to display
        :type text: :obj:`str`
        """
        self.__ui.infoLineEdit.setText(text)

    @QtCore.pyqtSlot(str)
    def updateDisplayedTextTip(self, text):
        """ sets displayed info text tup

        :param text: tip text to display
        :type text: :obj:`str`
        """
        self.__ui.infoLineEdit.setToolTip(text)

    @QtCore.pyqtSlot()
    def setTicks(self):
        """ launch axes widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        self.__displaywidget.setTicks()

    def image(self):
        """ provides imageItem object

        :returns: image object
        :rtype: :class:`pyqtgraph.ImageItem`
        """
        return self.__displaywidget.image()

    @QtCore.pyqtSlot(bool)
    def emitAspectLockedToggled(self, status):
        """emits aspectLockedToggled

        :param status: current state
        :type status: :obj:`bool`
        """
        self.aspectLockedToggled.emit(status)

    @QtCore.pyqtSlot()
    def _emitMouseImagePositionChanged(self):
        """emits mouseImagePositionChanged
        """
        self.mouseImagePositionChanged.emit()

    @QtCore.pyqtSlot(float, float)
    def _emitMouseImageDoubleClicked(self, x, y):
        """emits mouseImageDoubleClicked

        :param x: x pixel coordinate
        :type x: :obj:`float`
        :param y: y pixel coordinate
        :type y: :obj:`float`
        """
        self.mouseImageDoubleClicked.emit(x, y)

    @QtCore.pyqtSlot(float, float)
    def _emitMouseImageSingleClicked(self, x, y):
        """emits mouseImageSingleClicked

        :param x: x pixel coordinate
        :type x: :obj:`float`
        :param y: y pixel coordinate
        :type y: :obj:`float`
        """
        self.mouseImageSingleClicked.emit(x, y)

    def setAspectLocked(self, status):
        """sets aspectLocked

        :param status: state to set
        :type status: :obj:`bool`
        """
        self.__displaywidget.setAspectLocked(status)

    def setStatsWOScaling(self, status):
        """ sets statistics without scaling flag

        :param status: statistics without scaling flag
        :type status: :obj:`bool`
        """
        return self.__displaywidget.setStatsWOScaling(status)

    def setScalingType(self, scalingtype):
        """ sets intensity scaling types

        :param scalingtype: intensity scaling type
        :type scalingtype: :obj:`str`
        """
        self.__displaywidget.setScalingType(scalingtype)

    def setDoBkgSubtraction(self, state):
        """ sets do background subtraction flag

        :param status: do background subtraction flag
        :type status: :obj:`bool`
        """
        self.__displaywidget.setDoBkgSubtraction(state)

    def setSardanaUtils(self, sardana):
        """ sets sardana utils

        :param sardana: sardana utils
        :type sardana: :class:`lavuelib.sardanaUtils.SardanaUtils`
        """
        if sardana:
            self.sardanaEnabled.emit(True)
        else:
            self.sardanaEnabled.emit(False)
        self.__sardana = sardana

    @QtCore.pyqtSlot(str, int)
    def applyROIs(self, rlabel, roispin):
        """ saves ROIs in sardana and add them to the measurement group

        :param rlabel: rois aliases separated by space
        :type rlabel: :obj:`str`
        :param roispin: the current number of rois
        :type roispin: :obj:`int`
        """

        if isr.PYTANGO:
            if not self.__settings.doorname:
                self.__settings.doorname = self.__sardana.getDeviceName("Door")
            try:
                rois = json.loads(self.__sardana.getScanEnv(
                    str(self.__settings.doorname), ["DetectorROIs"]))
            except Exception:
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "Problems in connecting to Door or MacroServer")
                messageBox.MessageBox.warning(
                    self, "lavue: Error in connecting to Door or MacroServer",
                    text, str(value))
                return

            slabel = re.split(';|,| |\n', str(rlabel))
            slabel = [lb for lb in slabel if lb]
            rid = 0
            lastcrdlist = None
            toremove = []
            toadd = []
            if "DetectorROIs" not in rois or not isinstance(
                    rois["DetectorROIs"], dict):
                rois["DetectorROIs"] = {}
            lastalias = None

            roicoords = self.__displaywidget.roiCoords()
            for alias in slabel:
                if alias not in toadd:
                    rois["DetectorROIs"][alias] = []
                lastcrdlist = rois["DetectorROIs"][alias]
                if rid < len(roicoords):
                    lastcrdlist.append(roicoords[rid])
                    rid += 1
                    if alias not in toadd:
                        toadd.append(alias)
                if not lastcrdlist:
                    if alias in rois["DetectorROIs"].keys():
                        rois["DetectorROIs"].pop(alias)
                    if roispin >= 0:
                        toadd.append(alias)
                    else:
                        toremove.append(alias)
                lastalias = alias
            if rid > 0:
                while rid < len(roicoords):
                    lastcrdlist.append(roicoords[rid])
                    rid += 1
                if not lastcrdlist:
                    if lastalias in rois["DetectorROIs"].keys():
                        rois["DetectorROIs"].pop(lastalias)
                    if roispin >= 0:
                        toadd.append(lastalias)
                    else:
                        toremove.append(lastalias)

            self.__sardana.setScanEnv(
                str(self.__settings.doorname), json.dumps(rois))
            warns = []
            if self.__settings.addrois:
                try:
                    for alias in toadd:
                        _, warn = self.__sardana.runMacro(
                            str(self.__settings.doorname), ["nxsadd", alias])
                        if warn:
                            warns.extend(list(warn))
                            print("Warning: %s" % warn)
                    for alias in toremove:
                        _, warn = self.__sardana.runMacro(
                            str(self.__settings.doorname), ["nxsrm", alias])
                        if warn:
                            warns.extend(list(warn))
                            print("Warning: %s" % warn)
                    if warns:
                        msg = "\n".join(set(warns))
                        messageBox.MessageBox.warning(
                            self, "lavue: Errors in setting Measurement group",
                            msg, str(warns))

                except Exception:
                    import traceback
                    value = traceback.format_exc()
                    text = messageBox.MessageBox.getText(
                        "Problems in setting Measurement group")
                    messageBox.MessageBox.warning(
                        self, "lavue: Error in Setting Measurement group",
                        text, str(value))

        else:
            print("Connection error")

    @QtCore.pyqtSlot(str)
    def fetchROIs(self, rlabel):
        """ loads ROIs from sardana

        :param rlabel: rois aliases separated by space
        :type rlabel: :obj:`str`
        """
        if isr.PYTANGO:
            if not self.__settings.doorname:
                self.__settings.doorname = self.__sardana.getDeviceName("Door")
            try:
                rois = json.loads(self.__sardana.getScanEnv(
                    str(self.__settings.doorname), ["DetectorROIs"]))
            except Exception:
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "Problems in connecting to Door or MacroServer")
                messageBox.MessageBox.warning(
                    self, "lavue: Error in connecting to Door or MacroServer",
                    text, str(value))
                return
            slabel = re.split(';|,| |\n', str(rlabel))
            slabel = [lb for lb in set(slabel) if lb]
            detrois = {}
            if "DetectorROIs" in rois and isinstance(
                    rois["DetectorROIs"], dict):
                detrois = rois["DetectorROIs"]
                if slabel:
                    detrois = dict(
                        (k, v) for k, v in detrois.items() if k in slabel)
            coords = []
            aliases = []
            for k, v in detrois.items():
                if isinstance(v, list):
                    for cr in v:
                        if isinstance(cr, list):
                            coords.append(cr)
                            aliases.append(k)
            slabel = []
            for i, al in enumerate(aliases):
                if len(set(aliases[i:])) == 1:
                    slabel.append(al)
                    break
                else:
                    slabel.append(al)
            self.roiAliasesChanged.emit(" ".join(slabel))
            self.roiLineEditChanged.emit()

            self.updateROIs(len(coords), coords)
        else:
            print("Connection error")

    def currentIntensity(self):
        """ provides intensity for current mouse position

        :returns: x position, y position, pixel intensity
        :rtype: (`obj`:float:, `obj`:float:, `obj`:float:)
        """
        return self.__displaywidget.currentIntensity()

    def scalingLabel(self):
        """ provides scaling label

        :returns:  scaling label
        :rtype: `obj`:str:
        """
        return self.__displaywidget.scalingLabel()

    def scaledxy(self, x, y):
        """ provides scaled x,y positions

        :param x: x pixel coordinate
        :type x: :obj:`float`
        :param y: y pixel coordinate
        :type y: :obj:`float`
        :returns: scaled x,y position
        :rtype: (:obj:`float`, :obj:`float`)
        """
        return self.__displaywidget.scaledxy(x, y)

    def axesunits(self):
        """ return axes units
        :returns: x,y units
        :rtype: (:obj:`str`, :obj:`str`)
        """
        return self.__displaywidget.axesunits()

    def roiCoords(self):
        """ provides rois coordinates

        :return: rois coordinates
        :rtype: :obj:`list`
               < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        return self.__displaywidget.roiCoords()

    def cutCoords(self):
        """ provides cuts coordinates

        :return: cuts coordinates
        :rtype: :obj:`list`
               < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        return self.__displaywidget.cutCoords()

    def currentROI(self):
        """ provides current roi id

        :return: roi id
        :rtype: :obj:`int`
        """
        return self.__displaywidget.currentROI()

    def currentCut(self):
        """ provides current cut id

        :return: cut id
        :rtype: :obj:`int`
        """
        return self.__displaywidget.currentCut()

    def changeROIRegion(self):
        """ changes the current roi region
        """
        return self.__displaywidget.changeROIRegion()
