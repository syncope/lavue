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

""" image source selection """

from .qtuic import uic
from pyqtgraph import QtCore, QtGui
import os
import json

from . import sourceWidget as swgm

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "SourceTabWidget.ui"))

_sformclass, _sbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "SourceForm.ui"))


class SourceForm(QtGui.QWidget):

    """ source form """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source connected signal
    sourceConnected = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source state signal
    sourceStateChanged = QtCore.pyqtSignal(int, int)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source state signal
    sourceChanged = QtCore.pyqtSignal(int)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source label name signal
    sourceLabelChanged = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) add Icon Clicked signal
    addIconClicked = QtCore.pyqtSignal(str, str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) remove Icon Clicked signal
    removeIconClicked = QtCore.pyqtSignal(str, str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) push button clicked signal
    pushButtonClicked = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) translation changed signal
    translationChanged = QtCore.pyqtSignal(str, int)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) push button enabled signal
    buttonEnabled = QtCore.pyqtSignal(bool, int)

    def __init__(self, parent=None, sourceid=0):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        :param expertmode: expert mode flag
        :type expertmode: :obj:`bool`
        :param sourceid: source id
        :type sourceid: :obj:`int`
        """
        QtGui.QWidget.__init__(self, parent)

        #: (:obj:`bool`) if image source connected
        self.__connected = False

        #: (:class:`lavuelib.sourceWidget.SourceBaseWidget`)
        #:      current source widget
        self.__currentSource = None

        #:  (:obj:`str`) default datasource
        self.__defaultsource = "Hidra"

        #: (:obj:`list` < :obj:`str` > ) source names
        self.__sourcenames = []
        #: (:obj:`dict` < :obj:`str`,
        #:      :class:`lavuelib.sourceWidget.SourceBaseWidget` >)
        #:           source names
        self.__sourcewidgets = {}

        #: (:obj:`int`) source id
        self.__sourceid = sourceid

        # (:obj:`str`) error status
        self.__errorstatus = ""

        #: (:obj:`list` < :obj:`str` > ) source tab widgets
        self.__sourcetabs = []

        #: (:obj:`list` < :class:`PyQt5.QtGui.QWidget` > ) datasource names
        self.__subwidgets = []

        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "sourceTypeLabel", "sourceTypeLabel",
            "translationLabel", "translationEditLine",
            "cStatusLabel", "cStatusLineEdit",
            "activeCheckBox", "pushButton",
        ]

        self._ui = _sformclass()
        self._ui.setupUi(self)

    def init(self):
        """ initialize widget
        """
        self._ui.sourceTypeComboBox.currentIndexChanged.connect(
            self.onSourceChanged)
        self.onSourceChanged()

    def disconnectWidget(self):
        """ disconnect widget
        """
        self._ui.cStatusLineEdit.setStyleSheet(
            "color: yellow;"
            "background-color: red;")
        self._ui.cStatusLineEdit.setText("Disconnected")
        if not self.__sourceid:
            self._ui.pushButton.setText("&Start")
        self.__connected = False
        self._ui.sourceTypeComboBox.setEnabled(True)
        if self.__currentSource is not None:
            self.__currentSource.disconnectWidget()

    def connectWidget(self):
        """ connect widget
        """
        self._ui.sourceTypeComboBox.setEnabled(False)
        if self.__currentSource is not None:
            self.__currentSource.connectWidget()

    def currentDataSource(self):
        """ current data source

        :returns: current datasource class name
        :rtype: :obj:`str`
        """
        if self.__currentSource is not None:
            return self.__currentSource.datasource

    def currentDataSourceName(self):
        """ current data source name

        :returns: current datasource class name
        :rtype: :obj:`str`
        """
        return self.__currentSource.name

    def gridLayout(self):
        """ provide grid layout

        :returns: grid layout
        :rtype: :class:`PyQt5.QtGui.QGridLayout`
        """
        return self._ui.formGridLayout

    def pushButtonEnabled(self):
        """ provide status of push button

        :returns: if push button enabled
        :rtype: :obj:`bool`
        """
        return self._ui.pushButton.isEnabled()

    def removeCommonWidgets(self):
        """ remove common widgets
        """
        layout = self.gridLayout()
        layout.removeWidget(self._ui.cStatusLabel)
        layout.removeWidget(self._ui.cStatusLineEdit)
        layout.removeWidget(self._ui.translationLabel)
        layout.removeWidget(self._ui.translationLineEdit)
        layout.removeWidget(self._ui.pushButton)

    def addCommonWidgets(self, sln):
        """ add common widgets after given row in the grid layout

        :param sln: given row in the grid layout
        :type sln: :obj:`int`
        """
        layout = self.gridLayout()
        layout.addWidget(self._ui.cStatusLabel, sln + 1, 0)
        layout.addWidget(self._ui.cStatusLineEdit, sln + 1, 1)
        layout.addWidget(self._ui.translationLabel, sln + 2, 0)
        layout.addWidget(self._ui.translationLineEdit, sln + 2, 1)
        if self.__sourceid:
            self._ui.pushButton.hide()
        else:
            layout.addWidget(self._ui.pushButton, sln + 3, 1)
            self._ui.pushButton.clicked.connect(
                self.toggleServerConnection)
        self._ui.translationLineEdit.textEdited.connect(
            self.emitTranslationChanged)
        self._ui.sourceTypeComboBox.setCurrentIndex(0)

    def showItem(self, trans):
        """ show items of the widget

        :param trans: translation item show status
        :type trans: :obj:`bool`
        """
        if trans:
            self._ui.translationLineEdit.show()
            self._ui.translationLabel.show()
        else:
            self._ui.translationLineEdit.hide()
            self._ui.translationLabel.hide()

    def addWidgets(self, st, expertmode):
        """ add widgets

        :param st: source type class
        :type st: :class:`sourceWidget.SourceBaseWidget`
        :param expertmode:  expert mode
        :type expertmode: :obj:`bool`
        """
        layout = self.gridLayout()
        swg = getattr(swgm, st)()
        swg.expertmode = expertmode
        self.__sourcewidgets[swg.name] = swg
        self.__sourcenames.append(swg.name)
        self._ui.sourceTypeComboBox.addItem(swg.name)
        widgets = zip(swg.widgets[0::2], swg.widgets[1::2])
        for wg1, wg2 in widgets:
            sln = len(self.__subwidgets)
            layout.addWidget(wg1, sln + 1, 0)
            layout.addWidget(wg2, sln + 1, 1)
            self.__subwidgets.append([wg1, wg2])
        return len(self.__subwidgets)

    def sourceStatus(self):
        """ source status

        :returns: source type id
        :rtype: :obj:`int`
        """
        return self._ui.sourceTypeComboBox.currentIndex() + 1

    def updateLayout(self):
        """ update source layout
        """
        if hasattr(self.__currentSource, "name"):
            name = self.__currentSource.name
        else:
            name = None
        mst = None
        for stnm, st in self.__sourcewidgets.items():
            if name == stnm:
                mst = st
                for wg in st.widgets:
                    wg.show()
            else:
                for wg in st.widgets:
                    wg.hide()
        if mst:
            mst.updateButton()

    def updateSourceComboBox(self, sourcenames, name=None):
        """ set source by changing combobox

        :param sourcenames: source names
        :type sourcenames: :obj:`list` < :obj:`str` >
        :param index: combobox index
        :type index: :obj:`int`
        """

        self._ui.sourceTypeComboBox.currentIndexChanged.disconnect(
            self.onSourceChanged)
        if sourcenames and name and name not in sourcenames:
            sourcenames = list(sourcenames)
            sourcenames.append(name)
        sourcenames = [sr for sr in sourcenames if sr in self.__sourcenames]
        if not sourcenames:
            sourcenames = self.__sourcenames
        name = name or str(self._ui.sourceTypeComboBox.currentText())
        self._ui.sourceTypeComboBox.clear()
        self._ui.sourceTypeComboBox.addItems(sourcenames)
        if self._ui.sourceTypeComboBox.count() == 0:
            self._ui.sourceTypeComboBox.addItems(self.__sourcenames)
        index = self._ui.sourceTypeComboBox.findText(name)
        if index == -1:
            index = 0
        self._ui.sourceTypeComboBox.setCurrentIndex(index)
        self.updateLayout()
        self._ui.sourceTypeComboBox.currentIndexChanged.connect(
           self.onSourceChanged)

    def setSource(self, name=None, disconnect=True):
        """ set source with the given name

        :param name: source name
        :type name: :obj:`str`
        :param disconnect: disconnect signals on update
        :type disconnect: :obj:`bool`
        """
        if disconnect and self.__currentSource is not None:
            self.__currentSource.buttonEnabled.disconnect(
                self.emitButtonEnabled)
            self.__currentSource.sourceLabelChanged.disconnect(
                self._emitSourceLabelChanged)
            self.__currentSource.sourceStateChanged.disconnect(
                self._emitSourceStateChanged)
            self.__currentSource.addIconClicked.disconnect(
                self._emitAddIconClicked)
            self.__currentSource.removeIconClicked.disconnect(
                self._emitRemoveIconClicked)
            self.__currentSource.active = False
            self.__currentSource.disconnectWidget()
        if name is not None and name in self.__sourcewidgets.keys():
            self.__currentSource = self.__sourcewidgets[name]
            self.__currentSource.active = True
            self.__currentSource.buttonEnabled.connect(
                self.emitButtonEnabled)
            self.__currentSource.sourceLabelChanged.connect(
                self._emitSourceLabelChanged)
            self.__currentSource.sourceStateChanged.connect(
                self._emitSourceStateChanged)
            self.__currentSource.addIconClicked.connect(
                self._emitAddIconClicked)
            self.__currentSource.removeIconClicked.connect(
                self._emitRemoveIconClicked)
        self.updateLayout()
        self.updateMetaData(disconnect=disconnect)
        self.emitSourceChanged()

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        return self.__currentSource.label()

    def updateMetaData(self, **kargs):
        """ update source input parameters

        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        for wg in self.__sourcewidgets.values():
            wg.updateMetaData(**kargs)

    def setSourceComboBoxByName(self, name):
        """ set source by changing combobox by name

        :param name: combobox name
        :type name: :obj:`str`
        """
        index = self._ui.sourceTypeComboBox.findText(name)
        if index != -1:
            self._ui.sourceTypeComboBox.setCurrentIndex(index)

    def emitSourceChanged(self):
        """ emits sourceChanged signal
        """
        status = self._ui.sourceTypeComboBox.currentIndex() + 1
        self.sourceChanged.emit(status)

    @QtCore.pyqtSlot(str, str)
    def _emitAddIconClicked(self, name, value):
        """ emits addIconClicked signal

        :param name: object name
        :type name: :obj:`str`
        :param value: text value
        :type value: :obj:`str`
        """
        self.addIconClicked.emit(name, value)

    @QtCore.pyqtSlot(str, str)
    def _emitRemoveIconClicked(self, name, label):
        """ emits addIconClicked signal

        :param name: object name
        :type name: :obj:`str`
        :param value: text value label to remove
        :type value: :obj:`str`
        """
        self.removeIconClicked.emit(name, label)

    @QtCore.pyqtSlot()
    def _emitSourceLabelChanged(self):
        """ emits sourceLabelChanged signal
        """
        self.sourceLabelChanged.emit()

    @QtCore.pyqtSlot(int)
    def _emitSourceStateChanged(self, status):
        """ emits sourceStateChanged signal

        :param status: source state
        :type status: :obj:`int`
        """
        if status == -1:
            self.sourceConnected.emit()
        else:
            self.sourceStateChanged.emit(status, self.__sourceid)

    @QtCore.pyqtSlot(bool)
    def updateButton(self, status):
        """ update slot for source button

        :param status: button state
        :type status: :obj:`bool`
        """
        self._ui.pushButton.setEnabled(status)

    def isConnected(self):
        """ is datasource source connected

        :returns: if datasource source connected
        :rtype: :obj:`bool`
        """
        return self.__connected

    @QtCore.pyqtSlot()
    def toggleServerConnection(self):
        """ toggles server connection
        """
        self.pushButtonClicked.emit()

    @QtCore.pyqtSlot(str)
    def emitTranslationChanged(self, trans):
        """ emit translationChanged

        :param trans: x,y translation, e.g. 50,45
        :type trans: :obj:`str`
        """
        self.translationChanged.emit(trans, self.__sourceid)

    @QtCore.pyqtSlot(bool)
    def emitButtonEnabled(self, status):
        """ emit buttonEnabled

        :param trans: enabled status of button
        :type trans: :obj:`bool`
        """
        self.buttonEnabled.emit(status, self.__sourceid)

    def setErrorStatus(self, status=""):
        """ set error status

        :param status: error status
        :type status: :obj:`str`
        """
        if status:
            self._ui.cStatusLineEdit.setStyleSheet(
                "background-color: gray;")
        elif "emitting" in str(self._ui.cStatusLineEdit.text()):
            self._ui.cStatusLineEdit.setStyleSheet(
                "color: white;"
                "background-color: blue;")
        else:
            self._ui.cStatusLineEdit.setStyleSheet(
                "color: white;"
                "background-color: green;")
        self.__errorstatus = status

    def connectSuccess(self, port=None):
        """ set connection status on and display connection status

        :param port: zmq port
        :type port: :obj: `str`
        """
        self.__connected = True
        if port is not None:
            self._ui.cStatusLineEdit.setStyleSheet(
                "color: white;"
                "background-color: blue;")
            self._ui.cStatusLineEdit.setText(
                "Connected (emitting via %s)" % port)
        else:
            self._ui.cStatusLineEdit.setStyleSheet(
                "color: white;"
                "background-color: green;")
            self._ui.cStatusLineEdit.setText("Connected")

        self._ui.sourceTypeComboBox.setEnabled(False)

        if not self.__sourceid:
            self._ui.pushButton.setText("&Stop")
        if self.__currentSource is not None:
            self.__currentSource.connectWidget()

    @QtCore.pyqtSlot()
    def onSourceChanged(self):
        """ update current source widgets
        """
        self.setSource(str(self._ui.sourceTypeComboBox.currentText()))

    def connectFailure(self):
        """ set connection status off and display connection status
        """
        self.__connected = False
        self.sourceStateChanged.emit(0, self.__sourceid)
        self._ui.cStatusLineEdit.setText("Trouble connecting")

        self._ui.sourceTypeComboBox.setEnabled(True)
        if not self.__sourceid:
            self._ui.pushButton.setText("&Start")
        if self.__currentSource is not None:
            self.__currentSource.disconnectWidget()
        # self.pushButton.setText("Retry connect")

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """

        if self.__currentSource is not None:
            self.__currentSource.configure(configuration)

    def setTranslation(self, trans):
        """ stores translation of the given source

        :param: x,y tranlation, e.g. 2345,354
        :type: :obj:`str`
        """
        self._ui.translationLineEdit.setText(trans)

    def configuration(self):
        """ provides configuration for the current image source

        :return: configuration string
        :rtype configuration: :obj:`str`
        """
        if self.__currentSource is not None:
            return self.__currentSource.configuration()

    def start(self):
        """ starts viewing if pushButton enable
        """
        if self._ui.pushButton.isEnabled():
            self.toggleServerConnection()


class SourceTabWidget(QtGui.QTabWidget):
    """ image source selection
    """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source disconnected signal
    sourceDisconnected = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source connected signal
    sourceConnected = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source state signal
    sourceStateChanged = QtCore.pyqtSignal(int, int)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source state signal
    sourceChanged = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source label name signal
    sourceLabelChanged = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) add Icon Clicked
    addIconClicked = QtCore.pyqtSignal(str, str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) remove Icon Clicked
    removeIconClicked = QtCore.pyqtSignal(str, str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) translation changed signal
    translationChanged = QtCore.pyqtSignal(str, int)

    def __init__(self, parent=None, sourcetypes=None, expertmode=False,
                 nrsources=1):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        :param sourcetypes: source type class names
        :type sourcetypes: :obj:`list` <:obj:`str`>
        :param expertmode: expert mode flag
        :type expertmode: :obj:`bool`
        :param nrsources: number of sources
        :type nrsources: :obj:`int`
        """
        QtGui.QTabWidget.__init__(self, parent)

        #: (:class:`Ui_SourceTabWidget') ui_groupbox object from qtdesigner
        self._ui = _formclass()
        self._ui.setupUi(self)

        #: (:obj:`bool`) if image source connected
        self.__connected = False

        #: (:obj:`int`) number of image sources
        self.__nrsources = 0

        #: (:obj:`list` < :obj:`str` > ) source class names
        self.__types = sourcetypes or []
        #:  (:obj:`str`) default datasource
        self.__defaultsource = "Hidra"
        #:  (:obj:`bool`) expert mode flag
        self.__expertmode = expertmode

        #: (:obj:`list` < :obj:`str` > ) source names
        self.__sourcenames = []
        # (:obj:`str`) error status
        self.__errorstatus = ""

        #: (:obj:`list` < :obj:`str` > ) source tab widgets
        self.__sourcetabs = []

        #: (:obj:`list` < :obj:`str` > ) source tab widgets
        self.__buttonstatus = [False]

        self.setNumberOfSources(nrsources)
        self.__sourcetabs[0].pushButtonClicked.connect(
            self.toggleServerConnection)

        self.__setSource(self.__defaultsource, disconnect=False)

        for st in self.__sourcetabs:
            st.init()

    def currentDataSources(self):
        """ current data source

        :returns: current datasource class name
        :rtype: :obj:`str`
        """
        return [st.currentDataSource()
                for st in self.__sourcetabs][:self.count()]

    def currentDataSourceNames(self):
        """ current data source name

        :returns: current datasource class name
        :rtype: :obj:`str`
        """
        return [st.currentDataSourceName()
                for st in self.__sourcetabs][:self.count()]

    def __addSourceWidgets(self, wg=None):
        """ add source subwidgets into grid layout

        :param wg: source form object
        :type wg: :class:`SourceForm`
        """
        wg = wg or self
        wg.removeCommonWidgets()
        sln = 0
        for st in self.__types:
            sln = wg.addWidgets(st, self.__expertmode)
            swg = getattr(swgm, st)
            self.__sourcenames.append(swg.name)

        wg.addCommonWidgets(sln)
        wg.buttonEnabled.connect(self.updateButton)
        wg.sourceChanged.connect(self.emitSourceChanged)
        wg.sourceLabelChanged.connect(self._emitSourceLabelChanged)
        wg.sourceStateChanged.connect(self._emitSourceStateChanged)
        wg.addIconClicked.connect(self._emitAddIconClicked)
        wg.removeIconClicked.connect(self._emitRemoveIconClicked)
        wg.translationChanged.connect(self._emitTranslationChanged)

        self.__sourcetabs.append(wg)
        self.__buttonstatus.append(False)

    def setNumberOfSources(self, nrsources):
        """ set a number of image sources

        :param nrsources: a number of image sources
        :type nrsources: :obj:`int`
        """
        if not self.__sourcenames:
            for st in self.__types:
                swg = getattr(swgm, st)
                self.__sourcenames.append(swg.name)
        if self.__nrsources < nrsources:
            for i in range(
                    self.count(),
                    min(len(self.__sourcetabs), nrsources)):

                self.addTab(self.__sourcetabs[i], str(i + 1))
            for i in range(len(self.__sourcetabs), nrsources):
                sf = SourceForm(self, sourceid=i)
                self.__addSourceWidgets(sf)
                sf.init()
                self.addTab(sf, str(i + 1))
            if nrsources > 1:
                self.setTabText(0, "Image Source 1")
            else:
                self.setTabText(0, "Image Source")
            self.__nrsources = nrsources
        elif self.__nrsources > nrsources:
            if nrsources == 1:
                self.setTabText(0, "Image Source")
            for i in reversed(range(nrsources, self.count())):
                self.removeTab(i)
            self.__nrsources = nrsources
        self.showItem(nrsources > 1)

    def setSourceComboBoxByName(self, sid, name):
        """ set source by changing combobox by name

        :param sid: source id
        :type sid: :obj:`int`
        :param name: combobox name
        :type name: :obj:`str`
        """
        if len(self.__sourcetabs) > sid:
            self.__sourcetabs[sid].setSourceComboBoxByName(name)

    def updateSourceComboBox(self, sourcenames, name=None):
        """ set source by changing combobox

        :param sourcenames: source names
        :type sourcenames: :obj:`list` < :obj:`str` >
        :param index: combobox index
        :type index: :obj:`int`
        """
        for st in self.__sourcetabs:
            st.updateSourceComboBox(sourcenames, name=None)

    @QtCore.pyqtSlot()
    def onSourceChanged(self):
        """ update current source widgets
        """
        self.__setSource(str(self._ui.sourceTypeComboBox.currentText()))

    def updateLayout(self):
        """ update source layout
        """
        for st in self.__sourcetabs:
            st.updateLayout()

    def __setSource(self, name=None, disconnect=True):
        """ set source with the given name

        :param name: source name
        :type name: :obj:`str`
        :param disconnect: disconnect signals on update
        :type disconnect: :obj:`bool`
        """
        for st in self.__sourcetabs:
            st.setSource(name, disconnect)

    @QtCore.pyqtSlot(int)
    @QtCore.pyqtSlot()
    def emitSourceChanged(self):
        """ emits sourceChanged signal
        """
        status = json.dumps([st.sourceStatus()
                             for st in self.__sourcetabs][:self.count()])
        self.sourceChanged.emit(status)

    @QtCore.pyqtSlot(str, str)
    def _emitAddIconClicked(self, name, value):
        """ emits addIconClicked signal

        :param name: object name
        :type name: :obj:`str`
        :param value: text value
        :type value: :obj:`str`
        """
        self.addIconClicked.emit(name, value)

    @QtCore.pyqtSlot(str, str)
    def _emitRemoveIconClicked(self, name, label):
        """ emits addIconClicked signal

        :param name: object name
        :type name: :obj:`str`
        :param value: text value label to remove
        :type value: :obj:`str`
        """
        self.removeIconClicked.emit(name, label)

    @QtCore.pyqtSlot()
    def _emitSourceLabelChanged(self):
        """ emits sourceLabelChanged signal with the given name
        """
        status = "_".join([st.label()
                           for st in self.__sourcetabs][:self.count()])
        self.sourceLabelChanged.emit(status)

    @QtCore.pyqtSlot(int, int)
    def _emitSourceStateChanged(self, status, sid):
        """ emits sourceStateChanged signal with the current source id

        :param status: source id. -1 for take the current source
        :type status: :obj:`int`
        :param sid: source id
        :type sid: :obj:`int`
        """
        if status == -1:
            status = json.dumps(
                [st.sourceStatus()
                 for st in self.__sourcetabs][:self.count()])
            self.sourceConnected.emit(status)
        else:
            self.sourceStateChanged.emit(status, sid)

    @QtCore.pyqtSlot(str, int)
    def _emitTranslationChanged(self, trans, sid):
        """ emits sourceStateChanged signal with the current source id

        :param trans: x,y translation e.g. '560,235'
        :type trans: :obj:`str`
        :param sid: source id
        :type sid: :obj:`int`
        """
        self.translationChanged.emit(trans, sid)

    @QtCore.pyqtSlot(bool, int)
    def updateButton(self, status, sid):
        """ update slot for test source

        :param status: button status
        :type status: :obj:`bool`
        :param sid: source id
        :type sid: :obj:`int`
        """
        while len(self.__buttonstatus) <= sid:
            self.__buttonstatus.append(False)
        self.__buttonstatus[sid] = status
        lstatus = self.__buttonstatus[:self.count()]
        fstatus = sum(lstatus) == len(lstatus)
        self.__sourcetabs[0].updateButton(fstatus)

    def updateMetaData(self, **kargs):
        """ update source input parameters

        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        for st in self.__sourcetabs:
            st.updateMetaData(**kargs)

    def updateSourceMetaData(self, sid, **kargs):
        """ update source input parameters

        :param sid: source id
        :type sid: :obj:`int`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if len(self.__sourcetabs) > sid:
            self.__sourcetabs[sid].updateMetaData(**kargs)

    def isConnected(self):
        """ is datasource source connected

        :returns: if datasource source connected
        :rtype: :obj:`bool`
        """
        return self.__connected

    @QtCore.pyqtSlot()
    def toggleServerConnection(self):
        """ toggles server connection
        """
        if self.__errorstatus:
            self.setErrorStatus()
        if self.__connected:
            for st in self.__sourcetabs:
                st.disconnectWidget()
            self.__connected = False
            self.sourceDisconnected.emit()
        else:
            for st in self.__sourcetabs:
                st.connectWidget()
            status = json.dumps(
                [st.sourceStatus()
                 for st in self.__sourcetabs][:self.count()])
            self.sourceConnected.emit(status)

    def setErrorStatus(self, status=""):
        """ set error status

        :param status: error status
        :type status: :obj:`str`
        """
        for st in self.__sourcetabs:
            st.setErrorStatus(status)
        self.__errorstatus = status

    def connectSuccess(self, port=None):
        """ set connection status on and display connection status

        :param port: zmq port
        :type port: :obj: `str`
        """
        self.__connected = True
        for st in self.__sourcetabs:
            st.connectSuccess(port)

    def connectFailure(self):
        """ set connection status off and display connection status
        """
        self.__connected = False
        for i, st in enumerate(self.__sourcetabs):
            self.sourceStateChanged.emit(0, i)
            st.connectFailure()

    def configure(self, sid, configuration):
        """ set configuration for the current image source

        :param sid: source id
        :type sid: :obj:`int`
        :param configuration: configuration string
        :type configuration: :obj:`str`
        """

        if len(self.__sourcetabs) > sid:
            self.__sourcetabs[sid].configure(configuration)

    def configuration(self):
        """ provides configuration for the current image source

        :return: configuration string
        :rtype configuration: :obj:`str`
        """
        return [st.configuration()
                for st in self.__sourcetabs][:self.count()]

    def setTranslation(self, trans, sid):
        """ stores translation of the given source

        :param: x,y tranlation, e.g. 2345,354
        :type: :obj:`str`
        :param sid: source id
        :type sid: :obj:`int`
        """
        if len(self.__sourcetabs) > sid:
            self.__sourcetabs[sid].setTranslation(trans)

    def showItem(self, trans):
        """ show items of the widget

        :param trans: translation item show status
        :type trans: :obj:`bool`
        """
        for st in self.__sourcetabs:
            st.showItem(trans)

    def start(self):
        """ starts viewing if pushButton enable
        """
        if self.__sourcetabs[0].pushButtonEnabled():
            self.toggleServerConnection()
