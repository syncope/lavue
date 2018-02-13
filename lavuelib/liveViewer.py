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
                 "ui", "MainWindow.ui"))


class LiveViewer(QtGui.QMainWindow):

    '''The master class for the dialog, contains all other
    widget and handles communication.'''
    _stateUpdated = QtCore.pyqtSignal(bool)

    def __init__(self, umode=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        #: (:obj:`list` < :obj:`str` > ) source class names
        self.__sourcetypes = []
        if isr.HIDRA:
            self.__sourcetypes.append("HidraSourceWidget")
        if isr.REQUESTS:
            self.__sourcetypes.append("HTTPSourceWidget")
        if isr.PYTANGO:
            self.__sourcetypes.append("TangoAttrSourceWidget")
            self.__sourcetypes.append("TangoFileSourceWidget")
        self.__sourcetypes.append("ZMQSourceWidget")
        self.__sourcetypes.append("TestSourceWidget")

        #: (:obj:`list` < :obj:`str` > ) tool class names
        self.__tooltypes = []
        self.__tooltypes.append("IntensityToolWidget")
        self.__tooltypes.append("ROIToolWidget")
        self.__tooltypes.append("LineCutToolWidget")
        self.__tooltypes.append("AngleQToolWidget")

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

        #: (:class:`lavuelib.settings.Settings`) settings
        self.__settings = settings.Settings()

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
        self.__imagewg = imageWidget.ImageWidget(
            parent=self, tooltypes=self.__tooltypes, settings=self.__settings)

        self.__levelswg.setImageItem(self.__imagewg.image())
        self.__levelswg.updateHistoImage(autoLevel=True)

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
        #: (:obj:`str`) last image name
        self.__lastimagename = None
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

        # # LAYOUT DEFINITIONS
        self.setWindowTitle("laVue: Live Image Viewer")
        self.__ui.confVerticalLayout.addWidget(self.__sourcewg)
        self.__ui.confVerticalLayout.addWidget(self.__prepwg)
        self.__ui.confVerticalLayout.addWidget(self.__scalingwg)
        self.__ui.confVerticalLayout.addWidget(self.__levelswg)
        self.__ui.confVerticalLayout.addWidget(self.__statswg)
        self.__ui.imageVerticalLayout.addWidget(self.__imagewg)
        spacer = QtGui.QSpacerItem(
            0, 0,
            QtGui.QSizePolicy.Minimum,
            QtGui.QSizePolicy.Expanding
        )
        self.__ui.confVerticalLayout.addItem(spacer)
        self.__ui.splitter.setStretchFactor(0, 1)
        self.__ui.splitter.setStretchFactor(1, 10)

        # SIGNAL LOGIC::

        # signal from intensity scaling widget:
        # self.__scalingwg.scalingChanged.connect(self.scale)
        self.__scalingwg.simpleScalingChanged.connect(self._plot)
        self.__scalingwg.scalingChanged.connect(
            self.__levelswg.setScalingLabel)

        # signal from limit setting widget
        self.__levelswg.minLevelChanged.connect(self.__imagewg.setMinLevel)
        self.__levelswg.maxLevelChanged.connect(self.__imagewg.setMaxLevel)
        self.__levelswg.autoLevelsChanged.connect(self.__imagewg.setAutoLevels)
        self.__levelswg.levelsChanged.connect(self._plot)
        self.__ui.cnfPushButton.clicked.connect(self._configuration)
        self.__ui.quitPushButton.clicked.connect(self.close)
        self.__ui.loadPushButton.clicked.connect(self._loadfile)
        if self.__umode in ["user"]:
            self.__ui.cnfPushButton.hide()
        self.__imagewg.roiCoordsChanged.connect(self._calcUpdateStatsSec)
        self.__imagewg.currentToolChanged.connect(
            self._onToolChanged)
        # connecting signals from source widget:
        self.__sourcewg.sourceConnected.connect(self._connectSource)
        self.__sourcewg.sourceConnected.connect(self._startPlotting)

        self.__sourcewg.sourceDisconnected.connect(self._stopPlotting)
        self.__sourcewg.sourceDisconnected.connect(self._disconnectSource)

        # gradient selector
        self.__levelswg.channelChanged.connect(self._plot)
        self.__imagewg.aspectLockedToggled.connect(self._setAspectLocked)

        # simple mutable caching object for data exchange with thread
        #: (:class:`lavuelib.dataFetchTread.ExchangeList`)
        #:    exchange list
        self.__exchangelist = dataFetchThread.ExchangeList()

        #: (:class:`lavuelib.dataFetchTread.DataFetchThread`)
        #:    data fetch thread
        self.__dataFetcher = dataFetchThread.DataFetchThread(
            self.__datasource, self.__exchangelist)
        self.__dataFetcher.newDataNameFetched.connect(self._getNewData)
        # ugly !!! sent current state to the data fetcher...
        self._stateUpdated.connect(self.__dataFetcher.changeStatus)
        self.__sourcewg.sourceStateChanged.connect(self._updateSource)
        self.__sourcewg.sourceChanged.connect(self._onSourceChanged)

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

        self.__sourcewg.configurationChanged.connect(
            self._setSourceConfiguration)

        self.__sourcewg.updateLayout()
        self.__sourcewg.emitSourceChanged()
        self.__imagewg.showCurrentTool()

        self.__loadSettings()

        self._plot()

    def __loadSettings(self):
        """ loads settings from QSettings object
        """
        settings = QtCore.QSettings()
        self.restoreGeometry(
            settings.value("Layout/Geometry").toByteArray())

        status = self.__settings.load(settings)

        for topic, value in status:
            text = messageBox.MessageBox.getText(topic)
            messageBox.MessageBox.warning(self, topic, text, str(value))

        self.__setSardana(self.__settings.sardana)
        self.__imagewg.setAspectLocked(self.__settings.aspectlocked)
        self.__datasource.setTimeOut(self.__settings.timeout)
        dataFetchThread.GLOBALREFRESHRATE = self.__settings.refreshrate
        self.__imagewg.setStatsWOScaling(self.__settings.statswoscaling)

        self.__sourcewg.updateMetaData(
            zmqtopics=self.__settings.zmqtopics,
            dirtrans=self.__settings.dirtrans,
            autozmqtopics=self.__settings.autozmqtopics)

        self.__statswg.changeView(self.__settings.showstats)
        self.__levelswg.changeView(self.__settings.showhisto)
        self.__prepwg.changeView(self.__settings.showmask)

    def __storeSettings(self):
        """ stores settings in QSettings object
        """
        settings = QtCore.QSettings()
        settings.setValue(
            "Layout/Geometry",
            QtCore.QVariant(self.saveGeometry()))

        self.__settings.refreshrate = dataFetchThread.GLOBALREFRESHRATE
        self.__settings.sardana = True if self.__sardana is not None else False
        self.__settings.store(settings)

    @QtCore.pyqtSlot(bool)
    def _setAspectLocked(self, status):
        self.__settings.aspectlocked = status
        self.__imagewg.setAspectLocked(self.__settings.aspectlocked)

    @QtCore.pyqtSlot(str)
    def _onToolChanged(self, text):
        if text == "ROI":
            self.__trafoname = "None"
            self.__trafowg.setEnabled(False)
        elif text == "LineCut":
            self.__trafowg.setEnabled(True)
        elif text == "Angle/Q":
            self.__trafowg.setEnabled(True)
        else:
            self.__trafowg.setEnabled(True)

    def closeEvent(self, event):
        """ stores the setting before finishing the application
        """
        self.__storeSettings()
        self.__settings.secstream = False
        try:
            self.__dataFetcher.newDataNameFetched.disconnect(self._getNewData)
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
    def _loadfile(self):
        """ loads the image file
        """

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
        """ launches the configuration dialog
        """
        cnfdlg = configDialog.ConfigDialog(self)
        if not self.__settings.doorname and self.__sardana is not None:
            self.__settings.doorname = self.__sardana.getDeviceName("Door")
        cnfdlg.sardana = True if self.__sardana is not None else False
        cnfdlg.door = self.__settings.doorname
        cnfdlg.addrois = self.__settings.addrois
        cnfdlg.showhisto = self.__settings.showhisto
        cnfdlg.showmask = self.__settings.showmask
        cnfdlg.showstats = self.__settings.showstats
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
        """ updates the configuration
        """
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
        if self.__settings.showstats != dialog.showstats:
            self.__statswg.changeView(dialog.showstats)
            self.__settings.showstats = dialog.showstats
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
        self.__imagewg.setAspectLocked(self.__settings.aspectlocked)
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
        if self.__imagewg.setStatsWOScaling(self.__settings.statswoscaling):
            self._plot()

    @QtCore.pyqtSlot(str)
    def _setSourceConfiguration(self, sourceConfiguration):
        """ sets the source configuration
        """
        self.__sourceconfiguration = sourceConfiguration
        self.__datasource.setConfiguration(self.__sourceconfiguration)

    def __setSardana(self, status):
        """ sets the sardana utils
        """
        if status is False:
            self.__sardana = None
        else:
            self.__sardana = sardanaUtils.SardanaUtils()
        self.__imagewg.setSardanaUtils(self.__sardana)

    @QtCore.pyqtSlot(int)
    def _onSourceChanged(self, status):
        if status:
            self.__datasource = getattr(
                isr, self.__sourcewg.currentDataSource())(
                    self.__settings.timeout)
            self.__sourcewg.updateMetaData(**self.__datasource.getMetaData())

    @QtCore.pyqtSlot(int)
    def _updateSource(self, status):
        """ update tyhe current source

        :param status: current source status id
        :type status: :obj:`int`
        """
        if status:
            self.__datasource.setTimeOut(self.__settings.timeout)
            self.__dataFetcher.setDataSource(self.__datasource)
            if self.__sourceconfiguration:
                self.__datasource.setConfiguration(self.__sourceconfiguration)
            self.__sourcewg.updateMetaData(**self.__datasource.getMetaData())
        self._stateUpdated.emit(bool(status))

    @QtCore.pyqtSlot()
    def _plot(self, onlynew=False):
        """ The main command of the live viewer class:
        draw a numpy array with the given name.

        :param onlynew: plot only new image
        :type onlynew: :obj:`bool`
        """
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
            self.__levelswg.updateHistoImage()
            self.__updatehisto = False

    @QtCore.pyqtSlot()
    def _calcUpdateStatsSec(self):
        """ calcuates statistics without  sending security stream
        """
        self.__calcUpdateStats(secstream=False)

    def __calcUpdateStats(self, secstream=True):
        """ calcuates statistics

        :param secstream: send security stream flag
        :type secstream: :obj:`bool`
        """
        # calculate the stats for this

        auto = self.__levelswg.isAutoLevel()
        stream = secstream and self.__settings.secstream and \
           self.__scaledimage is not None
        display = self.__settings.showstats
        maxval, meanval, varval, minval, maxrawval, maxsval = \
            self.__calcStats(
                (stream or display,
                 stream or display,
                 display,
                 stream or auto,
                 stream,
                 auto))
        smaxval = "%.4f" % maxval
        smeanval = "%.4f" % meanval
        svarval = "%.4f" % varval
        sminval = "%.3f" % minval
        smaxrawval = "%.4f" % maxrawval
        smaxsval = "%.3f" % maxsval
        calctime = time.time()
        currentscaling = self.__scalingwg.currentScaling()
        # update the statistics display
        if stream:
            messagedata = {
                'command': 'alive', 'calctime': calctime, 'maxval': smaxval,
                'maxrawval': smaxrawval,
                'minval': sminval, 'meanval': smeanval, 'pid': self.__apppid,
                'scaling': (
                    'linear'
                    if self.__settings.statswoscaling
                    else currentscaling)}
            topic = 10001
            message = "%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii"))
            self.__settings.secsocket.send_string(str(message))

        self.__statswg.updateStatistics(
            smeanval, smaxval, svarval,
            'linear' if self.__settings.statswoscaling else currentscaling)

        # if needed, update the level display
        if auto:
            self.__levelswg.updateLevels(minval, maxsval)

    @QtCore.pyqtSlot()
    def _startPlotting(self):
        """ mode changer: start plotting mode.
        It starts plotting if the connection is really established.
        """
        #
        if not self.__sourcewg.isConnected():
            return
        self.__dataFetcher.changeStatus(True)
        print("START %s" % (not self.__dataFetcher.isRunning()))
        if not self.__dataFetcher.isRunning():
            self.__dataFetcher.start()
        else:
            self.__dataFetcher.restart()

    @QtCore.pyqtSlot()
    def _stopPlotting(self):
        """ mode changer: stop plotting mode
        """
        
        if self.__dataFetcher is not None:
            print("STOP PLOTTING")
            # self.__dataFetcher.stop()
            self.__dataFetcher.changeStatus(False)
            pass

    @QtCore.pyqtSlot()
    def _connectSource(self):
        """ calls the connect function of the source interface
        """
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

    @QtCore.pyqtSlot()
    def _disconnectSource(self):
        """ calls the disconnect function of the source interface
        """
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
        """ checks if data is there at all

        :param name: image name
        :type name: :obj:`str`
        :param metadata: JSON dictionary with metadata
        :type metadata: :obj:`str`
        """

        name, rawimage, metadata = self.__exchangelist.readData()

        print("GETNEWDATA %s %s %s %s" % (str(self.__imagename).strip() == str(name).strip(), bool(not metadata), str(self.__imagename).strip(), str(name).strip()))
        if str(self.__imagename).strip() == str(name).strip() and not metadata:
            return
        self.__dataFetcher.changeStatus(False)
        if name == "__ERROR__":
            if self.__settings.interruptonerror:
                if self.__sourcewg.isConnected():
                    self.__sourcewg.toggleServerConnection()
                errortext = rawimage
                messageBox.MessageBox.warning(
                    self, "lavue: Error in reading data",
                    "Viewing will be interrupted", str(errortext))
            self.__dataFetcher.changeStatus(True)
            return
        if name is None:
            self.__dataFetcher.changeStatus(True)
            return
        # first time:
        if str(self.__metadata) != str(metadata) and str(metadata).strip():
            imagename, self.__metadata = name, metadata
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
                self.__imagename, self.__metadata \
                    = name, metadata
                if not isinstance(rawimage, (str, unicode)):
                    self.__rawimage = rawimage
        self._plot(onlynew=True)
        self.__dataFetcher.changeStatus(True)

    def __prepareImage(self):
        """applies: make image gray, substracke the background image and
           apply the mask
        """
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
        """ does the image transformation on the given numpy array.
        """
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
        """ sets scaletype on the image

        :param scalingtype: scaling type
        :type scalingtype: :obj:`str`
        """
        self.__scaledimage = self.__displayimage
        self.__imagewg.setScalingType(scalingtype)
        if self.__displayimage is None:
            return
        if scalingtype == "sqrt":
            self.__scaledimage = np.clip(self.__displayimage, 0, np.inf)
            self.__scaledimage = np.sqrt(self.__scaledimage)
        elif scalingtype == "log":
            self.__scaledimage = np.clip(self.__displayimage, 10e-3, np.inf)
            self.__scaledimage = np.log10(self.__scaledimage)

    def __calcStats(self, flag):
        """ calcualtes scaled limits for intesity levels

        :param flag: (max value, mean value, variance value,
                  min scaled value, max raw value, max scaled value)
                  to calculate
        :type flag: [:obj:`bool`, :obj:`bool`, :obj:`bool`,
                       :obj:`bool`, :obj:`bool`, :obj:`bool`]
        :returns: max value, mean value, variance value,
                  min scaled value, max raw value, max scaled value
        :rtype: [:obj:`str`, :obj:`str`, :obj:`str`, :obj:`str`,
                    :obj:`str`, :obj:`str`]
        """
        if self.__settings.statswoscaling and self.__displayimage is not None:
            maxval = np.amax(self.__displayimage) if flag[0] else 0.0
            meanval = np.mean(self.__displayimage) if flag[1] else 0.0
            varval = np.var(self.__displayimage) if flag[2] else 0.0
            maxsval = np.amax(self.__scaledimage) if flag[5] else 0.0
        elif (not self.__settings.statswoscaling
              and self.__scaledimage is not None):
            maxval = np.amax(self.__scaledimage) if flag[0] else 0.0
            meanval = np.mean(self.__scaledimage) if flag[1] else 0.0
            varval = np.var(self.__scaledimage) if flag[2] else 0.0
            maxsval = maxval
        else:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        maxrawval = np.amax(self.__rawgreyimage) if flag[4] else 0.0
        # automatic maximum clipping to hardcoded value
        try:
            if flag[0] and flag[1] and flag[2]:
                checkval = meanval + 10 * np.sqrt(varval)
                if maxval > checkval:
                    maxval = checkval
        except:
            print("Warning in calculating checkval from:"
                  " meanval = %s,  varval = %s" % (meanval, varval))
        minval = np.amin(self.__scaledimage) if flag[3] else 0.0
        return (maxval, meanval, varval, minval, maxrawval,  maxsval)

    @QtCore.pyqtSlot(int)
    def _checkMasking(self, state):
        """ replots the image with mask if mask exists
        """
        self.__applymask = state
        if self.__applymask and self.__maskimage is None:
            self.__maskwg.noImage()
        self._plot()

    @QtCore.pyqtSlot(str)
    def _prepareMasking(self, imagename):
        """ reads the mask image, select non-zero elements and store the indices
        """
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
        """ replots the image with subtranction if background image exists
        """
        self.__dobkgsubtraction = state
        if self.__dobkgsubtraction and self.__backgroundimage is None:
            self.__bkgSubwg.setDisplayedName("")
        else:
            self.__bkgSubwg.checkBkgSubtraction(state)
        self.__imagewg.setDoBkgSubtraction(state)
        self._plot()

    @QtCore.pyqtSlot(str)
    def _prepareBkgSubtraction(self, imagename):
        """ reads the background image
        """
        self.__backgroundimage = np.transpose(
            imageFileHandler.ImageFileHandler(
                str(imagename)).getImage())

    @QtCore.pyqtSlot()
    def _setCurrentImageAsBkg(self):
        """ sets the chrrent image as the background image
        """
        if self.__rawgreyimage is not None:
            self.__backgroundimage = self.__rawgreyimage
            self.__bkgSubwg.setDisplayedName(str(self.__imagename))
        else:
            self.__bkgSubwg.setDisplayedName("")

    @QtCore.pyqtSlot(str)
    def _assessTransformation(self, trafoname):
        """ assesses the transformation and replot it
        """
        self.__trafoname = trafoname
        self._plot()
