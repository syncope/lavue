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


import math

from PyQt4 import QtCore, QtGui, uic

import pyqtgraph as _pg
import numpy as np
import re
import os
import json

from . import imageDisplayWidget
from . import geometryDialog
from . import axesDialog
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
    #: (:class:`PyQt4.QtCore.pyqtSignal`) geometry tips changed signal
    geometryTipsChanged = QtCore.pyqtSignal(str)
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

    def __init__(self, parent=None, tooltypes=None, settings=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
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

        self.__currentroimapper = QtCore.QSignalMapper(self)
        self.__roiregionmapper = QtCore.QSignalMapper(self)
        self.__currentcutmapper = QtCore.QSignalMapper(self)
        self.__cutregionmapper = QtCore.QSignalMapper(self)

        self.__lasttext = ""

        #: (:class:`Ui_ImageWidget') ui_imagewidget object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        self.__displaywidget = imageDisplayWidget.ImageDisplayWidget(
            parent=self)

        self.__cutPlot = _pg.PlotWidget(self)
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
        # self.__cutPlot.setMinimumSize(QtCore.QSize(0, 180))
        if _VMAJOR == '0' and int(_VMINOR) < 10 and int(_VPATCH) < 9:
            self.__cutPlot.setMinimumSize(QtCore.QSize(0, 170))

        self.__addToolWidgets()

        self.__ui.plotSplitter.setStretchFactor(0, 20)
        self.__ui.plotSplitter.setStretchFactor(1, 1)
        self.__ui.toolSplitter.setStretchFactor(0, 100)
        self.__ui.toolSplitter.setStretchFactor(1, 1)

        self.__displaywidget.currentMousePosition.connect(
            self._setDisplayedText)

        self.__roiregionmapper.mapped.connect(self._roiRegionChanged)
        self.__currentroimapper.mapped.connect(self._currentROIChanged)
        self.__displaywidget.getROI().sigHoverEvent.connect(
            self.__currentroimapper.map)
        self.__displaywidget.getROI().sigRegionChanged.connect(
            self.__roiregionmapper.map)
        self.__currentroimapper.setMapping(self.__displaywidget.getROI(), 0)
        self.__roiregionmapper.setMapping(self.__displaywidget.getROI(), 0)

        self.cutCoordsChanged.connect(self._plotCut)

        self.__cutregionmapper.mapped.connect(self._cutRegionChanged)
        self.__currentcutmapper.mapped.connect(self._currentCutChanged)
        self.__displaywidget.getCut().sigHoverEvent.connect(
            self.__currentcutmapper.map)
        self.__displaywidget.getCut().sigRegionChanged.connect(
            self.__cutregionmapper.map)
        self.__currentcutmapper.setMapping(self.__displaywidget.getCut(), 0)
        self.__cutregionmapper.setMapping(self.__displaywidget.getCut(), 0)
        self.__displaywidget.centerAngleChanged.connect(self._updateGeometry)

        self.__ui.toolComboBox.currentIndexChanged.connect(
            self.onToolChanged)

        self.__displaywidget.setaspectlocked.triggered.connect(
            self._toggleAspectLocked)

        self.roiLineEditChanged.emit()

    def __addToolWidgets(self):
        """ add tool subwidgets into grid layout
        """
        for tt in self.__tooltypes:
            twg = getattr(toolWidget, tt)()
            self.__toolwidgets[twg.name] = twg
            self.__toolnames.append(twg.name)
            self.__ui.toolComboBox.addItem(twg.name)
            self.__ui.toolVerticalLayout.addWidget(twg)
            for signal, slot in twg.signal2slot:
                if isinstance(signal, str):
                    signal = getattr(self, signal)
                if isinstance(slot, str):
                    slot = getattr(self, slot)
                signal.connect(slot)

    @QtCore.pyqtSlot(int)
    def onAngleQChanged(self, gindex):
        self.__displaywidget.gspaceindex = gindex

    @QtCore.pyqtSlot()
    def geometry(self):
        cnfdlg = geometryDialog.GeometryDialog(self)
        cnfdlg.centerx = self.__displaywidget.centerx
        cnfdlg.centery = self.__displaywidget.centery
        cnfdlg.energy = self.__displaywidget.energy
        cnfdlg.pixelsizex = self.__displaywidget.pixelsizex
        cnfdlg.pixelsizey = self.__displaywidget.pixelsizey
        cnfdlg.detdistance = self.__displaywidget.detdistance
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__displaywidget.centerx = cnfdlg.centerx
            self.__displaywidget.centery = cnfdlg.centery
            self.__displaywidget.energy = cnfdlg.energy
            self.__displaywidget.pixelsizex = cnfdlg.pixelsizex
            self.__displaywidget.pixelsizey = cnfdlg.pixelsizey
            self.__displaywidget.detdistance = cnfdlg.detdistance
            self.__updateGeometryTip()

    @QtCore.pyqtSlot()
    def _updateGeometry(self):
        self._setDisplayedText("")
        self.__updateGeometryTip()

    def __updateGeometryTip(self):
        message = self.__displaywidget.geometryMessage()
        self.__ui.infoLineEdit.setToolTip(
            "coordinate info display for the mouse pointer\n%s" % message)
        self.geometryTipsChanged.emit(message)

    def updateMetaData(self, axisscales=None, axislabels=None):
        if axislabels is not None:
            self.__displaywidget.xtext = str(axislabels[0]) \
                if axislabels[0] is not None else None
            self.__displaywidget.ytext = str(axislabels[1]) \
                if axislabels[0] is not None else None
            self.__displaywidget.xunits = str(axislabels[2]) \
                if axislabels[0] is not None else None
            self.__displaywidget.yunits = str(axislabels[3]) \
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
        self.__displaywidget.setScale(
            position, scale,
            not self.__displaywidget.roienable
            and not self.__displaywidget.cutenable
            and not self.__displaywidget.qenable)

    @QtCore.pyqtSlot(int)
    def _roiRegionChanged(self, rid=None):
        try:
            # ?? rid == rid
            rid = self.__displaywidget.currentroi
            state = self.__displaywidget.getROI(rid).state
            ptx = int(math.floor(state['pos'].x()))
            pty = int(math.floor(state['pos'].y()))
            szx = int(math.floor(state['size'].x()))
            szy = int(math.floor(state['size'].y()))
            self.__displaywidget.roicoords[rid] = [
                ptx, pty, ptx + szx, pty + szy]
            self.roiCoordsChanged.emit()
        except Exception as e:
            print("Warning: %s" % str(e))

    @QtCore.pyqtSlot(int)
    def _cutRegionChanged(self, cid):
        try:
            # ??? cid == cid
            cid = self.__displaywidget.currentcut
            self.__displaywidget.cutcoords[cid] = \
                self.__displaywidget.getCut(cid).getCoordinates()
            self.cutCoordsChanged.emit()
        except Exception as e:
            print("Warning: %s" % str(e))

    @QtCore.pyqtSlot(int)
    def _currentROIChanged(self, rid):
        oldrid = self.__displaywidget.currentroi
        if rid != oldrid:
            self.__displaywidget.currentroi = rid
            self.roiCoordsChanged.emit()

    @QtCore.pyqtSlot(int)
    def _currentCutChanged(self, cid):
        oldcid = self.__displaywidget.currentcut
        if cid != oldcid:
            self.__displaywidget.currentcut = cid
            self.cutCoordsChanged.emit()

    @QtCore.pyqtSlot(int)
    def roiNrChanged(self, rid, coords=None):
        self.applyTipsChanged.emit(rid)
        self.__displaywidget.addROICoords(coords)
        while rid > self.__displaywidget.countROIs():
            if coords and len(coords) >= self.__displaywidget.countROIs():
                self.__displaywidget.addROI(
                    coords[self.__displaywidget.countROIs()])
            else:
                self.__displaywidget.addROI()
            self.__displaywidget.getROI().sigHoverEvent.connect(
                self.__currentroimapper.map)
            self.__displaywidget.getROI().sigRegionChanged.connect(
                self.__roiregionmapper.map)
            self.__currentroimapper.setMapping(
                self.__displaywidget.getROI(),
                self.__displaywidget.countROIs() - 1)
            self.__roiregionmapper.setMapping(
                self.__displaywidget.getROI(),
                self.__displaywidget.countROIs() - 1)
        if rid <= 0:
            self.__displaywidget.currentroi = -1
        elif self.__displaywidget.currentroi >= rid:
            self.__displaywidget.currentroi = 0
        #        while max(rid, 0) < len(self.__displaywidget.roi):
        while self.__displaywidget.getROI(max(rid, 0)) is not None:
            self.__currentroimapper.removeMappings(
                self.__displaywidget.getROI())
            self.__roiregionmapper.removeMappings(
                self.__displaywidget.getROI())
            self.__displaywidget.removeROI()
        self.roiCoordsChanged.emit()
        self.roiNumberChanged.emit(rid)

    @QtCore.pyqtSlot(int)
    def cutNrChanged(self, cid, coords=None):
        self.__displaywidget.addCutCoords(coords)
        while cid > self.__displaywidget.countCuts():
            if coords and len(coords) >= self.__displaywidget.countCuts():
                self.__displaywidget.addCut(
                    coords[self.__displaywidget.countCuts()])
            else:
                self.__displaywidget.addCut()
            self.__displaywidget.getCut().sigHoverEvent.connect(
                self.__currentcutmapper.map)
            self.__displaywidget.getCut().sigRegionChanged.connect(
                self.__cutregionmapper.map)
            self.__currentcutmapper.setMapping(
                self.__displaywidget.getCut(),
                self.__displaywidget.countCuts() - 1)
            self.__cutregionmapper.setMapping(
                self.__displaywidget.getCut(),
                self.__displaywidget.countCuts() - 1)
        if cid <= 0:
            self.__displaywidget.currentcut = -1
        elif self.__displaywidget.currentcut >= cid:
            self.__displaywidget.currentcut = 0
        while max(cid, 0) < self.__displaywidget.countCuts():
            self.__currentcutmapper.removeMappings(
                self.__displaywidget.getCut())
            self.__cutregionmapper.removeMappings(
                self.__displaywidget.getCut())
            self.__displaywidget.removeCut()
        self.cutCoordsChanged.emit()
        self.cutNumberChanged.emit(cid)

    @QtCore.pyqtSlot(int)
    def onToolChanged(self):
        text = self.__ui.toolComboBox.currentText()
        stwg = None
        for nm, twg in self.__toolwidgets.items():
            if text == nm:
                stwg = twg
            else:
                twg.hide()
        if stwg is not None:
            stwg.show()
            self.__displaywidget.setSubWidgets(stwg.parameters)
            self.__updateinfowidgets(stwg.parameters)

        if text == "ROI":
            self._roiRegionChanged()
        elif text == "LineCut":
            self.roiCoordsChanged.emit()
        elif text == "Angle/Q":
            self.__updateGeometryTip()
            self.roiCoordsChanged.emit()
        else:
            self.roiCoordsChanged.emit()
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
        elif parameters.cutplot is False:
            self.__cutPlot.hide()

    def plot(self, array, rawarray=None):
        if array is None:
            return
        if rawarray is None:
            rawarray = array

        self.__displaywidget.updateImage(array, rawarray)
        if self.__displaywidget.cutenable:
            self._plotCut()
        if self.__displaywidget.roienable:
            self._setDisplayedText()

    def __calcROIsum(self):
        rid = self.__displaywidget.currentroi
        image = None
        if self.__displaywidget.rawdata is not None:
            image = self.__displaywidget.rawdata
        if image is not None:
            if self.__displaywidget.roienable:
                if rid >= 0:
                    roicoords = self.__displaywidget.roicoords
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

    @QtCore.pyqtSlot()
    def _plotCut(self):
        cid = self.__displaywidget.currentcut
        if cid > -1 and self.__displaywidget.countCuts() > cid:
            cut = self.__displaywidget.getCut(cid)
            if self.__displaywidget.rawdata is not None:
                dt = cut.getArrayRegion(
                    self.__displaywidget.rawdata,
                    self.__displaywidget.image, axes=(0, 1))
                while dt.ndim > 1:
                    dt = dt.mean(axis=1)
                self.__cutCurve.setData(y=dt)
                self.__cutPlot.setVisible(True)
                self.__cutCurve.setVisible(True)
                return
        self.__cutCurve.setVisible(False)

    @QtCore.pyqtSlot(int)
    def setAutoLevels(self, autoLvls):
        self.__displaywidget.setAutoLevels(autoLvls)

    @QtCore.pyqtSlot(float)
    def setMinLevel(self, level=None):
        self.__displaywidget.setDisplayMinLevel(level)

    @QtCore.pyqtSlot(float)
    def setMaxLevel(self, level=None):
        self.__displaywidget.setDisplayMaxLevel(level)

    @QtCore.pyqtSlot(str)
    def _setDisplayedText(self, text=None):
        if text is not None:
            self.__lasttext = text
        else:
            text = self.__lasttext
        if self.__displaywidget.roienable and \
           self.__displaywidget.getROI() is not None:
            currentroi = self.__displaywidget.currentroi
            self.__ui.infoLineEdit.setText(text)
            if currentroi >= 0:
                roiVal, currentroi = self.__calcROIsum()
                self.roiValueChanged.emit(text, currentroi, roiVal)
        else:
            self.__ui.infoLineEdit.setText(text)

    @QtCore.pyqtSlot(str)
    def updateDisplayedText(self, text):
        self.__ui.infoLineEdit.setText(text)

    @QtCore.pyqtSlot()
    def setTicks(self):
        cnfdlg = axesDialog.AxesDialog(self)
        if self.__displaywidget.position is None:
            cnfdlg.xposition = None
            cnfdlg.yposition = None
        else:
            cnfdlg.xposition = self.__displaywidget.position[0]
            cnfdlg.yposition = self.__displaywidget.position[1]
        if self.__displaywidget.scale is None:
            cnfdlg.xscale = None
            cnfdlg.yscale = None
        else:
            cnfdlg.xscale = self.__displaywidget.scale[0]
            cnfdlg.yscale = self.__displaywidget.scale[1]

        cnfdlg.xtext = self.__displaywidget.xtext
        cnfdlg.ytext = self.__displaywidget.ytext

        cnfdlg.xunits = self.__displaywidget.xunits
        cnfdlg.yunits = self.__displaywidget.yunits

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
            self.__displaywidget.xtext = cnfdlg.xtext or None
            self.__displaywidget.ytext = cnfdlg.ytext or None

            self.__displaywidget.xunits = cnfdlg.xunits or None
            self.__displaywidget.yunits = cnfdlg.yunits or None
            self.__displaywidget.setScale(position, scale)
            self.__displaywidget.updateImage(
                self.__displaywidget.data, self.__displaywidget.rawdata)
            return True
        return False

    def image(self):
        return self.__displaywidget.image

    @QtCore.pyqtSlot(bool)
    def _toggleAspectLocked(self, status):
        self.aspectLockedToggled.emit(status)

    def setAspectLocked(self, status):
        self.__displaywidget.setAspectLocked(status)

    def setStatsWOScaling(self, status):
        if self.__displaywidget.statswoscaling != status:
            self.__displaywidget.statswoscaling = status
            return True
        return False

    def setScalingType(self, scalingtype):
        self.__displaywidget.scaling = scalingtype

    def setDoBkgSubtraction(self, state):
        self.__displaywidget.dobkgsubtraction = state

    def setSardanaUtils(self, sardana):
        if sardana:
            self.sardanaEnabled.emit(True)
        else:
            self.sardanaEnabled.emit(False)
        self.__sardana = sardana

    @QtCore.pyqtSlot(str, int)
    def onapplyrois(self, rlabel, roispin):
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

            roicoords = self.__displaywidget.roicoords
            slabel = re.split(';|,| |\n', rlabel)
            slabel = [lb for lb in slabel if lb]
            rid = 0
            lastcrdlist = None
            toremove = []
            toadd = []
            if "DetectorROIs" not in rois or not isinstance(
                    rois["DetectorROIs"], dict):
                rois["DetectorROIs"] = {}
            lastalias = None
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
    def onfetchrois(self, rlabel):
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
            slabel = re.split(';|,| |\n', rlabel)
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
            
            self.roiNrChanged(len(coords), coords)
        else:
            print("Connection error")
