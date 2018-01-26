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

import pyqtgraph as pg
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
        filenamelayout = QtGui.QHBoxLayout()

        filelabel = QtGui.QLabel("Image/File name: ")
        filelabel.setToolTip("image or/and file name")

        filenamelayout.addWidget(filelabel)
        self.filenamedisplay = QtGui.QLineEdit()
        self.filenamedisplay.setReadOnly(True)
        self.filenamedisplay.setToolTip("image or/and file name")
        filenamelayout.addWidget(self.filenamedisplay)
        # self.buttonBox = QtGui.QDialogButtonBox()
        # self.quitButton  = self.buttonBox.addButton(
        #        QtGui.QDialogButtonBox.Close)
        # self.quitButton.setText("&Quit")
        self.quitButton = QtGui.QPushButton("&Quit")
        self.quitButton.setToolTip("quit the image viewer")
        self.cnfButton = QtGui.QPushButton("Configuration")
        self.cnfButton.setToolTip("image viewer configuration")
        self.loadButton = QtGui.QPushButton("Load ...")
        self.loadButton.setToolTip("load an image from a file")
        # self.buttonBox.addButton(self.cnfButton,
        #          QtGui.QDialogButtonBox.ActionRole)
        filenamelayout.addWidget(self.loadButton)
        filenamelayout.addWidget(self.cnfButton)
        filenamelayout.addWidget(self.quitButton)
        # filenamelayout.addWidget(self.buttonBox)
        verticallayout.addLayout(filenamelayout)

        self.splitter = QtGui.QSplitter(self)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.img_widget = imageDisplayWidget.ImageDisplayWidget(
            parent=self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,
                                       QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(15)
        sizePolicy.setHeightForWidth(
            self.img_widget.sizePolicy().hasHeightForWidth())
        self.img_widget.setSizePolicy(sizePolicy)

        self.cutPlot = pg.PlotWidget(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,
                                       QtGui.QSizePolicy.Preferred)
        self.cutCurve = self.cutPlot.plot()
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(
            self.cutPlot.sizePolicy().hasHeightForWidth())
        self.cutPlot.setSizePolicy(sizePolicy)
        self.cutPlot.setMinimumSize(QtCore.QSize(0, 120))

        verticallayout.addWidget(self.splitter)

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
        self.pixellabel = QtGui.QLabel("Pixel position and intensity: ")
        self.pixellabel.setToolTip(
            "coordinate info display for the mouse pointer")

        self.infodisplay = QtGui.QLineEdit()
        self.infodisplay.setReadOnly(True)
        self.infodisplay.setToolTip(
            "coordinate info display for the mouse pointer")

        self.ticksPushButton = QtGui.QPushButton("Axes ...")

        self.roiLabel = QtGui.QLabel("[x1, y1, x2, y2], sum: ")
        self.roiLabel.setToolTip(
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
        pixelvaluelayout2.addWidget(self.roiLabel)
        pixelvaluelayout2.addWidget(self.infodisplay)
        pixelvaluelayout2.addWidget(self.pixelComboBox)

        verticallayout.addLayout(pixelvaluelayout)
        verticallayout.addLayout(pixelvaluelayout2)

        self.setLayout(verticallayout)
        self.img_widget.currentMousePosition.connect(self.setDisplayedText)

        self.roiregionmapper.mapped.connect(self.roiRegionChanged)
        self.currentroimapper.mapped.connect(self.currentROIChanged)
        self.img_widget.roi[0].sigHoverEvent.connect(self.currentroimapper.map)
        self.img_widget.roi[0].sigRegionChanged.connect(
            self.roiregionmapper.map)
        self.currentroimapper.setMapping(self.img_widget.roi[0], 0)
        self.roiregionmapper.setMapping(self.img_widget.roi[0], 0)

        self.cutCoordsChanged.connect(self.plotCut)
        self.roiSpinBox.valueChanged.connect(self.roiNrChanged)
        self.labelROILineEdit.textEdited.connect(self.updateROIButton)
        self.updateROIButton()

        self.cutregionmapper.mapped.connect(self.cutRegionChanged)
        self.currentcutmapper.mapped.connect(self.currentCutChanged)
        self.img_widget.cut[0].sigHoverEvent.connect(self.currentcutmapper.map)
        self.img_widget.cut[0].sigRegionChanged.connect(
            self.cutregionmapper.map)
        self.currentcutmapper.setMapping(self.img_widget.cut[0], 0)
        self.cutregionmapper.setMapping(self.img_widget.cut[0], 0)
        self.angleqPushButton.clicked.connect(self.geometry)
        self.angleqComboBox.currentIndexChanged.connect(
            self.onAngleQChanged)
        self.img_widget.centerAngleChanged.connect(self.updateGeometry)
        self.cutSpinBox.valueChanged.connect(self.cutNrChanged)

    @QtCore.pyqtSlot(int)
    def onAngleQChanged(self, gindex):
        self.img_widget.gspaceindex = gindex

    @QtCore.pyqtSlot()
    def geometry(self):
        cnfdlg = geometryDialog.GeometryDialog(self)
        cnfdlg.centerx = self.img_widget.centerx
        cnfdlg.centery = self.img_widget.centery
        cnfdlg.energy = self.img_widget.energy
        cnfdlg.pixelsizex = self.img_widget.pixelsizex
        cnfdlg.pixelsizey = self.img_widget.pixelsizey
        cnfdlg.detdistance = self.img_widget.detdistance
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.img_widget.centerx = cnfdlg.centerx
            self.img_widget.centery = cnfdlg.centery
            self.img_widget.energy = cnfdlg.energy
            self.img_widget.pixelsizex = cnfdlg.pixelsizex
            self.img_widget.pixelsizey = cnfdlg.pixelsizey
            self.img_widget.detdistance = cnfdlg.detdistance
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
                      self.img_widget.centerx,
                      self.img_widget.centery,
                      self.img_widget.pixelsizex,
                      self.img_widget.pixelsizey,
                      self.img_widget.detdistance,
                      self.img_widget.energy
                  )
        self.angleqPushButton.setToolTip(
            "Input physical parameters\n%s" % message)
        self.angleqComboBox.setToolTip(
            "Select the display space\n%s" % message)
        self.pixellabel.setToolTip(
            "coordinate info display for the mouse pointer\n%s" % message)
        self.infodisplay.setToolTip(
            "coordinate info display for the mouse pointer\n%s" % message)

    def updateMetaData(self, axisscales=None, axislabels=None):
        if axislabels is not None:
            self.img_widget.xtext = str(axislabels[0]) \
                if axislabels[0] is not None else None
            self.img_widget.ytext = str(axislabels[1]) \
                if axislabels[0] is not None else None
            self.img_widget.xunits = str(axislabels[2]) \
                if axislabels[0] is not None else None
            self.img_widget.yunits = str(axislabels[3]) \
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
        self.img_widget.setScale(
            position, scale,
            not self.img_widget.roienable
            and not self.img_widget.cutenable
            and not self.img_widget.qenable)

    @QtCore.pyqtSlot(int)
    def roiRegionChanged(self, _):
        self.roiChanged()

    @QtCore.pyqtSlot(int)
    def cutRegionChanged(self, cid):
        self.cutChanged()

    @QtCore.pyqtSlot(int)
    def currentROIChanged(self, rid):
        oldrid = self.img_widget.currentroi
        if rid != oldrid:
            self.img_widget.currentroi = rid
            self.roiCoordsChanged.emit()

    @QtCore.pyqtSlot(int)
    def currentCutChanged(self, cid):
        oldcid = self.img_widget.currentcut
        if cid != oldcid:
            self.img_widget.currentcut = cid
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
            for i, crd in enumerate(self.img_widget.roi):
                if i < len(coords):
                    self.img_widget.roicoords[i] = coords[i]
                    crd.setPos([coords[i][0], coords[i][1]])
                    crd.setSize(
                        [coords[i][2] - coords[i][0],
                         coords[i][3] - coords[i][1]])
        while rid > len(self.img_widget.roi):
            if coords and len(coords) >= len(self.img_widget.roi):
                self.img_widget.addROI(coords[len(self.img_widget.roi)])
            else:
                self.img_widget.addROI()
            self.img_widget.roi[-1].sigHoverEvent.connect(
                self.currentroimapper.map)
            self.img_widget.roi[-1].sigRegionChanged.connect(
                self.roiregionmapper.map)
            self.currentroimapper.setMapping(
                self.img_widget.roi[-1],
                len(self.img_widget.roi) - 1)
            self.roiregionmapper.setMapping(
                self.img_widget.roi[-1],
                len(self.img_widget.roi) - 1)
        if rid <= 0:
            self.img_widget.currentroi = -1
        elif self.img_widget.currentroi >= rid:
            self.img_widget.currentroi = 0
        while max(rid, 0) < len(self.img_widget.roi):
            self.currentroimapper.removeMappings(self.img_widget.roi[-1])
            self.roiregionmapper.removeMappings(self.img_widget.roi[-1])
            self.img_widget.removeROI()
        self.roiCoordsChanged.emit()
        self.roiSpinBox.setValue(rid)

    @QtCore.pyqtSlot(int)
    def cutNrChanged(self, cid, coords=None):
        if coords:
            for i, crd in enumerate(self.img_widget.cut):
                if i < len(coords):
                    self.img_widget.cutcoords[i] = coords[i]
                    crd.setPos([coords[i][0], coords[i][1]])
                    crd.setSize(
                        [coords[i][2] - coords[i][0],
                         coords[i][3] - coords[i][1]])
        while cid > len(self.img_widget.cut):
            if coords and len(coords) >= len(self.img_widget.cut):
                self.img_widget.addCut(coords[len(self.img_widget.cut)])
            else:
                self.img_widget.addCut()
            self.img_widget.cut[-1].sigHoverEvent.connect(
                self.currentcutmapper.map)
            self.img_widget.cut[-1].sigRegionChanged.connect(
                self.cutregionmapper.map)
            self.currentcutmapper.setMapping(
                self.img_widget.cut[-1],
                len(self.img_widget.cut) - 1)
            self.cutregionmapper.setMapping(
                self.img_widget.cut[-1],
                len(self.img_widget.cut) - 1)
        if cid <= 0:
            self.img_widget.currentcut = -1
        elif self.img_widget.currentcut >= cid:
            self.img_widget.currentcut = 0
        while max(cid, 0) < len(self.img_widget.cut):
            self.currentcutmapper.removeMappings(self.img_widget.cut[-1])
            self.cutregionmapper.removeMappings(self.img_widget.cut[-1])
            self.img_widget.removeCut()
        self.cutCoordsChanged.emit()
        self.cutSpinBox.setValue(cid)

    def roiChanged(self):
        try:
            rid = self.img_widget.currentroi
            state = self.img_widget.roi[rid].state
            ptx = int(math.floor(state['pos'].x()))
            pty = int(math.floor(state['pos'].y()))
            szx = int(math.floor(state['size'].x()))
            szy = int(math.floor(state['size'].y()))
            self.img_widget.roicoords[rid] = [ptx, pty, ptx + szx, pty + szy]
            self.roiCoordsChanged.emit()
        except Exception as e:
            print("Warning: %s" % str(e))

    def cutChanged(self):
        try:
            cid = self.img_widget.currentcut
            self.img_widget.cutcoords[cid] = \
                self.img_widget.cut[cid].getCoordinates()
            self.cutCoordsChanged.emit()
        except Exception as e:
            print("Warning: %s" % str(e))

    def showROIFrame(self):
        self.img_widget.vLine.hide()
        self.img_widget.hLine.hide()
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
        self.roiLabel.show()
        for roi in self.img_widget.roi:
            roi.show()
        for cut in self.img_widget.cut:
            cut.hide()
        doreset = not (self.img_widget.cutenable or
                       self.img_widget.roienable or
                       self.img_widget.qenable)
        self.img_widget.cutenable = False
        self.img_widget.roienable = True
        self.img_widget.qenable = False
        if self.img_widget.roi:
            self.img_widget.roi[0].show()
        self.infodisplay.setText("")
        self.infodisplay.setToolTip(
            "coordinate info display for the mouse pointer")
        self.pixellabel.setToolTip(
            "ROI alias or aliases related to sardana experimental channels")
        if doreset:
            self.img_widget.resetScale()

    def showIntensityFrame(self):
        self.pixellabel.setText("Pixel position and intensity: ")
        for roi in self.img_widget.roi:
            roi.hide()
        for cut in self.img_widget.cut:
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
        self.roiLabel.hide()
        self.img_widget.roienable = False
        self.img_widget.cutenable = False
        self.img_widget.qenable = False
        self.img_widget.vLine.show()
        self.img_widget.hLine.show()
        self.infodisplay.setText("")
        self.infodisplay.setToolTip(
            "coordinate info display for the mouse pointer")
        self.pixellabel.setToolTip(
            "coordinate info display for the mouse pointer")
        self.img_widget.setScale(
            self.img_widget.position, self.img_widget.scale)

    def showLineCutFrame(self):
        self.pixellabel.setText("Cut, pixel position and intensity: ")
        for roi in self.img_widget.roi:
            roi.hide()
        for cut in self.img_widget.cut:
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
        self.roiLabel.hide()
        doreset = not (self.img_widget.cutenable or
                       self.img_widget.roienable or
                       self.img_widget.qenable)
        self.img_widget.roienable = False
        self.img_widget.cutenable = True
        self.img_widget.qenable = False
        self.img_widget.vLine.hide()
        self.img_widget.hLine.hide()
        self.infodisplay.setText("")
        self.infodisplay.setToolTip(
            "coordinate info display for the mouse pointer")
        self.pixellabel.setToolTip(
            "coordinate info display for the mouse pointer")
        if doreset:
            self.img_widget.resetScale()

    def showAngleQFrame(self):
        self.pixellabel.setText("Pixel position and intensity: ")
        for roi in self.img_widget.roi:
            roi.hide()
        for cut in self.img_widget.cut:
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
        self.roiLabel.hide()
        doreset = not (self.img_widget.cutenable or
                       self.img_widget.roienable or
                       self.img_widget.qenable)
        self.img_widget.roienable = False
        self.img_widget.cutenable = False
        self.img_widget.qenable = True
        self.img_widget.vLine.show()
        self.img_widget.hLine.show()
        self.infodisplay.setText("")
        self.updateGeometryTip()
        if doreset:
            self.img_widget.resetScale()

    def plot(self, array, name=None, rawarray=None):
        if array is None:
            return
        if rawarray is None:
            rawarray = array
        if name is not None:
            self.filenamedisplay.setText(name)

        self.img_widget.updateImage(array, rawarray)
        if self.img_widget.cutenable:
            self.plotCut()
        if self.img_widget.roienable:
            self.setDisplayedText()

    def createROILabel(self):
        roilabel = ""
        currentroi = self.img_widget.currentroi
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
        rid = self.img_widget.currentroi
        image = None
        if self.img_widget.rawdata is not None:
            image = self.img_widget.rawdata
        if image is not None:
            if self.img_widget.roienable:
                if rid >= 0:
                    roicoords = self.img_widget.roicoords
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
        cid = self.img_widget.currentcut
        if cid > -1 and len(self.img_widget.cut) > cid:
            cut = self.img_widget.cut[cid]
            if self.img_widget.rawdata is not None:
                dt = cut.getArrayRegion(
                    self.img_widget.rawdata,
                    self.img_widget.image, axes=(0, 1))
                while dt.ndim > 1:
                    dt = dt.mean(axis=1)
                self.cutCurve.setData(y=dt)
                self.cutPlot.setVisible(True)
                self.cutCurve.setVisible(True)
                return
        self.cutCurve.setVisible(False)

    @QtCore.pyqtSlot(int)
    def setAutoLevels(self, autoLvls):
        self.img_widget.setAutoLevels(autoLvls)

    @QtCore.pyqtSlot(float)
    def setMinLevel(self, level=None):
        self.img_widget.setDisplayMinLevel(level)

    @QtCore.pyqtSlot(float)
    def setMaxLevel(self, level=None):
        self.img_widget.setDisplayMaxLevel(level)

    @QtCore.pyqtSlot(str)
    def changeGradient(self, name):
        self.img_widget.updateGradient(name)

    @QtCore.pyqtSlot(str)
    def setDisplayedText(self, text=None):
        if text is not None:
            self.__lasttext = text
        else:
            text = self.__lasttext
        if self.img_widget.roienable and self.img_widget.roi:
            roiVal, currentroi = self.calcROIsum()
            roilabel = self.createROILabel()

            text = "%s, %s = %s" % (text, roilabel, roiVal)
        self.infodisplay.setText(text)

    def setTicks(self):
        cnfdlg = axesDialog.AxesDialog(self)
        if self.img_widget.position is None:
            cnfdlg.xposition = None
            cnfdlg.yposition = None
        else:
            cnfdlg.xposition = self.img_widget.position[0]
            cnfdlg.yposition = self.img_widget.position[1]
        if self.img_widget.scale is None:
            cnfdlg.xscale = None
            cnfdlg.yscale = None
        else:
            cnfdlg.xscale = self.img_widget.scale[0]
            cnfdlg.yscale = self.img_widget.scale[1]

        cnfdlg.xtext = self.img_widget.xtext
        cnfdlg.ytext = self.img_widget.ytext

        cnfdlg.xunits = self.img_widget.xunits
        cnfdlg.yunits = self.img_widget.yunits

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
            self.img_widget.xtext = cnfdlg.xtext or None
            self.img_widget.ytext = cnfdlg.ytext or None

            self.img_widget.xunits = cnfdlg.xunits or None
            self.img_widget.yunits = cnfdlg.yunits or None
            self.img_widget.setScale(position, scale)
            return True
        return False
