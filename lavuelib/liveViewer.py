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
    _updateStateSignal = QtCore.pyqtSignal(int)

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

        #: (:class:`lavuelib.sardanaUtils.SardanaUtils`)
        #:  sardana utils
        self.__sardana = None

        # WIDGET DEFINITIONS
        #: (:class:`lavuelib.sourceGroupBox.SourceGroupBox`) source groupbox
        self.__sourcewg = sourceGroupBox.SourceGroupBox(
            parent=self, sourcetypes=self.__sourcetypes)
        self.__sourcewg.updateMetaData(serverdict=HIDRASERVERLIST)

        #: (:class:`lavuelib.preparationGroupBox.PreparationGroupBox`)
        #: preparation groupbox
        self.__prepwg = preparationGroupBox.PreparationGroupBox(parent=self)
        #: (:class:`lavuelib.scalingGroupBox.ScalingGroupBox`) scaling groupbox
        self.__scalingwg = scalingGroupBox.ScalingGroupBox(parent=self)
        #: (:class:`lavuelib.levelsGroupBox.LevelsGroupBox`) level groupbox
        self.__levelswg = levelsGroupBox.LevelsGroupBox(parent=self)
        #: (:class:`lavuelib.statisticsGroupBox.StatisticsGroupBox`)
        #:     statistic groupbox
        self.__statswg = statisticsGroupBox.StatisticsGroupBox(parent=self)
        #: (:class:`lavuelib.imageWidget.ImageWidget`) image widget
        self.__imagewg = imageWidget.ImageWidget(parent=self)

        self.__levelswg.setImageItem(self.__imagewg.displaywidget.image)
        self.__levelswg.imageChanged(autoLevel=True)

        #: (:class:`lavuelib.maskWidget.MaskWidget`) mask widget
        self.__maskwg = self.__prepwg.maskWidget
        #: (:class:`lavuelib.bkgSubtractionWidget.BkgSubtractionWidget`)
        #:    background subtraction widget
        self.__bkgSubwg = self.__prepwg.bkgSubWidget
        #: (:class:`lavuelib.transformationsWidget.TransformationsWidget`)
        #:    transformations widget
        self.__trafowg = self.__prepwg.trafoWidget

        # keep a reference to the "raw" image and the current filename
        #: (:class:`numpy.ndarray`) raw image
        self.__rawimage = None
        #: (:class:`numpy.ndarray`) raw gray image
        self.__rawgreyimage = None
        #: (:obj:`str`) image name
        self.__imagename = None
        #: (:obj:`str`) metadata JSON dictionary
        self.__metadata = ""
        #: (:class:`numpy.ndarray`) displayed image after preparation
        self.__displayimage = None
        #: (:class:`numpy.ndarray`) scaled displayed image
        self.__scaledimage = None

        #: (:class:`numpy.ndarray`) background image
        self.__backgroundimage = None
        #: (:obj:`bool`) apply background image subtraction
        self.__dobkgsubtraction = False

        #: (:class:`numpy.ndarray`) mask image
        self.__maskimage = None
        #: (:class:`numpy.ndarray`) mask image indices
        self.__maskindices = None
        #: (:obj:`bool`) apply mask
        self.__applymask = False

        #: (:obj:`str`) source configuration string
        self.__sourceconfiguration = None

        #: (:obj:`str`) transformation name
        self.__trafoname = "None"

        #: (:class:`Ui_LevelsGroupBox') ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        self.__settings = settings.Settings()

        # # LAYOUT DEFINITIONS
        self.setWindowTitle("laVue: Live Image Viewer")
        self.__ui.confVerticalLayout.addWidget(self.__sourcewg)
        self.__ui.confVerticalLayout.addWidget(self.__prepwg)
        self.__ui.confVerticalLayout.addWidget(self.__scalingwg)
        self.__ui.confVerticalLayout.addWidget(self.__levelswg)
        self.__ui.confVerticalLayout.addWidget(self.__statswg)
        self.__ui.imageVerticalLayout.addWidget(self.__imagewg)
        self.__ui.splitter.setStretchFactor(0, 1)
        self.__ui.splitter.setStretchFactor(1, 10)

        # SIGNAL LOGIC::

        # signal from intensity scaling widget:
        # self.__scalingwg.scalingChanged.connect(self.scale)
        self.__scalingwg.scalingChanged.connect(self._plot)
        self.__scalingwg.scalingChanged.connect(
            self.__levelswg.setScalingLabel)

        # signal from limit setting widget
        self.__levelswg.minLevelChanged.connect(self.__imagewg.setMinLevel)
        self.__levelswg.maxLevelChanged.connect(self.__imagewg.setMaxLevel)
        self.__levelswg.autoLevelsChanged.connect(self.__imagewg.setAutoLevels)
        self.__levelswg.levelsChanged.connect(self._plot)
        self.__levelswg.changeView(self.__settings.showhisto)
        self.__ui.cnfPushButton.clicked.connect(self._configuration)
        self.__ui.quitPushButton.clicked.connect(self.close)
        self.__ui.loadPushButton.clicked.connect(self._loadfile)
        if self.__umode in ["user"]:
            self.__ui.cnfPushButton.hide()
        self.__imagewg.applyROIButton.clicked.connect(self._onapplyrois)
        self.__imagewg.fetchROIButton.clicked.connect(self._onfetchrois)
        self.__imagewg.roiCoordsChanged.connect(self._calcUpdateStatsSec)
        self.__imagewg.pixelComboBox.currentIndexChanged.connect(
            self._onPixelChanged)
        # connecting signals from source widget:
        self.__sourcewg.sourceConnectSignal.connect(self._connectSource)
        self.__sourcewg.sourceConnectSignal.connect(self._startPlotting)

        self.__sourcewg.sourceDisconnectSignal.connect(self._stopPlotting)
        self.__sourcewg.sourceDisconnectSignal.connect(self._disconnectSource)

        # gradient selector
        self.__levelswg.channelChanged.connect(self._plot)
        self.__imagewg.displaywidget.setaspectlocked.triggered.connect(
            self._toggleAspectLocked)
        self.__imagewg.ticksPushButton.clicked.connect(self._setTicks)

        # simple mutable caching object for data exchange with thread
        #: (:class:`lavuelib.dataFetchTread.ExchangeList`)
        #:    exchange list
        self.__exchangelist = dataFetchThread.ExchangeList()

        #: (:class:`lavuelib.dataFetchTread.DataFetchThread`)
        #:    data fetch thread
        self.__dataFetcher = dataFetchThread.DataFetchThread(
            self.__datasource, self.__exchangelist)
        self.__dataFetcher.newDataName.connect(self._getNewData)
        # ugly !!! sent current state to the data fetcher...
        self._updateStateSignal.connect(self.__dataFetcher.changeStatus)
        self.__sourcewg.sourceStateSignal.connect(self._updateSource)
        self.__sourcewg.sourceChangedSignal.connect(self._onSourceChanged)

        self.__bkgSubwg.bkgFileSelected.connect(self._prepareBkgSubtraction)
        self.__bkgSubwg.useCurrentImageAsBkg.connect(
            self._setCurrentImageAsBkg)
        self.__bkgSubwg.applyStateChanged.connect(self._checkBkgSubtraction)

        self.__maskwg.maskFileSelected.connect(self._prepareMasking)
        self.__maskwg.applyStateChanged.connect(self._checkMasking)

        # signals from transformation widget
        self.__trafowg.transformationChanged.connect(
            self._assessTransformation)

        # set the right target name for the source display at initialization

        self.__sourcewg.configurationSignal.connect(
            self._setSourceConfiguration)

        self.__sourcewg.updateLayout()
        self.__sourcewg.emitSourceChangedSignal()
        self._onPixelChanged()

        self.__loadSettings()

        self._plot()

    def __loadSettings(self):
        settings = QtCore.QSettings()
        self.restoreGeometry(
            settings.value("Layout/Geometry").toByteArray())

        status = self.__settings.load(settings)

        for topic, value in status:
            text = messageBox.MessageBox.getText(topic)
            messageBox.MessageBox.warning(self, topic, text, str(value))

        self.__setSardana(self.__settings.sardana)
        self.__imagewg.displaywidget.setAspectLocked(
            self.__settings.aspectlocked)
        self.__datasource.setTimeOut(self.__settings.timeout)
        dataFetchThread.GLOBALREFRESHRATE = self.__settings.refreshrate
        self.__imagewg.displaywidget.statswoscaling = \
            self.__settings.statswoscaling

        self.__sourcewg.updateMetaData(
            zmqtopics=self.__settings.zmqtopics,
            dirtrans=self.__settings.dirtrans,
            autozmqtopics=self.__settings.autozmqtopics)

        self.__levelswg.changeView(self.__settings.showhisto)
        self.__prepwg.changeView(self.__settings.showmask)

    def __storeSettings(self):
        """ Stores settings in QSettings object
        """
        settings = QtCore.QSettings()
        settings.setValue(
            "Layout/Geometry",
            QtCore.QVariant(self.saveGeometry()))

        self.__settings.refreshrate = dataFetchThread.GLOBALREFRESHRATE
        self.__settings.sardana = True if self.__sardana is not None else False
        self.__settings.store(settings)

    @QtCore.pyqtSlot(bool)
    def _toggleAspectLocked(self, status):
        self.__settings.aspectlocked = status
        self.__imagewg.displaywidget.setAspectLocked(
            self.__settings.aspectlocked)

    @QtCore.pyqtSlot(int)
    def _onPixelChanged(self):
        text = self.__imagewg.pixelComboBox.currentText()
        if text == "ROI":
            self.__trafoname = "None"
            self.__trafowg.setEnabled(False)
        elif text == "LineCut":
            self.__trafowg.setEnabled(True)
        elif text == "Angle/Q":
            self.__trafowg.setEnabled(True)
        else:
            self.__trafowg.setEnabled(True)
        self.__imagewg.onPixelChanged(text)

    @QtCore.pyqtSlot()
    def _onapplyrois(self):
        if isr.PYTANGO:
            roicoords = self.__imagewg.displaywidget.roicoords
            roispin = self.__imagewg.roiSpinBox.value()
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

            rlabel = str(self.__imagewg.labelROILineEdit.text())
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

    def closeEvent(self, event):
        """ stores the setting before finishing the application
        """
        self.__storeSettings()
        self.__settings.secstream = False
        try:
            self.__dataFetcher.newDataName.disconnect(self._getNewData)
        except:
            pass
        # except Exception as e:
        #     print (str(e))
        if self.__sourcewg.isConnected():
            self.__sourcewg.toggleServerConnection()
        self._disconnectSource()
        time.sleep(min(dataFetchThread.GLOBALREFRESHRATE * 5, 2))
        self.__dataFetcher.stop()
        self.__settings.seccontext.destroy()
        QtGui.QApplication.closeAllWindows()
        event.accept()

    @QtCore.pyqtSlot()
    def _onfetchrois(self):
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
            rlabel = str(self.__imagewg.labelROILineEdit.text())
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
            self.__imagewg.labelROILineEdit.setText(" ".join(slabel))
            self.__imagewg.updateROIButton()
            self.__imagewg.roiNrChanged(len(coords), coords)
        else:
            print("Connection error")

    @QtCore.pyqtSlot()
    def _loadfile(self):
        fileDialog = QtGui.QFileDialog()
        imagename = str(
            fileDialog.getOpenFileName(
                self, 'Load file', self.__settings.imagename or '.'))
        if imagename:
            self.__settings.imagename = imagename
            newimage = imageFileHandler.ImageFileHandler(
                str(self.__settings.imagename)).getImage()
            if newimage is not None:
                self.__imagename = self.__settings.imagename
                self.__rawimage = np.transpose(newimage)
                self._plot()
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
    def _configuration(self):
        cnfdlg = configDialog.ConfigDialog(self)
        if not self.__settings.doorname and self.__sardana is not None:
            self.__settings.doorname = self.__sardana.getDeviceName("Door")
        cnfdlg.sardana = True if self.__sardana is not None else False
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
        if dialog.sardana != (True if self.__sardana is not None else False):
            self.__setSardana(dialog.sardana)
            self.__settings.sardana = dialog.sardana
        self.__settings.addrois = dialog.addrois

        if self.__settings.showhisto != dialog.showhisto:
            self.__levelswg.changeView(dialog.showhisto)
            self.__settings.showhisto = dialog.showhisto
        if self.__settings.showmask != dialog.showmask:
            self.__prepwg.changeView(dialog.showmask)
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
                if self.__sourcewg.isConnected():
                    self.__sourcewg.connectSuccess(None)
            if dialog.secstream:
                if dialog.secautoport:
                    self.__settings.secsockopt = "tcp://*:*"
                    self.__settings.secsocket.bind(self.__settings.secsockopt)
                    dialog.secport = self.__settings.secsocket.getsockopt(
                        zmq.LAST_ENDPOINT).split(":")[-1]
                else:
                    self.__settings.secsockopt = "tcp://*:%s" % dialog.secport
                    self.__settings.secsocket.bind(self.__settings.secsockopt)
                if self.__sourcewg.isConnected():
                    self.__sourcewg.connectSuccess(dialog.secport)
        self.__settings.secautoport = dialog.secautoport
        self.__settings.secport = dialog.secport
        self.__settings.timeout = dialog.timeout
        self.__datasource.setTimeOut(self.__settings.timeout)
        self.__settings.aspectlocked = dialog.aspectlocked
        self.__imagewg.displaywidget.setAspectLocked(
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
            self.__sourcewg.updateMetaData(
                zmqtopics=self.__settings.zmqtopics,
                dirtrans=self.__settings.dirtrans,
                autozmqtopics=self.__settings.autozmqtopics)
            self.__sourcewg.updateLayout()

        self.__settings.statswoscaling = dialog.statswoscaling
        if self.__imagewg.displaywidget.statswoscaling != \
           self.__settings.statswoscaling:
            self.__imagewg.displaywidget.statswoscaling = \
                self.__settings.statswoscaling
            self._plot()

    @QtCore.pyqtSlot(str)
    def _setSourceConfiguration(self, sourceConfiguration):
        self.__sourceconfiguration = sourceConfiguration
        self.__datasource.setConfiguration(self.__sourceconfiguration)

    def __setSardana(self, status):
        if status is False:
            self.__sardana = None
            self.__imagewg.applyROIButton.setEnabled(False)
            self.__imagewg.fetchROIButton.setEnabled(False)
        else:
            self.__sardana = sardanaUtils.SardanaUtils()
            self.__imagewg.applyROIButton.setEnabled(True)
            self.__imagewg.fetchROIButton.setEnabled(True)

    @QtCore.pyqtSlot(int)
    def _onSourceChanged(self, status):
        if status:
            self.__datasource = getattr(
                isr, self.__sourcewg.currentDataSource())(
                    self.__settings.timeout)
            self.__sourcewg.updateMetaData(**self.__datasource.getMetaData())

    @QtCore.pyqtSlot(int)
    def _updateSource(self, status):
        if status:
            self.__datasource.setTimeOut(self.__settings.timeout)
            self.__dataFetcher.data_source = self.__datasource
            if self.__sourceconfiguration:
                self.__datasource.setConfiguration(self.__sourceconfiguration)
            self.__sourcewg.updateMetaData(**self.__datasource.getMetaData())
        self._updateStateSignal.emit(status)

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def _plot(self):
        """ The main command of the live viewer class:
        draw a numpy array with the given name."""
        # prepare or preprocess the raw image if present:
        self.__prepareImage()

        # perform transformation
        self.__transform()

        # use the internal raw image to create a display image with chosen
        # scaling
        self.__scale(self.__scalingwg.currentScaling())
        # calculate and update the stats for this
        self.__calcUpdateStats()

        # calls internally the plot function of the plot widget
        if self.__imagename is not None and self.__scaledimage is not None:
            self.__ui.fileNameLineEdit.setText(self.__imagename)
        self.__imagewg.plot(
            self.__scaledimage,
            self.__displayimage
            if self.__settings.statswoscaling else self.__scaledimage)
        if self.__updatehisto:
            self.__levelswg.imageChanged()
            self.__updatehisto = False

    @QtCore.pyqtSlot()
    def _calcUpdateStatsSec(self):
        self.__calcUpdateStats(secstream=False)

    def __calcUpdateStats(self, secstream=True):
        # calculate the stats for this
        maxVal, meanVal, varVal, minVal, maxRawVal, maxSVal = \
            self.__calcStats()
        calctime = time.time()
        currentscaling = self.__scalingwg.currentScaling()
        # update the statistics display
        if secstream and self.__settings.secstream and \
           self.__scaledimage is not None:
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

        self.__statswg.updateStatistics(
            meanVal, maxVal, varVal,
            'linear' if self.__settings.statswoscaling else currentscaling)

        # if needed, update the level display
        if self.__levelswg.isAutoLevel():
            self.__levelswg.updateLevels(float(minVal), float(maxSVal))

    # mode changer: start plotting mode
    @QtCore.pyqtSlot()
    def _startPlotting(self):
        # only start plotting if the connection is really established
        if not self.__sourcewg.isConnected():
            return
        self.__dataFetcher.start()

    # mode changer: stop plotting mode
    @QtCore.pyqtSlot()
    def _stopPlotting(self):
        if self.__dataFetcher is not None:
            pass

    # call the connect function of the source interface
    @QtCore.pyqtSlot()
    def _connectSource(self):
        if self.__datasource is None:
            messageBox.MessageBox.warning(
                self, "lavue: No data source is defined",
                "No data source is defined",
                "Please select the image source")

        if not self.__datasource.connect():
            self.__sourcewg.connectFailure()
            messageBox.MessageBox.warning(
                self, "lavue: The %s connection could not be established"
                % type(self.__datasource).__name__,
                "The %s connection could not be established"
                % type(self.__datasource).__name__,
                "<WARNING> The %s connection could not be established. "
                "Check the settings." % type(self.__datasource))
        else:
            self.__sourcewg.connectSuccess(
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
    def _disconnectSource(self):
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
    def _getNewData(self, name, metadata=None):
        # check if data is there at all
        if name == "__ERROR__":
            if self.__settings.interruptonerror:
                if self.__sourcewg.isConnected():
                    self.__sourcewg.toggleServerConnection()
                _, errortext, _ = self.__exchangelist.readData()
                messageBox.MessageBox.warning(
                    self, "lavue: Error in reading data",
                    "Viewing will be interrupted", str(errortext))
            return
        if name is None:
            return
        # first time:
        if str(self.__metadata) != str(metadata) and str(metadata).strip():
            imagename, rawimage, self.__metadata = \
                self.__exchangelist.readData()
            if str(imagename).strip() and \
               not isinstance(rawimage, (str, unicode)):
                self.__imagename = imagename
                self.__rawimage = rawimage
            try:
                mdata = json.loads(str(metadata))
                if isinstance(mdata, dict):
                    resdata = dict((k, v) for (k, v) in mdata.items()
                                   if k in self.__allowedmdata)
                    wgdata = dict((k, v) for (k, v) in mdata.items()
                                  if k in self.__allowedwgdata)
                    if wgdata:
                        self.__imagewg.updateMetaData(**wgdata)
                    if resdata:
                        self.__sourcewg.updateMetaData(**resdata)
            except Exception as e:
                print(str(e))
        elif str(name).strip():
            if self.__imagename is None or str(self.__imagename) != str(name):
                self.__imagename, rawimage, self.__metadata \
                    = self.__exchangelist.readData()
                if not isinstance(rawimage, (str, unicode)):
                    self.__rawimage = rawimage
        self._plot()

    def __prepareImage(self):
        if self.__rawimage is None:
            return

        if len(self.__rawimage.shape) == 3:
            self.__levelswg.setNumberOfChannels(self.__rawimage.shape[0])
            if not self.__levelswg.colorChannel():
                self.__rawgreyimage = np.sum(self.__rawimage, 0)
            else:
                try:
                    if len(self.__rawimage) >= self.__levelswg.colorChannel():
                        self.__rawgreyimage = self.__rawimage[
                            self.__levelswg.colorChannel() - 1]
                    else:
                        self.__rawgreyimage = np.mean(self.__rawimage, 0)
                except:
                    import traceback
                    value = traceback.format_exc()
                    text = messageBox.MessageBox.getText(
                        "lavue: color channel %s does not exist."
                        " Reset to grey scale"
                        % self.__levelswg.colorChannel())
                    messageBox.MessageBox.warning(
                        self,
                        "lavue: color channel %s does not exist. "
                        " Reset to grey scale"
                        % self.__levelswg.colorChannel(),
                        text, str(value))
                    self.__levelswg.setChannel(0)
                    self.__rawgreyimage = np.sum(self.__rawimage, 0)
        else:
            self.__rawgreyimage = self.__rawimage
            self.__levelswg.setNumberOfChannels(0)

        self.__displayimage = self.__rawgreyimage

        if self.__dobkgsubtraction and self.__backgroundimage is not None:
            # simple subtraction
            try:
                self.__displayimage = \
                    self.__rawgreyimage - self.__backgroundimage
            except:
                self._checkBkgSubtraction(False)
                self.__backgroundimage = None
                self.__dobkgsubtraction = False
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "lavue: Background image does not match "
                    "to the current image")
                messageBox.MessageBox.warning(
                    self, "lavue: Background image does not match "
                    "to the current image",
                    text, str(value))

        if self.__settings.showmask and self.__applymask and \
           self.__maskindices is not None:
            # set all masked (non-zero values) to zero by index
            try:
                self.__displayimage[self.__maskindices] = 0
            except IndexError:
                self.__maskwg.noImage()
                self.__applymask = False
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "lavue: Mask image does not match "
                    "to the current image")
                messageBox.MessageBox.warning(
                    self, "lavue: Mask image does not match "
                    "to the current image",
                    text, str(value))

    def __transform(self):
        '''Do the image transformation on the given numpy array.'''
        if self.__displayimage is None or self.__trafoname is "none":
            return

        elif self.__trafoname == "flip (up-down)":
            self.__displayimage = np.fliplr(self.__displayimage)
        elif self.__trafoname == "flip (left-right)":
            self.__displayimage = np.flipud(self.__displayimage)
        elif self.__trafoname == "transpose":
            self.__displayimage = np.transpose(self.__displayimage)
        elif self.__trafoname == "rot90 (clockwise)":
            # self.__displayimage = np.rot90(self.__displayimage, 3)
            self.__displayimage = np.transpose(
                np.flipud(self.__displayimage))
        elif self.__trafoname == "rot180":
            self.__displayimage = np.flipud(
                np.fliplr(self.__displayimage))
        elif self.__trafoname == "rot270 (clockwise)":
            # self.__displayimage = np.rot90(self.__displayimage, 1)
            self.__displayimage = np.transpose(
                np.fliplr(self.__displayimage))
        elif self.__trafoname == "rot180 + transpose":
            self.__displayimage = np.transpose(
                np.fliplr(np.flipud(self.__displayimage)))

    def __scale(self, scalingtype):
        self.__scaledimage = self.__displayimage
        self.__imagewg.displaywidget.scaling = scalingtype
        if self.__displayimage is None:
            return
        if scalingtype == "sqrt":
            self.__scaledimage = np.clip(self.__displayimage, 0, np.inf)
            self.__scaledimage = np.sqrt(self.__scaledimage)
        elif scalingtype == "log":
            self.__scaledimage = np.clip(self.__displayimage, 10e-3, np.inf)
            self.__scaledimage = np.log10(self.__scaledimage)

    def __calcStats(self):
        if self.__settings.statswoscaling and self.__displayimage is not None:
            maxval = np.amax(self.__displayimage)
            meanval = np.mean(self.__displayimage)
            varval = np.var(self.__displayimage)
            maxsval = np.amax(self.__scaledimage)
        elif (not self.__settings.statswoscaling
              and self.__scaledimage is not None):
            maxval = np.amax(self.__scaledimage)
            meanval = np.mean(self.__scaledimage)
            varval = np.var(self.__scaledimage)
            maxsval = maxval
        else:
            return "0.", "0.", "0.", "0.", "0.", "0."
        maxrawval = np.amax(self.__rawgreyimage)
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
                str("%.3f" % np.amin(self.__scaledimage)),
                str("%.4f" % maxrawval),
                str("%.3f" % maxsval))

    @QtCore.pyqtSlot(int)
    def _checkMasking(self, state):
        self.__applymask = state
        if self.__applymask and self.__maskimage is None:
            self.__maskwg.noImage()
        self._plot()

    @QtCore.pyqtSlot(str)
    def _prepareMasking(self, imagename):
        '''Get the mask image, select non-zero elements
        and store the indices.'''
        if imagename:
            self.__maskimage = np.transpose(
                imageFileHandler.ImageFileHandler(
                    str(imagename)).getImage())
            self.__maskindices = (self.__maskimage != 0)
        else:
            self.__maskimage = None
        # self.__maskindices = np.nonzero(self.__maskimage != 0)

    @QtCore.pyqtSlot(int)
    def _checkBkgSubtraction(self, state):
        self.__dobkgsubtraction = state
        if self.__dobkgsubtraction and self.__backgroundimage is None:
            self.__bkgSubwg.setDisplayedName("")
        else:
            self.__bkgSubwg.checkBkgSubtraction(state)
        self.__imagewg.displaywidget.doBkgSubtraction = state
        self._plot()

    @QtCore.pyqtSlot(str)
    def _prepareBkgSubtraction(self, imagename):
        self.__backgroundimage = np.transpose(
            imageFileHandler.ImageFileHandler(
                str(imagename)).getImage())

    @QtCore.pyqtSlot()
    def _setCurrentImageAsBkg(self):
        if self.__rawgreyimage is not None:
            self.__backgroundimage = self.__rawgreyimage
            self.__bkgSubwg.setDisplayedName(str(self.__imagename))
        else:
            self.__bkgSubwg.setDisplayedName("")

    @QtCore.pyqtSlot(str)
    def _assessTransformation(self, trafoname):
        self.__trafoname = trafoname
        self._plot()

    @QtCore.pyqtSlot()
    def _setTicks(self):
        if self.__imagewg.setTicks():
            self._plot()
