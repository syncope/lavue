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

from . import imageDisplayWidget
from . import geometryDialog
from . import axesDialog

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ImageWidget.ui"))

_intensityformclass, _intensitybaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "IntensityToolWidget.ui"))

_roiformclass, _roibaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ROIToolWidget.ui"))

_cutformclass, _cutbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "LineCutToolWidget.ui"))

_angleqformclass, _angleqbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "AngleQToolWidget.ui"))

class ToolWidget(QtGui.QWidget):
    """ tool widget
    """
    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        QtGui.QWidget.__init__(self, parent)
    

class IntensityToolWidget(ToolWidget):
    """ intensity tool widget
    """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        ToolWidget.__init__(self, parent)

class ImageWidget(QtGui.QWidget):

    """
    The part of the GUI that incorporates the image view.
    """

    roiCoordsChanged = QtCore.pyqtSignal()
    cutCoordsChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) current tool changed
    currentToolChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.nparray = None
        self.imageItem = None
        self.currentroimapper = QtCore.QSignalMapper(self)
        self.roiregionmapper = QtCore.QSignalMapper(self)
        self.currentcutmapper = QtCore.QSignalMapper(self)
        self.cutregionmapper = QtCore.QSignalMapper(self)

        self.__lasttext = ""

        #: (:class:`Ui_ImageWidget') ui_imagewidget object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        self.displaywidget = imageDisplayWidget.ImageDisplayWidget(parent=self)
        
        self.cutPlot = _pg.PlotWidget(self)
        self.cutCurve = self.cutPlot.plot()
        self.__ui.twoDVerticalLayout.addWidget(self.displaywidget)
        self.__ui.oneDVerticalLayout.addWidget(self.cutPlot)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,
                                       QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(15)
        sizePolicy.setHeightForWidth(
            self.displaywidget.sizePolicy().hasHeightForWidth())
        self.displaywidget.setSizePolicy(sizePolicy)
        self.cutPlot.setMinimumSize(QtCore.QSize(0, 180))

        self.__ui.toolComboBox.addItem("Intensity")
        self.__ui.toolComboBox.addItem("ROI")
        self.__ui.toolComboBox.addItem("LineCut")
        self.__ui.toolComboBox.addItem("Angle/Q")

        pixelvaluelayout = QtGui.QHBoxLayout()

        self.toolLabel = QtGui.QLabel("Pixel position and intensity: ")
        self.toolLabel.setToolTip(
            "coordinate info display for the mouse pointer")

        self.axesPushButton = QtGui.QPushButton("Axes ...")

        self.labelROILineEdit = QtGui.QLineEdit("")
        self.labelROILineEdit.setToolTip(
            "ROI alias or aliases related to Sardana Pool "
            "experimental channels")
        self.roiSpinBox = QtGui.QSpinBox()
        self.roiSpinBox.setMinimum(-1)
        self.roiSpinBox.setValue(1)
        self.roiSpinBox.setToolTip(
            "number of ROIs to add, -1 means remove ROI aliases from sardana")
        self.fetchROIButton = QtGui.QPushButton("Fetch")
        self.fetchROIButton.setToolTip(
            "fetch ROI aliases from the Door environment")
        self.applyROIButton = QtGui.QPushButton("Add")
        self.applyROIButton.setToolTip(
            "add ROI aliases to the Door environment "
            "as well as to Active MntGrp")

        self.cutSpinBox = QtGui.QSpinBox()
        self.cutSpinBox.setMinimum(0)
        self.cutSpinBox.setValue(1)
        self.cutSpinBox.setToolTip(
            "number of Line Cuts")

        self.angleqPushButton = QtGui.QPushButton("Geometry ...")
        self.angleqPushButton.setToolTip("Input physical parameters")
        self.angleqComboBox = QtGui.QComboBox()
        self.angleqComboBox.addItem("angles")
        self.angleqComboBox.addItem("q-space")
        self.angleqComboBox.setToolTip("Select the display space")

        pixelvaluelayout.addWidget(self.toolLabel)
        pixelvaluelayout.addWidget(self.labelROILineEdit)
        pixelvaluelayout.addWidget(self.roiSpinBox)
        pixelvaluelayout.addWidget(self.cutSpinBox)
        pixelvaluelayout.addWidget(self.applyROIButton)
        pixelvaluelayout.addWidget(self.fetchROIButton)
        pixelvaluelayout.addWidget(self.angleqPushButton)
        pixelvaluelayout.addWidget(self.angleqComboBox)
        pixelvaluelayout.addWidget(self.axesPushButton)


        self.__ui.toolVerticalLayout.addLayout(pixelvaluelayout)

        self.__ui.plotSplitter.setStretchFactor(0, 20)
        self.__ui.plotSplitter.setStretchFactor(1, 1)
        self.__ui.toolSplitter.setStretchFactor(0, 100)
        self.__ui.toolSplitter.setStretchFactor(1, 1)

        self.displaywidget.currentMousePosition.connect(self.setDisplayedText)

        self.roiregionmapper.mapped.connect(self.roiRegionChanged)
        self.currentroimapper.mapped.connect(self.currentROIChanged)
        self.displaywidget.getROI().sigHoverEvent.connect(
            self.currentroimapper.map)
        self.displaywidget.getROI().sigRegionChanged.connect(
            self.roiregionmapper.map)
        self.currentroimapper.setMapping(self.displaywidget.getROI(), 0)
        self.roiregionmapper.setMapping(self.displaywidget.getROI(), 0)

        self.cutCoordsChanged.connect(self.plotCut)
        self.roiSpinBox.valueChanged.connect(self.roiNrChanged)
        self.labelROILineEdit.textEdited.connect(self.updateROIButton)
        self.updateROIButton()

        self.cutregionmapper.mapped.connect(self.cutRegionChanged)
        self.currentcutmapper.mapped.connect(self.currentCutChanged)
        self.displaywidget.getCut().sigHoverEvent.connect(
            self.currentcutmapper.map)
        self.displaywidget.getCut().sigRegionChanged.connect(
            self.cutregionmapper.map)
        self.currentcutmapper.setMapping(self.displaywidget.getCut(), 0)
        self.cutregionmapper.setMapping(self.displaywidget.getCut(), 0)
        self.angleqPushButton.clicked.connect(self.geometry)
        self.angleqComboBox.currentIndexChanged.connect(
            self.onAngleQChanged)
        self.displaywidget.centerAngleChanged.connect(self.updateGeometry)
        self.cutSpinBox.valueChanged.connect(self.cutNrChanged)

        self.__ui.toolComboBox.currentIndexChanged.connect(
            self.onToolChanged)

    @QtCore.pyqtSlot(int)
    def onAngleQChanged(self, gindex):
        self.displaywidget.gspaceindex = gindex

    @QtCore.pyqtSlot()
    def geometry(self):
        cnfdlg = geometryDialog.GeometryDialog(self)
        cnfdlg.centerx = self.displaywidget.centerx
        cnfdlg.centery = self.displaywidget.centery
        cnfdlg.energy = self.displaywidget.energy
        cnfdlg.pixelsizex = self.displaywidget.pixelsizex
        cnfdlg.pixelsizey = self.displaywidget.pixelsizey
        cnfdlg.detdistance = self.displaywidget.detdistance
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.displaywidget.centerx = cnfdlg.centerx
            self.displaywidget.centery = cnfdlg.centery
            self.displaywidget.energy = cnfdlg.energy
            self.displaywidget.pixelsizex = cnfdlg.pixelsizex
            self.displaywidget.pixelsizey = cnfdlg.pixelsizey
            self.displaywidget.detdistance = cnfdlg.detdistance
            self.updateGeometryTip()

    @QtCore.pyqtSlot()
    def updateGeometry(self):
        self.setDisplayedText("")
        self.updateGeometryTip()

    @QtCore.pyqtSlot()
    def updateGeometryTip(self):
        message = u"geometry:\n" \
                  u"  center = (%s, %s) pixels\n" \
                  u"  pixel_size = (%s, %s) \u00B5m\n" \
                  u"  detector_distance = %s mm\n" \
                  u"  energy = %s eV" % (
                      self.displaywidget.centerx,
                      self.displaywidget.centery,
                      self.displaywidget.pixelsizex,
                      self.displaywidget.pixelsizey,
                      self.displaywidget.detdistance,
                      self.displaywidget.energy
                  )
        self.angleqPushButton.setToolTip(
            "Input physical parameters\n%s" % message)
        self.angleqComboBox.setToolTip(
            "Select the display space\n%s" % message)
        self.toolLabel.setToolTip(
            "coordinate info display for the mouse pointer\n%s" % message)
        self.__ui.infoLineEdit.setToolTip(
            "coordinate info display for the mouse pointer\n%s" % message)

    def updateMetaData(self, axisscales=None, axislabels=None):
        if axislabels is not None:
            self.displaywidget.xtext = str(axislabels[0]) \
                if axislabels[0] is not None else None
            self.displaywidget.ytext = str(axislabels[1]) \
                if axislabels[0] is not None else None
            self.displaywidget.xunits = str(axislabels[2]) \
                if axislabels[0] is not None else None
            self.displaywidget.yunits = str(axislabels[3]) \
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
        self.displaywidget.setScale(
            position, scale,
            not self.displaywidget.roienable
            and not self.displaywidget.cutenable
            and not self.displaywidget.qenable)

    @QtCore.pyqtSlot(int)
    def roiRegionChanged(self, _):
        self.roiChanged()

    @QtCore.pyqtSlot(int)
    def cutRegionChanged(self, cid):
        self.cutChanged()

    @QtCore.pyqtSlot(int)
    def currentROIChanged(self, rid):
        oldrid = self.displaywidget.currentroi
        if rid != oldrid:
            self.displaywidget.currentroi = rid
            self.roiCoordsChanged.emit()

    @QtCore.pyqtSlot(int)
    def currentCutChanged(self, cid):
        oldcid = self.displaywidget.currentcut
        if cid != oldcid:
            self.displaywidget.currentcut = cid
            self.cutCoordsChanged.emit()

    @QtCore.pyqtSlot()
    def updateROIButton(self):
        if not str(self.labelROILineEdit.text()).strip():
            self.applyROIButton.setEnabled(False)
        else:
            self.applyROIButton.setEnabled(True)

    @QtCore.pyqtSlot(int)
    def roiNrChanged(self, rid, coords=None):
        if rid < 0:
            self.applyROIButton.setText("Remove")
            self.applyROIButton.setToolTip(
                "remove ROI aliases from the Door environment"
                " as well as from Active MntGrp")
        else:
            self.applyROIButton.setText("Add")
            self.applyROIButton.setToolTip(
                "add ROI aliases to the Door environment "
                "as well as to Active MntGrp")
        if coords:
            for i, crd in enumerate(self.displaywidget.roi):
                if i < len(coords):
                    self.displaywidget.roicoords[i] = coords[i]
                    crd.setPos([coords[i][0], coords[i][1]])
                    crd.setSize(
                        [coords[i][2] - coords[i][0],
                         coords[i][3] - coords[i][1]])
        while rid > self.displaywidget.countROIs():
            if coords and len(coords) >= self.displaywidget.countROIs():
                self.displaywidget.addROI(
                    coords[self.displaywidget.countROIs()])
            else:
                self.displaywidget.addROI()
            self.displaywidget.getROI().sigHoverEvent.connect(
                self.currentroimapper.map)
            self.displaywidget.getROI().sigRegionChanged.connect(
                self.roiregionmapper.map)
            self.currentroimapper.setMapping(
                self.displaywidget.getROI(),
                self.displaywidget.countROIs() - 1)
            self.roiregionmapper.setMapping(
                self.displaywidget.getROI(),
                self.displaywidget.countROIs() - 1)
        if rid <= 0:
            self.displaywidget.currentroi = -1
        elif self.displaywidget.currentroi >= rid:
            self.displaywidget.currentroi = 0
        #        while max(rid, 0) < len(self.displaywidget.roi):
        while self.displaywidget.getROI(max(rid, 0)) is not None:
            self.currentroimapper.removeMappings(self.displaywidget.getROI())
            self.roiregionmapper.removeMappings(self.displaywidget.getROI())
            self.displaywidget.removeROI()
        self.roiCoordsChanged.emit()
        self.roiSpinBox.setValue(rid)

    @QtCore.pyqtSlot(int)
    def cutNrChanged(self, cid, coords=None):
        if coords:
            for i, crd in enumerate(self.displaywidget.cut):
                if i < len(coords):
                    self.displaywidget.cutcoords[i] = coords[i]
                    crd.setPos([coords[i][0], coords[i][1]])
                    crd.setSize(
                        [coords[i][2] - coords[i][0],
                         coords[i][3] - coords[i][1]])
        while cid > self.displaywidget.countCuts():
            if coords and len(coords) >= self.displaywidget.countCuts():
                self.displaywidget.addCut(
                    coords[self.displaywidget.countCuts()])
            else:
                self.displaywidget.addCut()
            self.displaywidget.getCut().sigHoverEvent.connect(
                self.currentcutmapper.map)
            self.displaywidget.getCut().sigRegionChanged.connect(
                self.cutregionmapper.map)
            self.currentcutmapper.setMapping(
                self.displaywidget.getCut(),
                self.displaywidget.countCuts() - 1)
            self.cutregionmapper.setMapping(
                self.displaywidget.getCut(),
                self.displaywidget.countCuts() - 1)
        if cid <= 0:
            self.displaywidget.currentcut = -1
        elif self.displaywidget.currentcut >= cid:
            self.displaywidget.currentcut = 0
        while max(cid, 0) < self.displaywidget.countCuts():
            self.currentcutmapper.removeMappings(self.displaywidget.getCut())
            self.cutregionmapper.removeMappings(self.displaywidget.getCut())
            self.displaywidget.removeCut()
        self.cutCoordsChanged.emit()
        self.cutSpinBox.setValue(cid)

    @QtCore.pyqtSlot(int)
    def onToolChanged(self):
        text = self.__ui.toolComboBox.currentText()
        if text == "ROI":
            self.showROIFrame()
            self.roiChanged()
        elif text == "LineCut":
            self.showLineCutFrame()
            self.roiCoordsChanged.emit()
        elif text == "Angle/Q":
            self.showAngleQFrame()
            self.roiCoordsChanged.emit()
        else:
            self.showIntensityFrame()
            self.roiCoordsChanged.emit()
        self.currentToolChanged.emit(text)


    def roiChanged(self):
        try:
            rid = self.displaywidget.currentroi
            state = self.displaywidget.getROI(rid).state
            ptx = int(math.floor(state['pos'].x()))
            pty = int(math.floor(state['pos'].y()))
            szx = int(math.floor(state['size'].x()))
            szy = int(math.floor(state['size'].y()))
            self.displaywidget.roicoords[rid] = [
                ptx, pty, ptx + szx, pty + szy]
            self.roiCoordsChanged.emit()
        except Exception as e:
            print("Warning: %s" % str(e))

    def cutChanged(self):
        try:
            cid = self.displaywidget.currentcut
            self.displaywidget.cutcoords[cid] = \
                self.displaywidget.getCut(cid).getCoordinates()
            self.cutCoordsChanged.emit()
        except Exception as e:
            print("Warning: %s" % str(e))

    def showROIFrame(self):
        self.displaywidget.showLines(False)
        self.axesPushButton.hide()
        self.angleqPushButton.hide()
        self.angleqComboBox.hide()
        self.cutPlot.hide()
        self.fetchROIButton.show()
        self.applyROIButton.show()
        self.roiSpinBox.show()
        self.cutSpinBox.hide()
        self.labelROILineEdit.show()

        self.toolLabel.setText("ROI alias(es): ")
        self.__ui.infoLabel.show()
        self.displaywidget.showROIs(True)
        self.displaywidget.showCuts(False)
        doreset = not (self.displaywidget.cutenable or
                       self.displaywidget.roienable or
                       self.displaywidget.qenable)
        self.displaywidget.cutenable = False
        self.displaywidget.roienable = True
        self.displaywidget.qenable = False
        self.__ui.infoLineEdit.setText("")
        self.__ui.infoLineEdit.setToolTip(
            "coordinate info display for the mouse pointer")
        self.toolLabel.setToolTip(
            "ROI alias or aliases related to sardana experimental channels")
        if doreset:
            self.displaywidget.resetScale()

    def showIntensityFrame(self):
        self.toolLabel.setText("Pixel position and intensity: ")
        self.displaywidget.showROIs(False)
        self.displaywidget.showCuts(False)
        self.cutPlot.hide()
        self.axesPushButton.show()
        self.angleqPushButton.hide()
        self.angleqComboBox.hide()
        self.fetchROIButton.hide()
        self.labelROILineEdit.hide()
        self.applyROIButton.hide()
        self.roiSpinBox.hide()
        self.cutSpinBox.hide()
        self.__ui.infoLabel.hide()
        self.displaywidget.roienable = False
        self.displaywidget.cutenable = False
        self.displaywidget.qenable = False
        self.displaywidget.showLines(True)
        self.__ui.infoLineEdit.setText("")
        self.__ui.infoLineEdit.setToolTip(
            "coordinate info display for the mouse pointer")
        self.toolLabel.setToolTip(
            "coordinate info display for the mouse pointer")
        self.displaywidget.setScale(
            self.displaywidget.position, self.displaywidget.scale)

    def showLineCutFrame(self):
        self.toolLabel.setText("Cut, pixel position and intensity: ")
        self.displaywidget.showROIs(False)
        self.displaywidget.showCuts(True)
        self.cutPlot.show()
        self.fetchROIButton.hide()
        self.axesPushButton.hide()
        self.angleqPushButton.hide()
        self.angleqComboBox.hide()
        self.labelROILineEdit.hide()
        self.applyROIButton.hide()
        self.cutSpinBox.show()
        self.roiSpinBox.hide()
        self.__ui.infoLabel.hide()
        doreset = not (self.displaywidget.cutenable or
                       self.displaywidget.roienable or
                       self.displaywidget.qenable)
        self.displaywidget.roienable = False
        self.displaywidget.cutenable = True
        self.displaywidget.qenable = False
        self.displaywidget.showLines(False)
        self.__ui.infoLineEdit.setText("")
        self.__ui.infoLineEdit.setToolTip(
            "coordinate info display for the mouse pointer")
        self.toolLabel.setToolTip(
            "coordinate info display for the mouse pointer")
        if doreset:
            self.displaywidget.resetScale()

    def showAngleQFrame(self):
        self.toolLabel.setText("Pixel position and intensity: ")
        self.displaywidget.showROIs(False)
        self.displaywidget.showCuts(False)
        self.cutPlot.hide()
        self.axesPushButton.hide()
        self.angleqPushButton.show()
        self.angleqComboBox.show()
        self.fetchROIButton.hide()
        self.labelROILineEdit.hide()
        self.applyROIButton.hide()
        self.roiSpinBox.hide()
        self.cutSpinBox.hide()
        self.__ui.infoLabel.hide()
        doreset = not (self.displaywidget.cutenable or
                       self.displaywidget.roienable or
                       self.displaywidget.qenable)
        self.displaywidget.roienable = False
        self.displaywidget.cutenable = False
        self.displaywidget.qenable = True
        self.displaywidget.showLines(True)
        self.__ui.infoLineEdit.setText("")
        self.updateGeometryTip()
        if doreset:
            self.displaywidget.resetScale()

    def plot(self, array, rawarray=None):
        if array is None:
            return
        if rawarray is None:
            rawarray = array

        self.displaywidget.updateImage(array, rawarray)
        if self.displaywidget.cutenable:
            self.plotCut()
        if self.displaywidget.roienable:
            self.setDisplayedText()

    def createROILabel(self):
        roilabel = ""
        currentroi = self.displaywidget.currentroi
        if currentroi >= 0:
            roilabel = "roi [%s]" % (currentroi + 1)
            slabel = []
            rlabel = str(self.labelROILineEdit.text())
            if rlabel:
                slabel = re.split(';|,| |\n', rlabel)
                slabel = [lb for lb in slabel if lb]
            if slabel:
                roilabel = "%s [%s]" % (
                    slabel[currentroi]
                    if currentroi < len(slabel) else slabel[-1],
                    (currentroi + 1)
                )
        return roilabel

    def calcROIsum(self):
        rid = self.displaywidget.currentroi
        image = None
        if self.displaywidget.rawdata is not None:
            image = self.displaywidget.rawdata
        if image is not None:
            if self.displaywidget.roienable:
                if rid >= 0:
                    roicoords = self.displaywidget.roicoords
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
    def plotCut(self):
        cid = self.displaywidget.currentcut
        if cid > -1 and self.displaywidget.countCuts() > cid:
            cut = self.displaywidget.getCut(cid)
            if self.displaywidget.rawdata is not None:
                dt = cut.getArrayRegion(
                    self.displaywidget.rawdata,
                    self.displaywidget.image, axes=(0, 1))
                while dt.ndim > 1:
                    dt = dt.mean(axis=1)
                self.cutCurve.setData(y=dt)
                self.cutPlot.setVisible(True)
                self.cutCurve.setVisible(True)
                return
        self.cutCurve.setVisible(False)

    @QtCore.pyqtSlot(int)
    def setAutoLevels(self, autoLvls):
        self.displaywidget.setAutoLevels(autoLvls)

    @QtCore.pyqtSlot(float)
    def setMinLevel(self, level=None):
        self.displaywidget.setDisplayMinLevel(level)

    @QtCore.pyqtSlot(float)
    def setMaxLevel(self, level=None):
        self.displaywidget.setDisplayMaxLevel(level)

    @QtCore.pyqtSlot(str)
    def changeGradient(self, name):
        self.displaywidget.updateGradient(name)

    @QtCore.pyqtSlot(str)
    def setDisplayedText(self, text=None):
        if text is not None:
            self.__lasttext = text
        else:
            text = self.__lasttext
        if self.displaywidget.roienable and \
           self.displaywidget.getROI() is not None:
            roiVal, currentroi = self.calcROIsum()
            roilabel = self.createROILabel()

            text = "%s, %s = %s" % (text, roilabel, roiVal)
        self.__ui.infoLineEdit.setText(text)

    def setTicks(self):
        cnfdlg = axesDialog.AxesDialog(self)
        if self.displaywidget.position is None:
            cnfdlg.xposition = None
            cnfdlg.yposition = None
        else:
            cnfdlg.xposition = self.displaywidget.position[0]
            cnfdlg.yposition = self.displaywidget.position[1]
        if self.displaywidget.scale is None:
            cnfdlg.xscale = None
            cnfdlg.yscale = None
        else:
            cnfdlg.xscale = self.displaywidget.scale[0]
            cnfdlg.yscale = self.displaywidget.scale[1]

        cnfdlg.xtext = self.displaywidget.xtext
        cnfdlg.ytext = self.displaywidget.ytext

        cnfdlg.xunits = self.displaywidget.xunits
        cnfdlg.yunits = self.displaywidget.yunits

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
            self.displaywidget.xtext = cnfdlg.xtext or None
            self.displaywidget.ytext = cnfdlg.ytext or None

            self.displaywidget.xunits = cnfdlg.xunits or None
            self.displaywidget.yunits = cnfdlg.yunits or None
            self.displaywidget.setScale(position, scale)
            return True
        return False
