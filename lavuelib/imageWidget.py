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

from PyQt4 import QtCore, QtGui

import pyqtgraph as _pg
import numpy as np
import re

from . import imageDisplayWidget
from . import geometryDialog
from . import axesDialog


class ImageWidget(QtGui.QWidget):

    """
    The part of the GUI that incorporates the image view.
    """

    roiCoordsChanged = QtCore.pyqtSignal()
    cutCoordsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.nparray = None
        self.imageItem = None
        self.currentroimapper = QtCore.QSignalMapper(self)
        self.roiregionmapper = QtCore.QSignalMapper(self)
        self.currentcutmapper = QtCore.QSignalMapper(self)
        self.cutregionmapper = QtCore.QSignalMapper(self)

        self.__lasttext = ""
        verticallayout = QtGui.QVBoxLayout()

        self.splitter2 = QtGui.QSplitter(self)
        self.splitter2.setOrientation(QtCore.Qt.Vertical)

        self.splitter = QtGui.QSplitter(self.splitter2)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.displaywidget = imageDisplayWidget.ImageDisplayWidget(
            parent=self.splitter)

        self.cutPlot = _pg.PlotWidget(self.splitter)
        self.cutPlot.setMinimumSize(QtCore.QSize(0, 120))
        self.cutCurve = self.cutPlot.plot()

        self.splitter.setStretchFactor(0, 20)
        self.splitter.setStretchFactor(1, 1)

        self.pixelComboBox = QtGui.QComboBox()
        self.pixelComboBox.addItem("Intensity")
        self.pixelComboBox.addItem("ROI")
        self.pixelComboBox.addItem("LineCut")
        self.pixelComboBox.addItem("Angle/Q")
        self.pixelComboBox.setStyleSheet("font: bold;")
        self.pixelComboBox.setToolTip(
            "select the image tool for the mouse pointer,"
            " i.e. Intensity, ROI, LineCut, Angle/Q")

        pixelvaluelayout = QtGui.QHBoxLayout()
        pixelvaluelayout2 = QtGui.QHBoxLayout()
        pixelvlayout = QtGui.QVBoxLayout()

        self.pixellabel = QtGui.QLabel("Pixel position and intensity: ")
        self.pixellabel.setToolTip(
            "coordinate info display for the mouse pointer")

        self.infoLineEdit = QtGui.QLineEdit()
        self.infoLineEdit.setReadOnly(True)
        self.infoLineEdit.setToolTip(
            "coordinate info display for the mouse pointer")

        self.ticksPushButton = QtGui.QPushButton("Axes ...")

        self.infoLabel = QtGui.QLabel("[x1, y1, x2, y2], sum: ")
        self.infoLabel.setToolTip(
            "coordinate info display for the mouse pointer")
        self.labelROILineEdit = QtGui.QLineEdit("")
        self.labelROILineEdit.setToolTip(
            "ROI alias or aliases related to Sardana Pool "
            "experimental channels")
        self.roiSpinBox = QtGui.QSpinBox()
        self.roiSpinBox.setMinimum(-1)
        self.roiSpinBox.setValue(1)
        self.roiSpinBox.setToolTip(
            "number of ROIs to add, -1 means remove ROI aliases from sardana")
        self.cutSpinBox = QtGui.QSpinBox()
        self.cutSpinBox.setMinimum(0)
        self.cutSpinBox.setValue(1)
        self.cutSpinBox.setToolTip(
            "number of Line Cuts")
        self.fetchROIButton = QtGui.QPushButton("Fetch")
        self.fetchROIButton.setToolTip(
            "fetch ROI aliases from the Door environment")
        self.applyROIButton = QtGui.QPushButton("Add")
        self.applyROIButton.setToolTip(
            "add ROI aliases to the Door environment "
            "as well as to Active MntGrp")

        self.angleqPushButton = QtGui.QPushButton("Geometry ...")
        self.angleqPushButton.setToolTip("Input physical parameters")
        self.angleqComboBox = QtGui.QComboBox()
        self.angleqComboBox.addItem("angles")
        self.angleqComboBox.addItem("q-space")
        self.angleqComboBox.setToolTip("Select the display space")

        pixelvaluelayout.addWidget(self.pixellabel)
        pixelvaluelayout.addWidget(self.labelROILineEdit)
        pixelvaluelayout.addWidget(self.roiSpinBox)
        pixelvaluelayout.addWidget(self.cutSpinBox)
        pixelvaluelayout.addWidget(self.applyROIButton)
        pixelvaluelayout.addWidget(self.fetchROIButton)
        pixelvaluelayout.addWidget(self.angleqPushButton)
        pixelvaluelayout.addWidget(self.angleqComboBox)
        pixelvaluelayout.addWidget(self.ticksPushButton)

        pixelvaluelayout2 = QtGui.QHBoxLayout()
        pixelvaluelayout2.addWidget(self.infoLabel)
        pixelvaluelayout2.addWidget(self.infoLineEdit)
        pixelvaluelayout2.addWidget(self.pixelComboBox)

        pixelvlayout.addLayout(pixelvaluelayout)
        pixelvlayout.addLayout(pixelvaluelayout2)
        spacerItem = QtGui.QSpacerItem(
            0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        pixelvlayout.addItem(spacerItem)
        frame = QtGui.QFrame(self.splitter2)
        frame.setLayout(pixelvlayout)

        self.splitter2.setStretchFactor(0, 100)
        self.splitter2.setStretchFactor(1, 1)

        verticallayout.addWidget(self.splitter2)

        self.setLayout(verticallayout)
        self.displaywidget.currentMousePosition.connect(self.setDisplayedText)

        self.roiregionmapper.mapped.connect(self.roiRegionChanged)
        self.currentroimapper.mapped.connect(self.currentROIChanged)
        self.displaywidget.roi[0].sigHoverEvent.connect(
            self.currentroimapper.map)
        self.displaywidget.roi[0].sigRegionChanged.connect(
            self.roiregionmapper.map)
        self.currentroimapper.setMapping(self.displaywidget.roi[0], 0)
        self.roiregionmapper.setMapping(self.displaywidget.roi[0], 0)

        self.cutCoordsChanged.connect(self.plotCut)
        self.roiSpinBox.valueChanged.connect(self.roiNrChanged)
        self.labelROILineEdit.textEdited.connect(self.updateROIButton)
        self.updateROIButton()

        self.cutregionmapper.mapped.connect(self.cutRegionChanged)
        self.currentcutmapper.mapped.connect(self.currentCutChanged)
        self.displaywidget.cut[0].sigHoverEvent.connect(
            self.currentcutmapper.map)
        self.displaywidget.cut[0].sigRegionChanged.connect(
            self.cutregionmapper.map)
        self.currentcutmapper.setMapping(self.displaywidget.cut[0], 0)
        self.cutregionmapper.setMapping(self.displaywidget.cut[0], 0)
        self.angleqPushButton.clicked.connect(self.geometry)
        self.angleqComboBox.currentIndexChanged.connect(
            self.onAngleQChanged)
        self.displaywidget.centerAngleChanged.connect(self.updateGeometry)
        self.cutSpinBox.valueChanged.connect(self.cutNrChanged)

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
        self.pixellabel.setToolTip(
            "coordinate info display for the mouse pointer\n%s" % message)
        self.infoLineEdit.setToolTip(
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
        while rid > len(self.displaywidget.roi):
            if coords and len(coords) >= len(self.displaywidget.roi):
                self.displaywidget.addROI(coords[len(self.displaywidget.roi)])
            else:
                self.displaywidget.addROI()
            self.displaywidget.roi[-1].sigHoverEvent.connect(
                self.currentroimapper.map)
            self.displaywidget.roi[-1].sigRegionChanged.connect(
                self.roiregionmapper.map)
            self.currentroimapper.setMapping(
                self.displaywidget.roi[-1],
                len(self.displaywidget.roi) - 1)
            self.roiregionmapper.setMapping(
                self.displaywidget.roi[-1],
                len(self.displaywidget.roi) - 1)
        if rid <= 0:
            self.displaywidget.currentroi = -1
        elif self.displaywidget.currentroi >= rid:
            self.displaywidget.currentroi = 0
        while max(rid, 0) < len(self.displaywidget.roi):
            self.currentroimapper.removeMappings(self.displaywidget.roi[-1])
            self.roiregionmapper.removeMappings(self.displaywidget.roi[-1])
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
        while cid > len(self.displaywidget.cut):
            if coords and len(coords) >= len(self.displaywidget.cut):
                self.displaywidget.addCut(coords[len(self.displaywidget.cut)])
            else:
                self.displaywidget.addCut()
            self.displaywidget.cut[-1].sigHoverEvent.connect(
                self.currentcutmapper.map)
            self.displaywidget.cut[-1].sigRegionChanged.connect(
                self.cutregionmapper.map)
            self.currentcutmapper.setMapping(
                self.displaywidget.cut[-1],
                len(self.displaywidget.cut) - 1)
            self.cutregionmapper.setMapping(
                self.displaywidget.cut[-1],
                len(self.displaywidget.cut) - 1)
        if cid <= 0:
            self.displaywidget.currentcut = -1
        elif self.displaywidget.currentcut >= cid:
            self.displaywidget.currentcut = 0
        while max(cid, 0) < len(self.displaywidget.cut):
            self.currentcutmapper.removeMappings(self.displaywidget.cut[-1])
            self.cutregionmapper.removeMappings(self.displaywidget.cut[-1])
            self.displaywidget.removeCut()
        self.cutCoordsChanged.emit()
        self.cutSpinBox.setValue(cid)

    def onPixelChanged(self, text):
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

    def roiChanged(self):
        try:
            rid = self.displaywidget.currentroi
            state = self.displaywidget.roi[rid].state
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
                self.displaywidget.cut[cid].getCoordinates()
            self.cutCoordsChanged.emit()
        except Exception as e:
            print("Warning: %s" % str(e))

    def showROIFrame(self):
        self.displaywidget.vLine.hide()
        self.displaywidget.hLine.hide()
        self.ticksPushButton.hide()
        self.angleqPushButton.hide()
        self.angleqComboBox.hide()
        self.cutPlot.hide()
        self.fetchROIButton.show()
        self.applyROIButton.show()
        self.roiSpinBox.show()
        self.cutSpinBox.hide()
        self.labelROILineEdit.show()

        self.pixellabel.setText("ROI alias(es): ")
        self.infoLabel.show()
        for roi in self.displaywidget.roi:
            roi.show()
        for cut in self.displaywidget.cut:
            cut.hide()
        doreset = not (self.displaywidget.cutenable or
                       self.displaywidget.roienable or
                       self.displaywidget.qenable)
        self.displaywidget.cutenable = False
        self.displaywidget.roienable = True
        self.displaywidget.qenable = False
        if self.displaywidget.roi:
            self.displaywidget.roi[0].show()
        self.infoLineEdit.setText("")
        self.infoLineEdit.setToolTip(
            "coordinate info display for the mouse pointer")
        self.pixellabel.setToolTip(
            "ROI alias or aliases related to sardana experimental channels")
        if doreset:
            self.displaywidget.resetScale()

    def showIntensityFrame(self):
        self.pixellabel.setText("Pixel position and intensity: ")
        for roi in self.displaywidget.roi:
            roi.hide()
        for cut in self.displaywidget.cut:
            cut.hide()
        self.cutPlot.hide()
        self.ticksPushButton.show()
        self.angleqPushButton.hide()
        self.angleqComboBox.hide()
        self.fetchROIButton.hide()
        self.labelROILineEdit.hide()
        self.applyROIButton.hide()
        self.roiSpinBox.hide()
        self.cutSpinBox.hide()
        self.infoLabel.hide()
        self.displaywidget.roienable = False
        self.displaywidget.cutenable = False
        self.displaywidget.qenable = False
        self.displaywidget.vLine.show()
        self.displaywidget.hLine.show()
        self.infoLineEdit.setText("")
        self.infoLineEdit.setToolTip(
            "coordinate info display for the mouse pointer")
        self.pixellabel.setToolTip(
            "coordinate info display for the mouse pointer")
        self.displaywidget.setScale(
            self.displaywidget.position, self.displaywidget.scale)

    def showLineCutFrame(self):
        self.pixellabel.setText("Cut, pixel position and intensity: ")
        for roi in self.displaywidget.roi:
            roi.hide()
        for cut in self.displaywidget.cut:
            cut.show()
        self.cutPlot.show()
        self.fetchROIButton.hide()
        self.ticksPushButton.hide()
        self.angleqPushButton.hide()
        self.angleqComboBox.hide()
        self.labelROILineEdit.hide()
        self.applyROIButton.hide()
        self.cutSpinBox.show()
        self.roiSpinBox.hide()
        self.infoLabel.hide()
        doreset = not (self.displaywidget.cutenable or
                       self.displaywidget.roienable or
                       self.displaywidget.qenable)
        self.displaywidget.roienable = False
        self.displaywidget.cutenable = True
        self.displaywidget.qenable = False
        self.displaywidget.vLine.hide()
        self.displaywidget.hLine.hide()
        self.infoLineEdit.setText("")
        self.infoLineEdit.setToolTip(
            "coordinate info display for the mouse pointer")
        self.pixellabel.setToolTip(
            "coordinate info display for the mouse pointer")
        if doreset:
            self.displaywidget.resetScale()

    def showAngleQFrame(self):
        self.pixellabel.setText("Pixel position and intensity: ")
        for roi in self.displaywidget.roi:
            roi.hide()
        for cut in self.displaywidget.cut:
            cut.hide()
        self.cutPlot.hide()
        self.ticksPushButton.hide()
        self.angleqPushButton.show()
        self.angleqComboBox.show()
        self.fetchROIButton.hide()
        self.labelROILineEdit.hide()
        self.applyROIButton.hide()
        self.roiSpinBox.hide()
        self.cutSpinBox.hide()
        self.infoLabel.hide()
        doreset = not (self.displaywidget.cutenable or
                       self.displaywidget.roienable or
                       self.displaywidget.qenable)
        self.displaywidget.roienable = False
        self.displaywidget.cutenable = False
        self.displaywidget.qenable = True
        self.displaywidget.vLine.show()
        self.displaywidget.hLine.show()
        self.infoLineEdit.setText("")
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
        if cid > -1 and len(self.displaywidget.cut) > cid:
            cut = self.displaywidget.cut[cid]
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
        if self.displaywidget.roienable and self.displaywidget.roi:
            roiVal, currentroi = self.calcROIsum()
            roilabel = self.createROILabel()

            text = "%s, %s = %s" % (text, roilabel, roiVal)
        self.infoLineEdit.setText(text)

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
