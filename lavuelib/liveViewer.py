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


""" live viewer image display base it on a qt dialog """

from __future__ import print_function
from __future__ import unicode_literals

import time
import json
import re
import numpy as np
import os
import zmq

from PyQt4 import QtCore, QtGui

from . import imageSource as hcs
from . import messageBox

from . import sourceWidget
from . import preparationBoxWidget
from . import scalingGroupBox
from . import levelsGroupBox
from . import statisticsGroupBox
from . import imageWidget
from . import configDialog

from . import imageFileHandler
from . import sardanaUtils
from . import dataFetchThread

try:
    from .hidraServerList import HidraServerList
except:
    print("Cannot read the list of HiDRA servers.")
    print("Alternate method not yet implemented.")


class LiveViewer(QtGui.QDialog):

    '''The master class for the dialog, contains all other
    widget and handles communication.'''
    update_state = QtCore.pyqtSignal(int)

    def __init__(self, umode=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.sourcetypes = []
        if hcs.HIDRA:
            self.sourcetypes.append(
                {"name": "Hidra",
                 "datasource": "HiDRASource",
                 "slot": "updateHidraButton",
                 "hidden": ["attrLabel", "attrLineEdit",
                            "fileLabel", "fileLineEdit",
                            "dirLabel", "dirLineEdit",
                            "httpLabel", "httpLineEdit",
                            "pickleTopicLabel", "pickleTopicComboBox",
                            "pickleLabel", "pickleLineEdit"]}
            )
        self.sourcetypes.append(
            {"name": "HTTP response",
             "datasource": "HTTPSource",
             "slot": "updateHTTPButton",
             "hidden": ["hostlabel", "currenthost",
                        "serverLabel", "serverlistBox",
                        "fileLabel", "fileLineEdit",
                        "dirLabel", "dirLineEdit",
                        "pickleLabel", "pickleLineEdit",
                        "pickleTopicLabel", "pickleTopicComboBox",
                        "attrLabel", "attrLineEdit"]},
        )
        if hcs.PYTANGO:
            self.sourcetypes.append(
                {"name": "Tango Attribute",
                 "datasource": "TangoAttrSource",
                 "slot": "updateAttrButton",
                 "hidden": ["hostlabel", "currenthost",
                            "fileLabel", "fileLineEdit",
                            "dirLabel", "dirLineEdit",
                            "pickleLabel", "pickleLineEdit",
                            "httpLabel", "httpLineEdit",
                            "pickleTopicLabel", "pickleTopicComboBox",
                            "serverLabel", "serverlistBox"]})

        if hcs.PYTANGO:
            self.sourcetypes.append(
                {"name": "Tango File",
                 "datasource": "TangoFileSource",
                 "slot": "updateFileButton",
                 "hidden": ["hostlabel", "currenthost",
                            "httpLabel", "httpLineEdit",
                            "pickleLabel", "pickleLineEdit",
                            "pickleTopicLabel", "pickleTopicComboBox",
                            "attrLabel", "attrLineEdit",
                            "serverLabel", "serverlistBox"]})

        self.sourcetypes.append(
            {"name": "ZMQ Stream",
             "datasource": "ZMQPickleSource",
             "slot": "updateZMQPickleButton",
             "hidden": ["hostlabel", "currenthost",
                        "fileLabel", "fileLineEdit",
                        "dirLabel", "dirLineEdit",
                        "serverLabel", "serverlistBox",
                        "httpLabel", "httpLineEdit",
                        "attrLabel", "attrLineEdit"]},
        )
        self.sourcetypes.append(
            {"name": "Test",
             "datasource": "GeneralSource",
             "slot": "updateButton",
             "hidden": ["hostlabel", "currenthost",
                        "httpLabel", "httpLineEdit",
                        "fileLabel", "fileLineEdit",
                        "dirLabel", "dirLineEdit",
                        "serverLabel", "serverlistBox",
                        "pickleLabel", "pickleLineEdit",
                        "pickleTopicLabel", "pickleTopicComboBox",
                        "attrLabel", "attrLineEdit"]},
        )

        self.doorname = ""
        self.addrois = True
        self.secstream = False
        self.secautoport = True
        self.secsockopt = ""
        self.secport = "5657"
        self.timeout = 3000
        if umode and umode.lower() in ["expert"]:
            self.umode = "expert"
        else:
            self.umode = "user"
        self.showhisto = True
        self.showmask = False
        self.updatehisto = False
        self.interruptonerror = True
        self.aspectlocked = False
        self.seccontext = zmq.Context()
        self.secsocket = self.seccontext.socket(zmq.PUB)
        self.apppid = os.getpid()
        self.imagename = None
        self.statswoscaling = False
        self.zmqtopics = []
        self.autozmqtopics = False
        self.dirtrans = '{"/ramdisk/": "/gpfs/"}'
        self.__allowedmdata = ["datasources"]
        self.__allowedwgdata = ["axisscales", "axislabels"]

        # note: host and target are defined in another place
        self.data_source = hcs.GeneralSource()

        # WIDGET DEFINITIONS
        # instantiate the widgets and declare the parent
        self.sourceW = sourceWidget.SourceWidget(parent=self)
        self.sourceW.serverdict = HidraServerList
        self.prepBoxW = preparationBoxWidget.PreparationBoxWidget(parent=self)
        self.scalingW = scalingGroupBox.ScalingGroupBox(parent=self)
        self.levelsW = levelsGroupBox.LevelsGroupBox(parent=self)
        self.statsW = statisticsGroupBox.StatisticsGroupBox(parent=self)
        self.imageW = imageWidget.ImageWidget(parent=self)
        self.levelsW.setImageItem(self.imageW.img_widget.image)
        self.levelsW.imageChanged(autoLevel=True)

        self.maskW = self.prepBoxW.maskW
        self.bkgSubW = self.prepBoxW.bkgSubW
        self.trafoW = self.prepBoxW.trafoW

        # keep a reference to the "raw" image and the current filename
        self.raw_image = None
        self.rawgrey_image = None
        self.image_name = None
        self.metadata = ""
        self.display_image = None
        self.scaled_image = None

        self.background_image = None
        self.doBkgSubtraction = False

        self.mask_image = None
        self.maskIndices = None
        self.applyImageMask = False

        self._signalhost = None

        self.trafoName = "None"

        # LAYOUT DEFINITIONS
        # the dialog layout is side by side
        globallayout = QtGui.QHBoxLayout()

        # define left hand side layout: vertical
        vlayout = QtGui.QVBoxLayout()

        # place widgets on the layouts
        # first the vertical layout on the left side

        # first element is supposed to be tabbed:
        vlayout.addWidget(self.sourceW)
        vlayout.addWidget(self.prepBoxW)
        vlayout.addWidget(self.scalingW)
        vlayout.addWidget(self.levelsW)
        # vlayout.addWidget(self.gradientW)
        vlayout.addWidget(self.statsW)

        # then the vertical layout on the --global-- horizontal one
        globallayout.addLayout(vlayout, 1)
        globallayout.addWidget(self.imageW, 10)

        self.setLayout(globallayout)
        self.setWindowTitle("laVue: Live Image Viewer")

        # SIGNAL LOGIC::

        # signal from intensity scaling widget:
        # self.scalingW.scalingChanged.connect(self.scale)
        self.scalingW.scalingChanged.connect(self.plot)
        self.scalingW.scalingChanged.connect(self.levelsW.setScalingLabel)

        # signal from limit setting widget
        self.levelsW.minLevelChanged.connect(self.imageW.setMinLevel)
        self.levelsW.maxLevelChanged.connect(self.imageW.setMaxLevel)
        self.levelsW.autoLevelsChanged.connect(self.imageW.setAutoLevels)
        self.levelsW.levelsChanged.connect(self.plot)
        self.levelsW.changeView(self.showhisto)
        self.imageW.cnfButton.clicked.connect(self.configuration)
        self.imageW.quitButton.clicked.connect(self.close)
        self.imageW.loadButton.clicked.connect(self.loadfile)
        if self.umode in ["user"]:
            self.imageW.cnfButton.hide()
        self.imageW.applyROIButton.clicked.connect(self.onapplyrois)
        self.imageW.fetchROIButton.clicked.connect(self.onfetchrois)
        self.imageW.roiCoordsChanged.connect(self.calc_update_stats_sec)
        self.imageW.pixelComboBox.currentIndexChanged.connect(
            self.onPixelChanged)
        # connecting signals from source widget:
        self.sourceW.source_connect.connect(self.connect_source)
        self.sourceW.source_connect.connect(self.startPlotting)

        self.sourceW.source_disconnect.connect(self.stopPlotting)
        self.sourceW.source_disconnect.connect(self.disconnect_source)

        # gradient selector
        self.levelsW.channelChanged.connect(self.plot)
        self.imageW.img_widget.setaspectlocked.triggered.connect(
            self.toggleAspectLocked)
        self.imageW.ticksPushButton.clicked.connect(self.setTicks)

        # simple mutable caching object for data exchange with thread
        self.exchangelist = dataFetchThread.ExchangeList()

        self.dataFetcher = dataFetchThread.DataFetchThread(
            self.data_source, self.exchangelist)
        self.dataFetcher.newDataName.connect(self.getNewData)
        # ugly !!! sent current state to the data fetcher...
        self.update_state.connect(self.dataFetcher.changeStatus)
        self.sourceW.source_state.connect(self.updateSource)

        self.bkgSubW.bkgFileSelection.connect(self.prepareBKGSubtraction)
        self.bkgSubW.useCurrentImageAsBKG.connect(self.setCurrentImageAsBKG)
        self.bkgSubW.applyBkgSubtractBox.stateChanged.connect(
            self.checkBKGSubtraction)
        self.maskW.maskFileSelection.connect(self.prepareMasking)
        self.maskW.applyMaskBox.stateChanged.connect(self.checkMasking)

        # signals from transformation widget
        self.trafoW.activatedTransformation.connect(self.assessTransformation)

        # set the right target name for the source display at initialization
        self.sourceW.setTargetName(self.data_source.getTarget())
        # self.sourceW.source_servername.connect(self.data_source.setSignalHost)
        self.sourceW.source_servername.connect(self.setSignalHost)
        self.onPixelChanged()

        settings = QtCore.QSettings()
        qstval = str(settings.value("Configuration/Sardana").toString())
        if qstval.lower() == "false":
            self.setSardana(False)
        else:
            self.setSardana(True)
        self.restoreGeometry(
            settings.value("Layout/Geometry").toByteArray())
        qstval = str(settings.value("Configuration/AddROIs").toString())
        if qstval.lower() == "false":
            self.addrois = False
        qstval = str(settings.value("Configuration/SecAutoPort").toString())
        if qstval.lower() == "false":
            self.secautoport = False

        qstval = str(settings.value("Configuration/ShowHistogram").toString())
        if qstval.lower() == "false":
            self.showhisto = False
        qstval = str(settings.value("Configuration/ShowMaskWidget").toString())
        if qstval.lower() == "true":
            self.showmask = True
        qstval = str(settings.value("Configuration/AspectLocked").toString())
        if qstval.lower() == "true":
            self.aspectlocked = True
            self.imageW.img_widget.setAspectLocked(self.aspectlocked)
        qstval = str(settings.value("Configuration/SecPort").toString())
        try:
            int(qstval)
            self.secport = str(qstval)
        except:
            pass
        qstval = str(settings.value("Configuration/SourceTimeout").toString())
        try:
            int(qstval)
            self.timeout = int(qstval)
            self.data_source.timeout = self.timeout
        except:
            pass
        qstval = str(settings.value("Configuration/SecStream").toString())
        if qstval.lower() == "true":
            try:
                if self.secautoport:
                    self.secsockopt = "tcp://*:*"
                    self.secsocket.bind(self.secsockopt)
                    self.secport = self.secsocket.getsockopt(
                        zmq.LAST_ENDPOINT).split(":")[-1]
                else:
                    self.secsockopt = "tcp://*:%s" % self.secport
                    self.secsocket.bind(self.secsockopt)
                self.secstream = True
            except:
                self.secstream = False
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "lavue: Cannot connect to: %s" % self.secsockopt)
                messageBox.MessageBox.warning(
                    self, "lavue: Cannot connect to: %s" % self.secsockopt,
                    text, str(value))

        try:
            dataFetchThread.GLOBALREFRESHRATE = float(
                settings.value("Configuration/RefreshRate").toString())
        except:
            pass

        qstval = str(
            settings.value("Configuration/InterruptOnError").toString())
        if qstval.lower() == "false":
            self.interruptonerror = False
        elif qstval.lower() == "true":
            self.interruptonerror = True
        qstval = str(
            settings.value("Configuration/LastImageFileName").toString())
        if qstval:
            self.imagename = qstval
        qstval = str(
            settings.value(
                "Configuration/StatisticsWithoutScaling").toString())
        if qstval.lower() == "true":
            self.statswoscaling = True
        self.imageW.img_widget.statswoscaling = self.statswoscaling

        qstval = \
            settings.value("Configuration/ZMQStreamTopics").toList()
        if qstval:
            self.zmqtopics = [str(tp.toString()) for tp in qstval]
        qstval = str(settings.value(
            "Configuration/AutoZMQStreamTopics").toString())
        if qstval.lower() == "true":
            self.autozmqtopics = True
        qstval = str(
            settings.value("Configuration/DirectoryTranslation").toString())
        if qstval:
            self.dirtrans = qstval

        self.sourceW.update(
            zmqtopics=self.zmqtopics, dirtrans=self.dirtrans,
            autozmqtopics=self.autozmqtopics)

        self.levelsW.changeView(self.showhisto)
        self.prepBoxW.changeView(self.showmask)
        self.plot()

    @QtCore.pyqtSlot(bool)
    def toggleAspectLocked(self, status):
        self.aspectlocked = status
        self.imageW.img_widget.setAspectLocked(self.aspectlocked)

    @QtCore.pyqtSlot(int)
    def onPixelChanged(self):
        text = self.imageW.pixelComboBox.currentText()
        if text == "ROI":
            self.imageW.showROIFrame()
            self.trafoName = "None"
            self.trafoW.cb.setCurrentIndex(0)
            self.trafoW.cb.setEnabled(False)
            self.imageW.roiChanged()
        elif text == "LineCut":
            self.imageW.showLineCutFrame()
            self.trafoW.cb.setEnabled(True)
            self.imageW.roiCoordsChanged.emit()
        elif text == "Angle/Q":
            self.imageW.showAngleQFrame()
            self.trafoW.cb.setEnabled(True)
            self.imageW.roiCoordsChanged.emit()
        else:
            self.imageW.showIntensityFrame()
            self.trafoW.cb.setEnabled(True)
            self.imageW.roiCoordsChanged.emit()

    @QtCore.pyqtSlot()
    def onapplyrois(self):
        if hcs.PYTANGO:
            roicoords = self.imageW.img_widget.roicoords
            roispin = self.imageW.roiSpinBox.value()
            if not self.doorname:
                self.doorname = self.sardana.getDeviceName("Door")
            try:
                rois = json.loads(self.sardana.getScanEnv(
                    str(self.doorname), ["DetectorROIs"]))
            except Exception:
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "Problems in connecting to Door or MacroServer")
                messageBox.MessageBox.warning(
                    self, "lavue: Error in connecting to Door or MacroServer",
                    text, str(value))
                return

            rlabel = str(self.imageW.labelROILineEdit.text())
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

            self.sardana.setScanEnv(str(self.doorname), json.dumps(rois))
            warns = []
            if self.addrois:
                try:
                    for alias in toadd:
                        _, warn = self.sardana.runMacro(
                            str(self.doorname), ["nxsadd", alias])
                        if warn:
                            warns.extend(list(warn))
                            print("Warning: %s" % warn)
                    for alias in toremove:
                        _, warn = self.sardana.runMacro(
                            str(self.doorname), ["nxsrm", alias])
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

    def __storeSettings(self):
        """ Stores settings in QSettings object
        """
        settings = QtCore.QSettings()
        settings.setValue(
            "Configuration/AddROIs",
            QtCore.QVariant(self.addrois))
        settings.setValue(
            "Configuration/ShowHistogram",
            QtCore.QVariant(self.showhisto))
        settings.setValue(
            "Configuration/ShowMaskWidget",
            QtCore.QVariant(self.showmask))
        settings.setValue(
            "Configuration/RefreshRate",
            QtCore.QVariant(dataFetchThread.GLOBALREFRESHRATE))
        settings.setValue(
            "Configuration/SecPort",
            QtCore.QVariant(self.secport))
        settings.setValue(
            "Configuration/SecAutoPort",
            QtCore.QVariant(self.secautoport))
        settings.setValue(
            "Configuration/SecStream",
            QtCore.QVariant(self.secstream))
        settings.setValue(
            "Configuration/Sardana",
            QtCore.QVariant(True if self.sardana is not None else False))
        settings.setValue(
            "Layout/Geometry",
            QtCore.QVariant(self.saveGeometry()))
        settings.setValue(
            "Configuration/InterruptOnError",
            QtCore.QVariant(self.interruptonerror))
        settings.setValue(
            "Configuration/SourceTimeout",
            QtCore.QVariant(self.timeout))
        settings.setValue(
            "Configuration/AspectLocked",
            QtCore.QVariant(self.aspectlocked))
        settings.setValue(
            "Configuration/LastImageFileName",
            QtCore.QVariant(self.imagename))
        settings.setValue(
            "Configuration/StatisticsWithoutScaling",
            QtCore.QVariant(self.statswoscaling))
        settings.setValue(
            "Configuration/ZMQStreamTopics",
            QtCore.QVariant(self.zmqtopics))
        settings.setValue(
            "Configuration/AutoZMQStreamTopics",
            QtCore.QVariant(self.autozmqtopics))
        settings.setValue(
            "Configuration/DirectoryTranslation",
            QtCore.QVariant(self.dirtrans))

    def closeEvent(self, event):
        """ stores the setting before finishing the application
        """
        self.__storeSettings()
        self.secstream = False
        try:
            self.dataFetcher.newDataName.disconnect(self.getNewData)
        except:
            pass
        # except Exception as e:
        #     print (str(e))
        if self.sourceW.connected:
            self.sourceW.toggleServerConnection()
        self.disconnect_source()
        time.sleep(min(dataFetchThread.GLOBALREFRESHRATE * 5, 2))
        self.dataFetcher.stop()
        self.seccontext.destroy()
        QtGui.QApplication.closeAllWindows()
        event.accept()

    @QtCore.pyqtSlot()
    def onfetchrois(self):
        if hcs.PYTANGO:
            if not self.doorname:
                self.doorname = self.sardana.getDeviceName("Door")
            try:
                rois = json.loads(self.sardana.getScanEnv(
                    str(self.doorname), ["DetectorROIs"]))
            except Exception:
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "Problems in connecting to Door or MacroServer")
                messageBox.MessageBox.warning(
                    self, "lavue: Error in connecting to Door or MacroServer",
                    text, str(value))
                return
            rlabel = str(self.imageW.labelROILineEdit.text())
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
            self.imageW.labelROILineEdit.setText(" ".join(slabel))
            self.imageW.updateROIButton()
            self.imageW.roiNrChanged(len(coords), coords)
        else:
            print("Connection error")

    @QtCore.pyqtSlot()
    def loadfile(self):
        fileDialog = QtGui.QFileDialog()
        imagename = str(
            fileDialog.getOpenFileName(
                self, 'Load file', self.imagename or '.'))
        if imagename:
            self.imagename = imagename
            newimage = imageFileHandler.ImageFileHandler(
                str(self.imagename)).getImage()
            if newimage is not None:
                self.image_name = self.imagename
                self.raw_image = np.transpose(newimage)
                self.plot()
            else:
                text = messageBox.MessageBox.getText(
                    "lavue: File %s cannot be loaded" % self.imagename)
                messageBox.MessageBox.warning(
                    self,
                    "lavue: File %s cannot be loaded" % self.imagename,
                    text,
                    str("lavue: File %s cannot be loaded" % self.imagename))

    @QtCore.pyqtSlot()
    def configuration(self):
        cnfdlg = configDialog.ConfigDialog(self)
        if not self.doorname and self.sardana is not None:
            self.doorname = self.sardana.getDeviceName("Door")
        cnfdlg.sardana = True if self.sardana is not None else False
        cnfdlg.door = self.doorname
        cnfdlg.addrois = self.addrois
        cnfdlg.showhisto = self.showhisto
        cnfdlg.showmask = self.showmask
        cnfdlg.secautoport = self.secautoport
        cnfdlg.secport = self.secport
        cnfdlg.secstream = self.secstream
        cnfdlg.refreshrate = dataFetchThread.GLOBALREFRESHRATE
        cnfdlg.timeout = self.timeout
        cnfdlg.aspectlocked = self.aspectlocked
        cnfdlg.statswoscaling = self.statswoscaling
        cnfdlg.zmqtopics = self.zmqtopics
        cnfdlg.autozmqtopics = self.autozmqtopics
        cnfdlg.dirtrans = self.dirtrans
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__updateConfig(cnfdlg)

    def __updateConfig(self, dialog):
        self.doorname = dialog.door
        if dialog.sardana != (True if self.sardana is not None else False):
            self.setSardana(dialog.sardana)
        self.addrois = dialog.addrois

        if self.showhisto != dialog.showhisto:
            self.levelsW.changeView(dialog.showhisto)
            self.showhisto = dialog.showhisto
        if self.showmask != dialog.showmask:
            self.prepBoxW.changeView(dialog.showmask)
            self.showmask = dialog.showmask
        dataFetchThread.GLOBALREFRESHRATE = dialog.refreshrate
        if self.secstream != dialog.secstream or (
                self.secautoport != dialog.secautoport and dialog.secautoport):
            if self.secstream:
                # workaround for a bug in libzmq
                try:
                    self.secsocket.unbind(self.secsockopt)
                except:
                    pass
                if self.sourceW.connected:
                    self.sourceW.connectSuccess(None)
            if dialog.secstream:
                if dialog.secautoport:
                    self.secsockopt = "tcp://*:*"
                    self.secsocket.bind(self.secsockopt)
                    dialog.secport = self.secsocket.getsockopt(
                        zmq.LAST_ENDPOINT).split(":")[-1]
                else:
                    self.secsockopt = "tcp://*:%s" % dialog.secport
                    self.secsocket.bind(self.secsockopt)
                if self.sourceW.connected:
                    self.sourceW.connectSuccess(dialog.secport)
        self.secautoport = dialog.secautoport
        self.secport = dialog.secport
        self.timeout = dialog.timeout
        self.data_source.timeout = self.timeout
        self.aspectlocked = dialog.aspectlocked
        self.imageW.img_widget.setAspectLocked(self.aspectlocked)
        self.secstream = dialog.secstream
        setsrc = False
        if self.dirtrans != dialog.dirtrans:
            self.dirtrans = dialog.dirtrans
            self.sourceW.dirtrans = self.dirtrans
            setsrc = True
        if self.zmqtopics != dialog.zmqtopics:
            self.zmqtopics = dialog.zmqtopics
            self.sourceW.zmqtopics = self.zmqtopics
            setsrc = True
        if self.autozmqtopics != dialog.autozmqtopics:
            self.autozmqtopics = dialog.autozmqtopics
            setsrc = True
        if setsrc:
            self.sourceW.update(
                zmqtopics=self.zmqtopics, dirtrans=self.dirtrans,
                autozmqtopics=self.autozmqtopics)
            self.sourceW.updateLayout()
        self.statswoscaling = dialog.statswoscaling
        if self.imageW.img_widget.statswoscaling != self.statswoscaling:
            self.imageW.img_widget.statswoscaling = self.statswoscaling
            self.plot()

    @QtCore.pyqtSlot(str)
    def setSignalHost(self, signalhost):
        self._signalhost = signalhost
        self.data_source.setSignalHost(self._signalhost)

    def setSardana(self, status):
        if status is False:
            self.sardana = None
            self.imageW.applyROIButton.setEnabled(False)
            self.imageW.fetchROIButton.setEnabled(False)
        else:
            self.sardana = sardanaUtils.SardanaUtils()
            self.imageW.applyROIButton.setEnabled(True)
            self.imageW.fetchROIButton.setEnabled(True)

    @QtCore.pyqtSlot(int)
    def updateSource(self, status):
        if status:
            self.data_source = getattr(
                hcs, self.sourcetypes[status - 1]["datasource"])(self.timeout)
            self.dataFetcher.data_source = self.data_source
            if self._signalhost:
                self.data_source.setSignalHost(self._signalhost)
        self.update_state.emit(status)

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def plot(self):
        """ The main command of the live viewer class:
        draw a numpy array with the given name."""
        # prepare or preprocess the raw image if present:
        self.prepareImage()

        # perform transformation
        self.transform()

        # use the internal raw image to create a display image with chosen
        # scaling
        self.scale(self.scalingW.currentScaling())
        # calculate and update the stats for this
        self.calc_update_stats()

        # calls internally the plot function of the plot widget
        self.imageW.plot(self.scaled_image, self.image_name,
                         self.display_image
                         if self.statswoscaling else self.scaled_image)
        if self.updatehisto:
            self.levelsW.imageChanged()
            self.updatehisto = False

    @QtCore.pyqtSlot()
    def calc_update_stats_sec(self):
        self.calc_update_stats(secstream=False)

    def calc_update_stats(self, secstream=True):
        # calculate the stats for this
        maxVal, meanVal, varVal, minVal, maxRawVal, maxSVal = self.calcStats()
        calctime = time.time()
        currentscaling = self.scalingW.currentScaling()
        # update the statistics display
        roiVal, currentroi = self.calcROIsum()
        roilabel = ""
        if currentroi >= 0:
            roilabel = "roi_%s sum: " % (currentroi + 1)
            slabel = []
            rlabel = str(self.imageW.labelROILineEdit.text())
            if rlabel:
                slabel = re.split(';|,| |\n', rlabel)
                slabel = [lb for lb in slabel if lb]
            if slabel:
                roilabel = "%s\n[%s]" % (
                    roilabel,
                    slabel[currentroi]
                    if currentroi < len(slabel) else slabel[-1])
        if secstream and self.secstream and self.scaled_image is not None:
            messagedata = {
                'command': 'alive', 'calctime': calctime, 'maxval': maxVal,
                'maxrawval': maxRawVal,
                'minval': minVal, 'meanval': meanVal, 'pid': self.apppid,
                'scaling': (
                    'linear' if self.statswoscaling else currentscaling)}
            topic = 10001
            message = "%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii"))
            self.secsocket.send_string(str(message))

        self.statsW.updateStatistics(
            meanVal, maxVal, varVal,
            'linear' if self.statswoscaling else currentscaling,
            roiVal, roilabel)

        # if needed, update the level display
        if self.levelsW.isAutoLevel():
            self.levelsW.updateLevels(float(minVal), float(maxSVal))

    # mode changer: start plotting mode
    @QtCore.pyqtSlot()
    def startPlotting(self):
        # only start plotting if the connection is really established
        if not self.sourceW.isConnected():
            return
        self.dataFetcher.start()

    # mode changer: stop plotting mode
    @QtCore.pyqtSlot()
    def stopPlotting(self):
        if self.dataFetcher is not None:
            pass

    # call the connect function of the source interface
    @QtCore.pyqtSlot()
    def connect_source(self):
        if self.data_source is None:
            messageBox.MessageBox.warning(
                self, "lavue: No data source is defined",
                "No data source is defined",
                "Please select the image source")

        if not self.data_source.connect():
            self.sourceW.connectFailure()
            messageBox.MessageBox.warning(
                self, "lavue: The %s connection could not be established"
                % type(self.data_source).__name__,
                "The %s connection could not be established"
                % type(self.data_source).__name__,
                "<WARNING> The %s connection could not be established. "
                "Check the settings." % type(self.data_source))
        else:
            self.sourceW.connectSuccess(
                self.secport if self.secstream else None)
        if self.secstream:
            calctime = time.time()
            messagedata = {
                'command': 'start', 'calctime': calctime, 'pid': self.apppid}
            topic = 10001
            # print(str(messagedata))
            self.secsocket.send_string("%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii")))
        self.updatehisto = True

    # call the disconnect function of the hidra interface
    @QtCore.pyqtSlot()
    def disconnect_source(self):
        self.data_source.disconnect()
        if self.secstream:
            calctime = time.time()
            messagedata = {
                'command': 'stop', 'calctime': calctime, 'pid': self.apppid}
            # print(str(messagedata))
            topic = 10001
            self.secsocket.send_string("%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii")))
        # self.data_source = None

    @QtCore.pyqtSlot(str, str)
    def getNewData(self, name, metadata=None):
        # check if data is there at all
        if name == "__ERROR__":
            if self.interruptonerror:
                if self.sourceW.connected:
                    self.sourceW.toggleServerConnection()
                _, errortext, _ = self.exchangelist.readData()
                messageBox.MessageBox.warning(
                    self, "lavue: Error in reading data",
                    "Viewing will be interrupted", str(errortext))
            return
        if name is None:
            return
        # first time:
        if str(self.metadata) != str(metadata) and str(metadata).strip():
            image_name, raw_image, self.metadata = self.exchangelist.readData()
            if str(image_name).strip() and \
               not isinstance(raw_image, (str, unicode)):
                self.image_name = image_name
                self.raw_image = raw_image
            try:
                mdata = json.loads(str(metadata))
                if isinstance(mdata, dict):
                    resdata = dict((k, v) for (k, v) in mdata.items()
                                   if k in self.__allowedmdata)
                    wgdata = dict((k, v) for (k, v) in mdata.items()
                                  if k in self.__allowedwgdata)
                    if wgdata:
                        self.imageW.updateMetaData(**wgdata)
                    if resdata:
                        self.sourceW.update(**resdata)
            except Exception as e:
                print(str(e))
        elif str(name).strip():
            if self.image_name is None or str(self.image_name) != str(name):
                self.image_name, raw_image, self.metadata \
                    = self.exchangelist.readData()
                if not isinstance(raw_image, (str, unicode)):
                    self.raw_image = raw_image
        self.plot()

    def prepareImage(self):
        if self.raw_image is None:
            return

        if len(self.raw_image.shape) == 3:
            self.levelsW.setNumberOfChannels(self.raw_image.shape[0])
            if not self.levelsW.colorChannel():
                self.rawgrey_image = np.sum(self.raw_image, 0)
            else:
                try:
                    if len(self.raw_image) >= self.levelsW.colorChannel():
                        self.rawgrey_image = self.raw_image[
                            self.levelsW.colorChannel() - 1]
                    else:
                        self.rawgrey_image = np.mean(self.raw_image, 0)
                except:
                    import traceback
                    value = traceback.format_exc()
                    text = messageBox.MessageBox.getText(
                        "lavue: color channel %s does not exist."
                        " Reset to grey scale"
                        % self.levelsW.colorChannel())
                    messageBox.MessageBox.warning(
                        self,
                        "lavue: color channel %s does not exist. "
                        " Reset to grey scale"
                        % self.levelsW.colorChannel(),
                        text, str(value))
                    self.levelsW.setChannel(0)
                    self.rawgrey_image = np.sum(self.raw_image, 0)
        else:
            self.rawgrey_image = self.raw_image
            self.levelsW.setNumberOfChannels(0)

        self.display_image = self.rawgrey_image

        if self.doBkgSubtraction and self.background_image is not None:
            # simple subtraction
            try:
                self.display_image = self.rawgrey_image - self.background_image
            except:
                self.checkBKGSubtraction(False)
                self.background_image = None
                self.doBkgSubtraction = False
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "lavue: Background image does not match "
                    "to the current image")
                messageBox.MessageBox.warning(
                    self, "lavue: Background image does not match "
                    "to the current image",
                    text, str(value))

        if self.showmask and self.applyImageMask and \
           self.maskIndices is not None:
            # set all masked (non-zero values) to zero by index
            self.display_image[self.maskIndices] = 0

    def transform(self):
        '''Do the image transformation on the given numpy array.'''
        if self.display_image is None or self.trafoName is "None":
            return
        # !!! there is a place, where indices go to die...
        # somewhere, the ordering of the indices gets messed up
        # to rectify the situation and not mislead users,
        # make the transformation, so that at least the name fits
        elif self.trafoName == "flip (up-down)":
            self.display_image = np.fliplr(self.display_image)
        elif self.trafoName == "flip (left-right)":
            self.display_image = np.flipud(self.display_image)
        elif self.trafoName == "transpose":
            self.display_image = np.transpose(self.display_image)
        elif self.trafoName == "rot90 (clockwise)":
            # self.display_image = np.rot90(self.display_image, 3)
            self.display_image = np.transpose(
                np.flipud(self.display_image))
        elif self.trafoName == "rot180":
            self.display_image = np.flipud(
                np.fliplr(self.display_image))
        elif self.trafoName == "rot270 (clockwise)":
            # self.display_image = np.rot90(self.display_image, 1)
            self.display_image = np.transpose(
                np.fliplr(self.display_image))
        elif self.trafoName == "rot180 + transpose":
            self.display_image = np.transpose(
                np.fliplr(np.flipud(self.display_image)))

    @QtCore.pyqtSlot(str)
    def scale(self, scalingType):
        self.scaled_image = self.display_image
        self.imageW.img_widget.scaling = scalingType
        if self.display_image is None:
            return
        if scalingType == "sqrt":
            self.scaled_image = np.clip(self.display_image, 0, np.inf)
            self.scaled_image = np.sqrt(self.scaled_image)
        elif scalingType == "log":
            self.scaled_image = np.clip(self.display_image, 10e-3, np.inf)
            self.scaled_image = np.log10(self.scaled_image)

    def calcROIsum(self):
        rid = self.imageW.img_widget.currentroi
        image = None
        if self.statswoscaling and self.display_image is not None:
            image = self.display_image
        elif not self.statswoscaling and self.scaled_image is not None:
            image = self.scaled_image
        if image is not None:
            if self.imageW.img_widget.roienable:
                if rid >= 0:
                    roicoords = self.imageW.img_widget.roicoords
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

    def calcStats(self):
        if self.statswoscaling and self.display_image is not None:
            maxval = np.amax(self.display_image)
            meanval = np.mean(self.display_image)
            varval = np.var(self.display_image)
            maxsval = np.amax(self.scaled_image)
        elif not self.statswoscaling and self.scaled_image is not None:
            maxval = np.amax(self.scaled_image)
            meanval = np.mean(self.scaled_image)
            varval = np.var(self.scaled_image)
            maxsval = maxval
        else:
            return "0.", "0.", "0.", "0.", "0.", "0."
        maxrawval = np.amax(self.rawgrey_image)
        # automatic maximum clipping to hardcoded value
        try:
            checkval = meanval + 10 * np.sqrt(varval)
            if maxval > checkval:
                maxval = checkval
        except:
            print("Warning in calculating checkval from:"
                  " meanval = %s,  varval = %s" % (meanval, varval))
        return (str("%.4f" % maxval),
                str("%.4f" % meanval),
                str("%.4f" % varval),
                str("%.3f" % np.amin(self.scaled_image)),
                str("%.4f" % maxrawval),
                str("%.3f" % maxsval))

    def getInitialLevels(self):
        if self.scaled_image is not None:
            return np.amin(self.scaled_image), np.amax(self.scaled_image)

    @QtCore.pyqtSlot(int)
    def checkMasking(self, state):
        self.applyImageMask = state
        if self.applyImageMask and self.mask_image is None:
            self.maskW.noImage()

    @QtCore.pyqtSlot(str)
    def prepareMasking(self, imagename):
        '''Get the mask image, select non-zero elements
        and store the indices.'''
        if imagename:
            self.mask_image = imageFileHandler.ImageFileHandler(
                str(imagename)).getImage()
            self.maskIndices = (self.mask_image != 0)
        else:
            self.mask_image = None
        # self.maskIndices = np.nonzero(self.mask_image != 0)

    @QtCore.pyqtSlot(int)
    def checkBKGSubtraction(self, state):
        self.doBkgSubtraction = state
        if self.doBkgSubtraction and self.background_image is None:
            self.bkgSubW.setDisplayedName("")
        elif not state and self.bkgSubW.applyBkgSubtractBox.isChecked():
            self.bkgSubW.applyBkgSubtractBox.setChecked(False)
            self.bkgSubW.setDisplayedName("")
        self.imageW.img_widget.doBkgSubtraction = state
        self.plot()

    @QtCore.pyqtSlot(str)
    def prepareBKGSubtraction(self, imagename):
        self.background_image = imageFileHandler.ImageFileHandler(
            str(imagename)).getImage()

    @QtCore.pyqtSlot()
    def setCurrentImageAsBKG(self):
        if self.rawgrey_image is not None:
            self.background_image = self.rawgrey_image
            self.bkgSubW.setDisplayedName(str(self.image_name))
        else:
            self.bkgSubW.setDisplayedName("")
        #  self.updatehisto = True

    @QtCore.pyqtSlot(str)
    def assessTransformation(self, trafoName):
        self.trafoName = trafoName
        self.plot()

    @QtCore.pyqtSlot()
    def setTicks(self):
        if self.imageW.setTicks():
            self.plot()
