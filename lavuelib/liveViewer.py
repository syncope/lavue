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


""" live viewer settings """

from __future__ import print_function
from __future__ import unicode_literals

import time
import json
import re
import numpy as np
import os
import zmq

from PyQt4 import QtCore, QtGui, uic

from . import imageSource as isr
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
from . import settings

from .hidraServerList import HIDRASERVERLIST

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "LavueDialog.ui"))


class LiveViewer(QtGui.QDialog):

    '''The master class for the dialog, contains all other
    widget and handles communication.'''
    updateStateSignal = QtCore.pyqtSignal(int)

    def __init__(self, umode=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        #: (:obj:`list` < :obj:`str` > ) source class names
        self.__sourcetypes = []
        if isr.HIDRA:
            self.__sourcetypes.append("HidraSourceWidget")
        self.__sourcetypes.append("HTTPSourceWidget")
        if isr.PYTANGO:
            self.__sourcetypes.append("TangoAttrSourceWidget")
            self.__sourcetypes.append("TangoFileSourceWidget")
        self.__sourcetypes.append("ZMQSourceWidget")
        self.__sourcetypes.append("TestSourceWidget")

        if umode and umode.lower() in ["expert"]:
            #: (:obj:`str`) execution mode: expert or user
            self.__umode = "expert"
        else:
            #: (:obj:`str`) execution mode: expert or user
            self.__umode = "user"
        #: (:obj:`bool`) histogram should be updated
        self.__updatehisto = False
        #: (:obj:`int`) program pid
        self.__apppid = os.getpid()

        #: (:obj:`list` < :obj:`str` > ) allowed source metadata
        self.__allowedmdata = ["datasources"]
        #: (:obj:`list` < :obj:`str` > ) allowed widget metadata
        self.__allowedwgdata = ["axisscales", "axislabels"]

        # (:class:`lavuelib.imageSource.BaseSource`) data source object
        self.__datasource = isr.BaseSource()

        # WIDGET DEFINITIONS

        #: (:class:`lavuelib.sourceGroupBox.SourceGroupBox`) source groupbox
        self.__sourceWg = sourceGroupBox.SourceGroupBox(
            parent=self, sourcetypes=self.__sourcetypes)
        self.__sourceWg.updateMetaData(serverdict=HIDRASERVERLIST)

        #: (:class:`lavuelib.preparationGroupBox.PreparationGroupBox`)
        #: preparation groupbox
        self.__prepWg = preparationGroupBox.PreparationGroupBox(parent=self)
        #: (:class:`lavuelib.scalingGroupBox.ScalingGroupBox`) scaling groupbox
        self.__scalingWg = scalingGroupBox.ScalingGroupBox(parent=self)
        #: (:class:`lavuelib.levelsGroupBox.LevelsGroupBox`) level groupbox
        self.__levelsWg = levelsGroupBox.LevelsGroupBox(parent=self)
        #: (:class:`lavuelib.statisticsGroupBox.StatisticsGroupBox`)
        #:     statistic groupbox
        self.__statsWg = statisticsGroupBox.StatisticsGroupBox(parent=self)
        #: (:class:`lavuelib.imageWidget.ImageWidget`) image widget
        self.__imageWg = imageWidget.ImageWidget(parent=self)

        self.__levelsWg.setImageItem(self.__imageWg.displaywidget.image)
        self.__levelsWg.imageChanged(autoLevel=True)

        #: (:class:`lavuelib.maskWidget.MaskWidget`) mask widget
        self.__maskWg = self.__prepWg.maskWg
        #: (:class:`lavuelib.bkgSubtractionWidget.BkgSubtractionWidget`)
        #:    background subtraction widget
        self.__bkgSubWg = self.__prepWg.bkgSubWg
        #: (:class:`lavuelib.transformationsWidget.TransformationsWidget`)
        #:    transformations widget
        self.__trafoWg = self.__prepWg.trafoWg

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

        #: (:class:`Ui_LevelsGroupBox') ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        self.__settings = settings.Settings()

        # # LAYOUT DEFINITIONS
        self.setWindowTitle("laVue: Live Image Viewer")
        self.__ui.confVerticalLayout.addWidget(self.__sourceWg)
        self.__ui.confVerticalLayout.addWidget(self.__prepWg)
        self.__ui.confVerticalLayout.addWidget(self.__scalingWg)
        self.__ui.confVerticalLayout.addWidget(self.__levelsWg)
        self.__ui.confVerticalLayout.addWidget(self.__statsWg)
        self.__ui.imageVerticalLayout.addWidget(self.__imageWg)
        self.__ui.splitter.setStretchFactor(0, 1)
        self.__ui.splitter.setStretchFactor(1, 10)

        # SIGNAL LOGIC::

        # signal from intensity scaling widget:
        # self.__scalingWg.scalingChanged.connect(self.scale)
        self.__scalingWg.scalingChanged.connect(self.plot)
        self.__scalingWg.scalingChanged.connect(self.__levelsWg.setScalingLabel)

        # signal from limit setting widget
        self.__levelsWg.minLevelChanged.connect(self.__imageWg.setMinLevel)
        self.__levelsWg.maxLevelChanged.connect(self.__imageWg.setMaxLevel)
        self.__levelsWg.autoLevelsChanged.connect(self.__imageWg.setAutoLevels)
        self.__levelsWg.levelsChanged.connect(self.plot)
        self.__levelsWg.changeView(self.__settings.showhisto)
        self.__ui.cnfPushButton.clicked.connect(self.configuration)
        self.__ui.quitPushButton.clicked.connect(self.close)
        self.__ui.loadPushButton.clicked.connect(self.loadfile)
        if self.__umode in ["user"]:
            self.__ui.cnfPushButton.hide()
        self.__imageWg.applyROIButton.clicked.connect(self.onapplyrois)
        self.__imageWg.fetchROIButton.clicked.connect(self.onfetchrois)
        self.__imageWg.roiCoordsChanged.connect(self.calc_update_stats_sec)
        self.__imageWg.pixelComboBox.currentIndexChanged.connect(
            self.onPixelChanged)
        # connecting signals from source widget:
        self.__sourceWg.sourceConnectSignal.connect(self.connect_source)
        self.__sourceWg.sourceConnectSignal.connect(self.startPlotting)

        self.__sourceWg.sourceDisconnectSignal.connect(self.stopPlotting)
        self.__sourceWg.sourceDisconnectSignal.connect(self.disconnect_source)

        # gradient selector
        self.__levelsWg.channelChanged.connect(self.plot)
        self.__imageWg.displaywidget.setaspectlocked.triggered.connect(
            self.toggleAspectLocked)
        self.__imageWg.ticksPushButton.clicked.connect(self.setTicks)

        # simple mutable caching object for data exchange with thread
        self.exchangelist = dataFetchThread.ExchangeList()

        self.dataFetcher = dataFetchThread.DataFetchThread(
            self.__datasource, self.exchangelist)
        self.dataFetcher.newDataName.connect(self.getNewData)
        # ugly !!! sent current state to the data fetcher...
        self.updateStateSignal.connect(self.dataFetcher.changeStatus)
        self.__sourceWg.sourceStateSignal.connect(self.updateSource)
        self.__sourceWg.sourceChangedSignal.connect(self.onSourceChanged)

        self.__bkgSubWg.bkgFileSelected.connect(self.prepareBkgSubtraction)
        self.__bkgSubWg.useCurrentImageAsBkg.connect(self.setCurrentImageAsBkg)
        self.__bkgSubWg.applyStateChanged.connect(self.checkBkgSubtraction)

        self.__maskWg.maskFileSelected.connect(self.prepareMasking)
        self.__maskWg.applyStateChanged.connect(self.checkMasking)

        # signals from transformation widget
        self.__trafoWg.transformationChanged.connect(self.assessTransformation)

        # set the right target name for the source display at initialization

        self.__sourceWg.configurationSignal.connect(self.setSourceConfiguration)

        self.__sourceWg.updateLayout()
        self.__sourceWg.emitSourceChangedSignal()
        self.onPixelChanged()

        self.__loadSettings()

        self.plot()

    def __loadSettings(self):
        settings = QtCore.QSettings()
        self.restoreGeometry(
            settings.value("Layout/Geometry").toByteArray())

        status = self.__settings.load(settings)

        for topic, value in status:
            text = messageBox.MessageBox.getText(topic)
            messageBox.MessageBox.warning(self, topic, text, str(value))

        self.setSardana(self.__settings.sardana)
        self.__imageWg.displaywidget.setAspectLocked(
            self.__settings.aspectlocked)
        self.__datasource.setTimeOut(self.__settings.timeout)
        dataFetchThread.GLOBALREFRESHRATE = self.__settings.refreshrate
        self.__imageWg.displaywidget.statswoscaling = \
            self.__settings.statswoscaling

        self.__sourceWg.updateMetaData(
            zmqtopics=self.__settings.zmqtopics,
            dirtrans=self.__settings.dirtrans,
            autozmqtopics=self.__settings.autozmqtopics)

        self.__levelsWg.changeView(self.__settings.showhisto)
        self.__prepWg.changeView(self.__settings.showmask)

    def __storeSettings(self):
        """ Stores settings in QSettings object
        """
        settings = QtCore.QSettings()
        settings.setValue(
            "Layout/Geometry",
            QtCore.QVariant(self.saveGeometry()))

        self.__settings.refreshrate = dataFetchThread.GLOBALREFRESHRATE
        self.__settings.sardana = True if self.sardana is not None else False
        self.__settings.store(settings)

    @QtCore.pyqtSlot(bool)
    def toggleAspectLocked(self, status):
        self.__settings.aspectlocked = status
        self.__imageWg.displaywidget.setAspectLocked(
            self.__settings.aspectlocked)

    @QtCore.pyqtSlot(int)
    def onPixelChanged(self):
        text = self.__imageWg.pixelComboBox.currentText()
        if text == "ROI":
            self.trafoName = "None"
            self.__trafoWg.setEnabled(False)
        elif text == "LineCut":
            self.__trafoWg.setEnabled(True)
        elif text == "Angle/Q":
            self.__trafoWg.setEnabled(True)
        else:
            self.__trafoWg.setEnabled(True)
        self.__imageWg.onPixelChanged(text)

    @QtCore.pyqtSlot()
    def onapplyrois(self):
        if isr.PYTANGO:
            roicoords = self.__imageWg.displaywidget.roicoords
            roispin = self.__imageWg.roiSpinBox.value()
            if not self.__settings.doorname:
                self.__settings.doorname = self.sardana.getDeviceName("Door")
            try:
                rois = json.loads(self.sardana.getScanEnv(
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

            rlabel = str(self.__imageWg.labelROILineEdit.text())
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

            self.sardana.setScanEnv(
                str(self.__settings.doorname), json.dumps(rois))
            warns = []
            if self.__settings.addrois:
                try:
                    for alias in toadd:
                        _, warn = self.sardana.runMacro(
                            str(self.__settings.doorname), ["nxsadd", alias])
                        if warn:
                            warns.extend(list(warn))
                            print("Warning: %s" % warn)
                    for alias in toremove:
                        _, warn = self.sardana.runMacro(
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

    def closeEvent(self, event):
        """ stores the setting before finishing the application
        """
        self.__storeSettings()
        self.__settings.secstream = False
        try:
            self.dataFetcher.newDataName.disconnect(self.getNewData)
        except:
            pass
        # except Exception as e:
        #     print (str(e))
        if self.__sourceWg.isConnected():
            self.__sourceWg.toggleServerConnection()
        self.disconnect_source()
        time.sleep(min(dataFetchThread.GLOBALREFRESHRATE * 5, 2))
        self.dataFetcher.stop()
        self.__settings.seccontext.destroy()
        QtGui.QApplication.closeAllWindows()
        event.accept()

    @QtCore.pyqtSlot()
    def onfetchrois(self):
        if isr.PYTANGO:
            if not self.__settings.doorname:
                self.__settings.doorname = self.sardana.getDeviceName("Door")
            try:
                rois = json.loads(self.sardana.getScanEnv(
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
            rlabel = str(self.__imageWg.labelROILineEdit.text())
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
            self.__imageWg.labelROILineEdit.setText(" ".join(slabel))
            self.__imageWg.updateROIButton()
            self.__imageWg.roiNrChanged(len(coords), coords)
        else:
            print("Connection error")

    @QtCore.pyqtSlot()
    def loadfile(self):
        fileDialog = QtGui.QFileDialog()
        imagename = str(
            fileDialog.getOpenFileName(
                self, 'Load file', self.__settings.imagename or '.'))
        if imagename:
            self.__settings.imagename = imagename
            newimage = imageFileHandler.ImageFileHandler(
                str(self.__settings.imagename)).getImage()
            if newimage is not None:
                self.image_name = self.__settings.imagename
                self.raw_image = np.transpose(newimage)
                self.plot()
            else:
                text = messageBox.MessageBox.getText(
                    "lavue: File %s cannot be loaded"
                    % self.__settings.imagename)
                messageBox.MessageBox.warning(
                    self,
                    "lavue: File %s cannot be loaded"
                    % self.__settings.imagename,
                    text,
                    str("lavue: File %s cannot be loaded"
                        % self.__settings.imagename))

    @QtCore.pyqtSlot()
    def configuration(self):
        cnfdlg = configDialog.ConfigDialog(self)
        if not self.__settings.doorname and self.sardana is not None:
            self.__settings.doorname = self.sardana.getDeviceName("Door")
        cnfdlg.sardana = True if self.sardana is not None else False
        cnfdlg.door = self.__settings.doorname
        cnfdlg.addrois = self.__settings.addrois
        cnfdlg.showhisto = self.__settings.showhisto
        cnfdlg.showmask = self.__settings.showmask
        cnfdlg.secautoport = self.__settings.secautoport
        cnfdlg.secport = self.__settings.secport
        cnfdlg.secstream = self.__settings.secstream
        cnfdlg.refreshrate = dataFetchThread.GLOBALREFRESHRATE
        cnfdlg.timeout = self.__settings.timeout
        cnfdlg.aspectlocked = self.__settings.aspectlocked
        cnfdlg.statswoscaling = self.__settings.statswoscaling
        cnfdlg.zmqtopics = self.__settings.zmqtopics
        cnfdlg.autozmqtopics = self.__settings.autozmqtopics
        cnfdlg.dirtrans = self.__settings.dirtrans
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__updateConfig(cnfdlg)

    def __updateConfig(self, dialog):
        self.__settings.doorname = dialog.door
        if dialog.sardana != (True if self.sardana is not None else False):
            self.setSardana(dialog.sardana)
            self.__settings.sardana = dialog.sardana
        self.__settings.addrois = dialog.addrois

        if self.__settings.showhisto != dialog.showhisto:
            self.__levelsWg.changeView(dialog.showhisto)
            self.__settings.showhisto = dialog.showhisto
        if self.__settings.showmask != dialog.showmask:
            self.__prepWg.changeView(dialog.showmask)
            self.__settings.showmask = dialog.showmask
        dataFetchThread.GLOBALREFRESHRATE = dialog.refreshrate
        self.__settings.refreshrate = dialog.refreshrate
        if self.__settings.secstream != dialog.secstream or (
                self.__settings.secautoport != dialog.secautoport
                and dialog.secautoport):
            if self.__settings.secstream:
                # workaround for a bug in libzmq
                try:
                    self.__settings.secsocket.unbind(
                        self.__settings.secsockopt)
                except:
                    pass
                if self.__sourceWg.isConnected():
                    self.__sourceWg.connectSuccess(None)
            if dialog.secstream:
                if dialog.secautoport:
                    self.__settings.secsockopt = "tcp://*:*"
                    self.__settings.secsocket.bind(self.__settings.secsockopt)
                    dialog.secport = self.__settings.secsocket.getsockopt(
                        zmq.LAST_ENDPOINT).split(":")[-1]
                else:
                    self.__settings.secsockopt = "tcp://*:%s" % dialog.secport
                    self.__settings.secsocket.bind(self.__settings.secsockopt)
                if self.__sourceWg.isConnected():
                    self.__sourceWg.connectSuccess(dialog.secport)
        self.__settings.secautoport = dialog.secautoport
        self.__settings.secport = dialog.secport
        self.__settings.timeout = dialog.timeout
        self.__datasource.setTimeOut(self.__settings.timeout)
        self.__settings.aspectlocked = dialog.aspectlocked
        self.__imageWg.displaywidget.setAspectLocked(
            self.__settings.aspectlocked)
        self.__settings.secstream = dialog.secstream
        setsrc = False
        if self.__settings.dirtrans != dialog.dirtrans:
            self.__settings.dirtrans = dialog.dirtrans
            setsrc = True
        if self.__settings.zmqtopics != dialog.zmqtopics:
            self.__settings.zmqtopics = dialog.zmqtopics
            setsrc = True
        if self.__settings.autozmqtopics != dialog.autozmqtopics:
            self.__settings.autozmqtopics = dialog.autozmqtopics
            setsrc = True
        if setsrc:
            self.__sourceWg.updateMetaData(
                zmqtopics=self.__settings.zmqtopics,
                dirtrans=self.__settings.dirtrans,
                autozmqtopics=self.__settings.autozmqtopics)
            self.__sourceWg.updateLayout()

        self.__settings.statswoscaling = dialog.statswoscaling
        if self.__imageWg.displaywidget.statswoscaling != \
           self.__settings.statswoscaling:
            self.__imageWg.displaywidget.statswoscaling = \
                self.__settings.statswoscaling
            self.plot()

    @QtCore.pyqtSlot(str)
    def setSourceConfiguration(self, sourceConfiguration):
        self._sourceConfiguration = sourceConfiguration
        self.__datasource.setConfiguration(self._sourceConfiguration)

    def setSardana(self, status):
        if status is False:
            self.sardana = None
            self.__imageWg.applyROIButton.setEnabled(False)
            self.__imageWg.fetchROIButton.setEnabled(False)
        else:
            self.sardana = sardanaUtils.SardanaUtils()
            self.__imageWg.applyROIButton.setEnabled(True)
            self.__imageWg.fetchROIButton.setEnabled(True)

    @QtCore.pyqtSlot(int)
    def onSourceChanged(self, status):
        if status:
            self.__datasource = getattr(
                isr, self.__sourceWg.currentDataSource())(
                    self.__settings.timeout)
            self.__sourceWg.updateMetaData(**self.__datasource.getMetaData())

    @QtCore.pyqtSlot(int)
    def updateSource(self, status):
        if status:
            self.__datasource.setTimeOut(self.__settings.timeout)
            self.dataFetcher.data_source = self.__datasource
            if self._sourceConfiguration:
                self.__datasource.setConfiguration(self._sourceConfiguration)
            self.__sourceWg.updateMetaData(**self.__datasource.getMetaData())
        self.updateStateSignal.emit(status)

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
        self.scale(self.__scalingWg.currentScaling())
        # calculate and update the stats for this
        self.calc_update_stats()

        # calls internally the plot function of the plot widget
        if self.image_name is not None and self.scaled_image is not None:
            self.__ui.fileNameLineEdit.setText(self.image_name)
        self.__imageWg.plot(
            self.scaled_image,
            self.display_image
            if self.__settings.statswoscaling else self.scaled_image)
        if self.__updatehisto:
            self.__levelsWg.imageChanged()
            self.__updatehisto = False

    @QtCore.pyqtSlot()
    def calc_update_stats_sec(self):
        self.calc_update_stats(secstream=False)

    def calc_update_stats(self, secstream=True):
        # calculate the stats for this
        maxVal, meanVal, varVal, minVal, maxRawVal, maxSVal = self.calcStats()
        calctime = time.time()
        currentscaling = self.__scalingWg.currentScaling()
        # update the statistics display
        if secstream and self.__settings.secstream and \
           self.scaled_image is not None:
            messagedata = {
                'command': 'alive', 'calctime': calctime, 'maxval': maxVal,
                'maxrawval': maxRawVal,
                'minval': minVal, 'meanval': meanVal, 'pid': self.__apppid,
                'scaling': (
                    'linear'
                    if self.__settings.statswoscaling
                    else currentscaling)}
            topic = 10001
            message = "%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii"))
            self.__settings.secsocket.send_string(str(message))

        self.__statsWg.updateStatistics(
            meanVal, maxVal, varVal,
            'linear' if self.__settings.statswoscaling else currentscaling)

        # if needed, update the level display
        if self.__levelsWg.isAutoLevel():
            self.__levelsWg.updateLevels(float(minVal), float(maxSVal))

    # mode changer: start plotting mode
    @QtCore.pyqtSlot()
    def startPlotting(self):
        # only start plotting if the connection is really established
        if not self.__sourceWg.isConnected():
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
        if self.__datasource is None:
            messageBox.MessageBox.warning(
                self, "lavue: No data source is defined",
                "No data source is defined",
                "Please select the image source")

        if not self.__datasource.connect():
            self.__sourceWg.connectFailure()
            messageBox.MessageBox.warning(
                self, "lavue: The %s connection could not be established"
                % type(self.__datasource).__name__,
                "The %s connection could not be established"
                % type(self.__datasource).__name__,
                "<WARNING> The %s connection could not be established. "
                "Check the settings." % type(self.__datasource))
        else:
            self.__sourceWg.connectSuccess(
                self.__settings.secport if self.__settings.secstream else None)
        if self.__settings.secstream:
            calctime = time.time()
            messagedata = {
                'command': 'start', 'calctime': calctime, 'pid': self.__apppid}
            topic = 10001
            # print(str(messagedata))
            self.__settings.secsocket.send_string("%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii")))
        self.__updatehisto = True

    # call the disconnect function of the hidra interface
    @QtCore.pyqtSlot()
    def disconnect_source(self):
        self.__datasource.disconnect()
        if self.__settings.secstream:
            calctime = time.time()
            messagedata = {
                'command': 'stop', 'calctime': calctime, 'pid': self.__apppid}
            # print(str(messagedata))
            topic = 10001
            self.__settings.secsocket.send_string("%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii")))
        # self.__datasource = None

    @QtCore.pyqtSlot(str, str)
    def getNewData(self, name, metadata=None):
        # check if data is there at all
        if name == "__ERROR__":
            if self.__settings.interruptonerror:
                if self.__sourceWg.isConnected():
                    self.__sourceWg.toggleServerConnection()
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
                        self.__imageWg.updateMetaData(**wgdata)
                    if resdata:
                        self.__sourceWg.updateMetaData(**resdata)
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
            self.__levelsWg.setNumberOfChannels(self.raw_image.shape[0])
            if not self.__levelsWg.colorChannel():
                self.rawgrey_image = np.sum(self.raw_image, 0)
            else:
                try:
                    if len(self.raw_image) >= self.__levelsWg.colorChannel():
                        self.rawgrey_image = self.raw_image[
                            self.__levelsWg.colorChannel() - 1]
                    else:
                        self.rawgrey_image = np.mean(self.raw_image, 0)
                except:
                    import traceback
                    value = traceback.format_exc()
                    text = messageBox.MessageBox.getText(
                        "lavue: color channel %s does not exist."
                        " Reset to grey scale"
                        % self.__levelsWg.colorChannel())
                    messageBox.MessageBox.warning(
                        self,
                        "lavue: color channel %s does not exist. "
                        " Reset to grey scale"
                        % self.__levelsWg.colorChannel(),
                        text, str(value))
                    self.__levelsWg.setChannel(0)
                    self.rawgrey_image = np.sum(self.raw_image, 0)
        else:
            self.rawgrey_image = self.raw_image
            self.__levelsWg.setNumberOfChannels(0)

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

        if self.__settings.showmask and self.applyImageMask and \
           self.maskIndices is not None:
            # set all masked (non-zero values) to zero by index
            try:
                self.display_image[self.maskIndices] = 0
            except IndexError:
                self.__maskWg.noImage()
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
        self.__imageWg.displaywidget.scaling = scalingType
        if self.display_image is None:
            return
        if scalingType == "sqrt":
            self.scaled_image = np.clip(self.display_image, 0, np.inf)
            self.scaled_image = np.sqrt(self.scaled_image)
        elif scalingType == "log":
            self.scaled_image = np.clip(self.display_image, 10e-3, np.inf)
            self.scaled_image = np.log10(self.scaled_image)

    def calcStats(self):
        if self.__settings.statswoscaling and self.display_image is not None:
            maxval = np.amax(self.display_image)
            meanval = np.mean(self.display_image)
            varval = np.var(self.display_image)
            maxsval = np.amax(self.scaled_image)
        elif (not self.__settings.statswoscaling
              and self.scaled_image is not None):
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
            self.__maskWg.noImage()
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
            self.__bkgSubWg.setDisplayedName("")
        else:
            self.__bkgSubWg.checkBkgSubtraction(state)
        self.__imageWg.displaywidget.doBkgSubtraction = state
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
            self.__bkgSubWg.setDisplayedName(str(self.image_name))
        else:
            self.__bkgSubWg.setDisplayedName("")

    @QtCore.pyqtSlot(str)
    def assessTransformation(self, trafoName):
        self.trafoName = trafoName
        self.plot()

    @QtCore.pyqtSlot()
    def setTicks(self):
        if self.__imageWg.setTicks():
            self.plot()
