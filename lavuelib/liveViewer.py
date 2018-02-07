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

from . import sourceGroupBox
from . import preparationGroupBox
from . import scalingGroupBox
from . import levelsGroupBox
from . import statisticsGroupBox
from . import imageWidget
from . import configDialog

from . import imageFileHandler
from . import sardanaUtils
from . import dataFetchThread

from .hidraServerList import HIDRASERVERLIST


class LiveViewer(QtGui.QDialog):

    '''The master class for the dialog, contains all other
    widget and handles communication.'''
    update_state = QtCore.pyqtSignal(int)

    def __init__(self, umode=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.sourcetypes = []
        if hcs.HIDRA:
            self.sourcetypes.append("HidraSourceWidget")
        self.sourcetypes.append("HTTPSourceWidget")
        if hcs.PYTANGO:
            self.sourcetypes.append("TangoAttrSourceWidget")
            self.sourcetypes.append("TangoFileSourceWidget")
        self.sourcetypes.append("ZMQSourceWidget")
        self.sourcetypes.append("TestSourceWidget")

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
        self.data_source = hcs.BaseSource()

        # WIDGET DEFINITIONS
        # instantiate the widgets and declare the parent

        self.sourceWg = sourceGroupBox.SourceGroupBox(
            parent=self, sourcetypes=self.sourcetypes)
        self.sourceWg.updateMetaData(serverdict=HIDRASERVERLIST)

        self.prepBoxWg = preparationGroupBox.PreparationGroupBox(parent=self)
        self.scalingWg = scalingGroupBox.ScalingGroupBox(parent=self)
        self.levelsWg = levelsGroupBox.LevelsGroupBox(parent=self)
        self.statsWg = statisticsGroupBox.StatisticsGroupBox(parent=self)
        self.imageWg = imageWidget.ImageWidget(parent=self)
        self.levelsWg.setImageItem(self.imageWg.img_widget.image)
        self.levelsWg.imageChanged(autoLevel=True)

        self.maskWg = self.prepBoxWg.maskWg
        self.bkgSubWg = self.prepBoxWg.bkgSubWg
        self.trafoWg = self.prepBoxWg.trafoWg

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

        self._sourceConfiguration = None

        self.trafoName = "None"

        # LAYOUT DEFINITIONS
        # the dialog layout is side by side
        globallayout = QtGui.QHBoxLayout()

        # define left hand side layout: vertical
        vlayout = QtGui.QVBoxLayout()

        # place widgets on the layouts
        # first the vertical layout on the left side

        # first element is supposed to be tabbed:
        vlayout.addWidget(self.sourceWg)
        vlayout.addWidget(self.prepBoxWg)
        vlayout.addWidget(self.scalingWg)
        vlayout.addWidget(self.levelsWg)
        # vlayout.addWidget(self.gradientW)
        vlayout.addWidget(self.statsWg)

        # then the vertical layout on the --global-- horizontal one
        globallayout.addLayout(vlayout, 1)
        globallayout.addWidget(self.imageWg, 10)

        self.setLayout(globallayout)
        self.setWindowTitle("laVue: Live Image Viewer")

        # SIGNAL LOGIC::

        # signal from intensity scaling widget:
        # self.scalingWg.scalingChanged.connect(self.scale)
        self.scalingWg.scalingChanged.connect(self.plot)
        self.scalingWg.scalingChanged.connect(self.levelsWg.setScalingLabel)

        # signal from limit setting widget
        self.levelsWg.minLevelChanged.connect(self.imageWg.setMinLevel)
        self.levelsWg.maxLevelChanged.connect(self.imageWg.setMaxLevel)
        self.levelsWg.autoLevelsChanged.connect(self.imageWg.setAutoLevels)
        self.levelsWg.levelsChanged.connect(self.plot)
        self.levelsWg.changeView(self.showhisto)
        self.imageWg.cnfButton.clicked.connect(self.configuration)
        self.imageWg.quitButton.clicked.connect(self.close)
        self.imageWg.loadButton.clicked.connect(self.loadfile)
        if self.umode in ["user"]:
            self.imageWg.cnfButton.hide()
        self.imageWg.applyROIButton.clicked.connect(self.onapplyrois)
        self.imageWg.fetchROIButton.clicked.connect(self.onfetchrois)
        self.imageWg.roiCoordsChanged.connect(self.calc_update_stats_sec)
        self.imageWg.pixelComboBox.currentIndexChanged.connect(
            self.onPixelChanged)
        # connecting signals from source widget:
        self.sourceWg.sourceConnectSignal.connect(self.connect_source)
        self.sourceWg.sourceConnectSignal.connect(self.startPlotting)

        self.sourceWg.sourceDisconnectSignal.connect(self.stopPlotting)
        self.sourceWg.sourceDisconnectSignal.connect(self.disconnect_source)

        # gradient selector
        self.levelsWg.channelChanged.connect(self.plot)
        self.imageWg.img_widget.setaspectlocked.triggered.connect(
            self.toggleAspectLocked)
        self.imageWg.ticksPushButton.clicked.connect(self.setTicks)

        # simple mutable caching object for data exchange with thread
        self.exchangelist = dataFetchThread.ExchangeList()

        self.dataFetcher = dataFetchThread.DataFetchThread(
            self.data_source, self.exchangelist)
        self.dataFetcher.newDataName.connect(self.getNewData)
        # ugly !!! sent current state to the data fetcher...
        self.update_state.connect(self.dataFetcher.changeStatus)
        self.sourceWg.sourceStateSignal.connect(self.updateSource)
        self.sourceWg.sourceChangedSignal.connect(self.onSourceChanged)

        self.bkgSubWg.bkgFileSelected.connect(self.prepareBkgSubtraction)
        self.bkgSubWg.useCurrentImageAsBkg.connect(self.setCurrentImageAsBkg)
        self.bkgSubWg.applyStateChanged.connect(self.checkBkgSubtraction)

        self.maskWg.maskFileSelected.connect(self.prepareMasking)
        self.maskWg.applyStateChanged.connect(self.checkMasking)

        # signals from transformation widget
        self.trafoWg.transformationChanged.connect(self.assessTransformation)

        # set the right target name for the source display at initialization

        self.sourceWg.configurationSignal.connect(self.setSourceConfiguration)

        self.sourceWg.updateLayout()
        self.sourceWg.emitSourceChangedSignal()
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
            self.imageWg.img_widget.setAspectLocked(self.aspectlocked)
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
            self.data_source.setTimeOut(self.timeout)
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
        self.imageWg.img_widget.statswoscaling = self.statswoscaling

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

        self.sourceWg.updateMetaData(
            zmqtopics=self.zmqtopics, dirtrans=self.dirtrans,
            autozmqtopics=self.autozmqtopics)

        self.levelsWg.changeView(self.showhisto)
        self.prepBoxWg.changeView(self.showmask)
        self.plot()

    @QtCore.pyqtSlot(bool)
    def toggleAspectLocked(self, status):
        self.aspectlocked = status
        self.imageWg.img_widget.setAspectLocked(self.aspectlocked)

    @QtCore.pyqtSlot(int)
    def onPixelChanged(self):
        text = self.imageWg.pixelComboBox.currentText()
        if text == "ROI":
            self.imageWg.showROIFrame()
            self.trafoName = "None"
            self.trafoWg.setEnabled(False)
            self.imageWg.roiChanged()
        elif text == "LineCut":
            self.imageWg.showLineCutFrame()
            self.trafoWg.setEnabled(True)
            self.imageWg.roiCoordsChanged.emit()
        elif text == "Angle/Q":
            self.imageWg.showAngleQFrame()
            self.trafoWg.setEnabled(True)
            self.imageWg.roiCoordsChanged.emit()
        else:
            self.imageWg.showIntensityFrame()
            self.trafoWg.setEnabled(True)
            self.imageWg.roiCoordsChanged.emit()

    @QtCore.pyqtSlot()
    def onapplyrois(self):
        if hcs.PYTANGO:
            roicoords = self.imageWg.img_widget.roicoords
            roispin = self.imageWg.roiSpinBox.value()
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

            rlabel = str(self.imageWg.labelROILineEdit.text())
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
        if self.sourceWg.isConnected():
            self.sourceWg.toggleServerConnection()
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
            rlabel = str(self.imageWg.labelROILineEdit.text())
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
            self.imageWg.labelROILineEdit.setText(" ".join(slabel))
            self.imageWg.updateROIButton()
            self.imageWg.roiNrChanged(len(coords), coords)
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
            self.levelsWg.changeView(dialog.showhisto)
            self.showhisto = dialog.showhisto
        if self.showmask != dialog.showmask:
            self.prepBoxWg.changeView(dialog.showmask)
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
                if self.sourceWg.isConnected():
                    self.sourceWg.connectSuccess(None)
            if dialog.secstream:
                if dialog.secautoport:
                    self.secsockopt = "tcp://*:*"
                    self.secsocket.bind(self.secsockopt)
                    dialog.secport = self.secsocket.getsockopt(
                        zmq.LAST_ENDPOINT).split(":")[-1]
                else:
                    self.secsockopt = "tcp://*:%s" % dialog.secport
                    self.secsocket.bind(self.secsockopt)
                if self.sourceWg.isConnected():
                    self.sourceWg.connectSuccess(dialog.secport)
        self.secautoport = dialog.secautoport
        self.secport = dialog.secport
        self.timeout = dialog.timeout
        self.data_source.setTimeOut(self.timeout)
        self.aspectlocked = dialog.aspectlocked
        self.imageWg.img_widget.setAspectLocked(self.aspectlocked)
        self.secstream = dialog.secstream
        setsrc = False
        if self.dirtrans != dialog.dirtrans:
            self.dirtrans = dialog.dirtrans
            setsrc = True
        if self.zmqtopics != dialog.zmqtopics:
            self.zmqtopics = dialog.zmqtopics
            setsrc = True
        if self.autozmqtopics != dialog.autozmqtopics:
            self.autozmqtopics = dialog.autozmqtopics
            setsrc = True
        if setsrc:
            self.sourceWg.updateMetaData(
                zmqtopics=self.zmqtopics, dirtrans=self.dirtrans,
                autozmqtopics=self.autozmqtopics)
            self.sourceWg.updateLayout()
        self.statswoscaling = dialog.statswoscaling
        if self.imageWg.img_widget.statswoscaling != self.statswoscaling:
            self.imageWg.img_widget.statswoscaling = self.statswoscaling
            self.plot()

    @QtCore.pyqtSlot(str)
    def setSourceConfiguration(self, sourceConfiguration):
        self._sourceConfiguration = sourceConfiguration
        self.data_source.setConfiguration(self._sourceConfiguration)

    def setSardana(self, status):
        if status is False:
            self.sardana = None
            self.imageWg.applyROIButton.setEnabled(False)
            self.imageWg.fetchROIButton.setEnabled(False)
        else:
            self.sardana = sardanaUtils.SardanaUtils()
            self.imageWg.applyROIButton.setEnabled(True)
            self.imageWg.fetchROIButton.setEnabled(True)

    @QtCore.pyqtSlot(int)
    def onSourceChanged(self, status):
        if status:
            self.data_source = getattr(
                hcs, self.sourceWg.currentDataSource())(self.timeout)
            self.sourceWg.updateMetaData(**self.data_source.getMetaData())

    @QtCore.pyqtSlot(int)
    def updateSource(self, status):
        if status:
            self.data_source.setTimeOut(self.timeout)
            self.dataFetcher.data_source = self.data_source
            if self._sourceConfiguration:
                self.data_source.setConfiguration(self._sourceConfiguration)
            self.sourceWg.updateMetaData(**self.data_source.getMetaData())
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
        self.scale(self.scalingWg.currentScaling())
        # calculate and update the stats for this
        self.calc_update_stats()

        # calls internally the plot function of the plot widget
        self.imageWg.plot(self.scaled_image, self.image_name,
                          self.display_image
                          if self.statswoscaling else self.scaled_image)
        if self.updatehisto:
            self.levelsWg.imageChanged()
            self.updatehisto = False

    @QtCore.pyqtSlot()
    def calc_update_stats_sec(self):
        self.calc_update_stats(secstream=False)

    def calc_update_stats(self, secstream=True):
        # calculate the stats for this
        maxVal, meanVal, varVal, minVal, maxRawVal, maxSVal = self.calcStats()
        calctime = time.time()
        currentscaling = self.scalingWg.currentScaling()
        # update the statistics display
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

        self.statsWg.updateStatistics(
            meanVal, maxVal, varVal,
            'linear' if self.statswoscaling else currentscaling)

        # if needed, update the level display
        if self.levelsWg.isAutoLevel():
            self.levelsWg.updateLevels(float(minVal), float(maxSVal))

    # mode changer: start plotting mode
    @QtCore.pyqtSlot()
    def startPlotting(self):
        # only start plotting if the connection is really established
        if not self.sourceWg.isConnected():
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
            self.sourceWg.connectFailure()
            messageBox.MessageBox.warning(
                self, "lavue: The %s connection could not be established"
                % type(self.data_source).__name__,
                "The %s connection could not be established"
                % type(self.data_source).__name__,
                "<WARNING> The %s connection could not be established. "
                "Check the settings." % type(self.data_source))
        else:
            self.sourceWg.connectSuccess(
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
                if self.sourceWg.isConnected():
                    self.sourceWg.toggleServerConnection()
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
                        self.imageWg.updateMetaData(**wgdata)
                    if resdata:
                        self.sourceWg.updateMetaData(**resdata)
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
            self.levelsWg.setNumberOfChannels(self.raw_image.shape[0])
            if not self.levelsWg.colorChannel():
                self.rawgrey_image = np.sum(self.raw_image, 0)
            else:
                try:
                    if len(self.raw_image) >= self.levelsWg.colorChannel():
                        self.rawgrey_image = self.raw_image[
                            self.levelsWg.colorChannel() - 1]
                    else:
                        self.rawgrey_image = np.mean(self.raw_image, 0)
                except:
                    import traceback
                    value = traceback.format_exc()
                    text = messageBox.MessageBox.getText(
                        "lavue: color channel %s does not exist."
                        " Reset to grey scale"
                        % self.levelsWg.colorChannel())
                    messageBox.MessageBox.warning(
                        self,
                        "lavue: color channel %s does not exist. "
                        " Reset to grey scale"
                        % self.levelsWg.colorChannel(),
                        text, str(value))
                    self.levelsWg.setChannel(0)
                    self.rawgrey_image = np.sum(self.raw_image, 0)
        else:
            self.rawgrey_image = self.raw_image
            self.levelsWg.setNumberOfChannels(0)

        self.display_image = self.rawgrey_image

        if self.doBkgSubtraction and self.background_image is not None:
            # simple subtraction
            try:
                self.display_image = self.rawgrey_image - self.background_image
            except:
                self.checkBkgSubtraction(False)
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
            try:
                self.display_image[self.maskIndices] = 0
            except IndexError:
                self.maskWg.noImage()
                self.applyImageMask = False
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "lavue: Mask image does not match "
                    "to the current image")
                messageBox.MessageBox.warning(
                    self, "lavue: Mask image does not match "
                    "to the current image",
                    text, str(value))

    def transform(self):
        '''Do the image transformation on the given numpy array.'''
        if self.display_image is None or self.trafoName is "none":
            return

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
        self.imageWg.img_widget.scaling = scalingType
        if self.display_image is None:
            return
        if scalingType == "sqrt":
            self.scaled_image = np.clip(self.display_image, 0, np.inf)
            self.scaled_image = np.sqrt(self.scaled_image)
        elif scalingType == "log":
            self.scaled_image = np.clip(self.display_image, 10e-3, np.inf)
            self.scaled_image = np.log10(self.scaled_image)

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
            self.maskWg.noImage()
        self.plot()

    @QtCore.pyqtSlot(str)
    def prepareMasking(self, imagename):
        '''Get the mask image, select non-zero elements
        and store the indices.'''
        if imagename:
            self.mask_image = np.transpose(
                imageFileHandler.ImageFileHandler(
                    str(imagename)).getImage())
            self.maskIndices = (self.mask_image != 0)
        else:
            self.mask_image = None
        # self.maskIndices = np.nonzero(self.mask_image != 0)

    @QtCore.pyqtSlot(int)
    def checkBkgSubtraction(self, state):
        self.doBkgSubtraction = state
        if self.doBkgSubtraction and self.background_image is None:
            self.bkgSubWg.setDisplayedName("")
        else:
            self.bkgSubWg.checkBkgSubtraction(state)
        self.imageWg.img_widget.doBkgSubtraction = state
        self.plot()

    @QtCore.pyqtSlot(str)
    def prepareBkgSubtraction(self, imagename):
        self.background_image = np.transpose(
            imageFileHandler.ImageFileHandler(
                str(imagename)).getImage())

    @QtCore.pyqtSlot()
    def setCurrentImageAsBkg(self):
        if self.rawgrey_image is not None:
            self.background_image = self.rawgrey_image
            self.bkgSubWg.setDisplayedName(str(self.image_name))
        else:
            self.bkgSubWg.setDisplayedName("")
        #  self.updatehisto = True

    @QtCore.pyqtSlot(str)
    def assessTransformation(self, trafoName):
        self.trafoName = trafoName
        self.plot()

    @QtCore.pyqtSlot()
    def setTicks(self):
        if self.imageWg.setTicks():
            self.plot()
