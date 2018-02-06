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

from PyQt4 import QtCore, QtGui, uic
import os

from . import sourceWidget as swgm

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "SourceGroupBox.ui"))


class SourceGroupBox(QtGui.QGroupBox):
    """ image source selection
    """

    #: (:class:`PyQt4.QtCore.pyqtSignal`) source disconnected signal
    sourceDisconnectSignal = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) source connected signal
    sourceConnectSignal = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) source state signal
    sourceStateSignal = QtCore.pyqtSignal(int)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) source server name signal
    configurationSignal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, sourcetypes=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        :param sourcetypes: source types, their corresponding
                            datasource classes, slots form checks
                            and widgets to hide.

        :type sourcetypes: :obj:`list` < {"name": :obj:`str`,
                            "datasource": :obj:`str`,
                            "slot": :obj:`str`,
                            "hidden": :obj:`list` <:obj:`str`> >
                            } >
        """
        QtGui.QGroupBox.__init__(self, parent)

        #: (:class:`Ui_SourceGroupBox') ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`bool`) if image source connected
        self.__connected = False

        #: (:class:`lavuelib.sourceWidget.GeneralSourceWidget`)
        #:      current source widget
        self.__currentSource = None

        #: (:obj:`list` < :obj:`str` > ) source class names
        self.__types = sourcetypes or []
        #:  (:obj:`str`) default datasource
        self.__defaultsource = "Hidra"

        #: (:obj:`list` < :obj:`str` > ) source names
        self.__sourcenames = []
        #: (:obj:`dict` < :obj:`str`,
        #:      :class:`lavuelib.sourceWidget.GeneralSourceWidget` >)
        #:           source names
        self.__sourcewidgets = {}

        #: (:obj:`list` < :obj:`str` > ) datasource class names
        self.__datasources = []
        #: (:obj:`list` < :class:`PyQt4.QtGui.QWidget` > ) datasource names
        self.__subwidgets = []

        self.__addSourceWidgets()

        self.__ui.pushButton.clicked.connect(self.toggleServerConnection)

        self.__setSource(self.__defaultsource, disconnect=False)

        self.__ui.sourceTypeComboBox.currentIndexChanged.connect(
            self._onSourceChanged)
        self._onSourceChanged()

    def currentDataSource(self):
        """ current data source

        :returns: current datasource class name
        :rtype: :obj:`str`
        """
        return self.__currentSource.datasource

    def __addSourceWidgets(self):
        """ add source subwidgets into grid layout
        """
        self.__ui.gridLayout.removeWidget(self.__ui.cStatusLabel)
        self.__ui.gridLayout.removeWidget(self.__ui.cStatusLineEdit)
        self.__ui.gridLayout.removeWidget(self.__ui.pushButton)
        for st in self.__types:
            swg = getattr(swgm, st)()
            self.__sourcewidgets[swg.name] = swg
            self.__sourcenames.append(swg.name)
            self.__ui.sourceTypeComboBox.addItem(swg.name)
            self.__datasources.append(swg.datasource)
            widgets = zip(swg.widgets[0::2], swg.widgets[1::2])
            for wg1, wg2 in widgets:
                sln = len(self.__subwidgets)
                self.__ui.gridLayout.addWidget(wg1, sln + 1, 0)
                self.__ui.gridLayout.addWidget(wg2, sln + 1, 1)
                self.__subwidgets.append([wg1, wg2])

        sln = len(self.__subwidgets)
        self.__ui.gridLayout.addWidget(self.__ui.cStatusLabel, sln + 1, 0)
        self.__ui.gridLayout.addWidget(self.__ui.cStatusLineEdit, sln + 1, 1)
        self.__ui.gridLayout.addWidget(self.__ui.pushButton, sln + 2, 1)

    @QtCore.pyqtSlot()
    def _onSourceChanged(self):
        """ update current source widgets
        """
        self.__setSource(str(self.__ui.sourceTypeComboBox.currentText()))

    def updateLayout(self):
        """ update source layout
        """
        name = self.__currentSource.name
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

    def __setSource(self, name=None, disconnect=True):
        """ set source with the given name

        :param name: source name
        :type name: :obj:`str`
        :param disconnect: disconnect signals on update
        :type disconnect: :obj:`bool`
        """
        if disconnect and self.__currentSource is not None:
            self.__currentSource.buttonEnabledSignal.disconnect(
                self.updateButton)
            self.__currentSource.configurationSignal.disconnect(
                self._emitConfigurationSignal)
            self.__currentSource.sourceStateSignal.disconnect(
                self._emitSourceStateSignal)
            self.__currentSource.active = False
            self.__currentSource.disconnectWidget()
        if name is not None and name in self.__sourcewidgets.keys():
            self.__currentSource = self.__sourcewidgets[name]
            self.__currentSource.active = True
            self.__currentSource.buttonEnabledSignal.connect(
                self.updateButton)
            self.__currentSource.configurationSignal.connect(
                self._emitConfigurationSignal)
            self.__currentSource.sourceStateSignal.connect(
                self._emitSourceStateSignal)
        self.updateLayout()
        self.updateMetaData(disconnect=disconnect)

    @QtCore.pyqtSlot(str)
    def _emitConfigurationSignal(self,  name):
        """ emits configurationSignal signal with the given name

        :param name: configuration string
        :type name: :obj:`str`
        """
        self.configurationSignal.emit(name)

    @QtCore.pyqtSlot(int)
    def _emitSourceStateSignal(self, status):
        if status == -1:
            status = self.__ui.sourceTypeComboBox.currentIndex() + 1
            self.sourceStateSignal.emit(status)
            self.sourceConnectSignal.emit()
        else:
            self.sourceStateSignal.emit(status)

    @QtCore.pyqtSlot(bool)
    def updateButton(self, status):
        """ update slot for test source
        """
        self.__ui.pushButton.setEnabled(status)

    def setTargetName(self, name):
        """ set target name

        :param name: source name
        :type name: :obj:`str`
        """

    def updateMetaData(self, **kargs):
        """ update source input parameters

        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        for wg in self.__sourcewidgets.values():
            wg.updateMetaData(**kargs)

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
        # if it is connected then it's easy:
        if self.__connected:
            self.sourceDisconnectSignal.emit()
            self.__ui.cStatusLineEdit.setStyleSheet(
                "color: yellow;"
                "background-color: red;")
            self.__ui.cStatusLineEdit.setText("Disconnected")
            self.__ui.pushButton.setText("&Start")
            self.__connected = False
            self.sourceStateSignal.emit(0)

            self.__ui.sourceTypeComboBox.setEnabled(True)
            if self.__currentSource is not None:
                self.__currentSource.disconnectWidget()

        else:
            self.__ui.sourceTypeComboBox.setEnabled(False)
            if self.__currentSource is not None:
                self.__currentSource.connectWidget()

            self.sourceStateSignal.emit(
                self.__ui.sourceTypeComboBox.currentIndex() + 1)
            self.sourceConnectSignal.emit()

    def connectSuccess(self, port=None):
        """ set connection status on and display connection status

        :param port: zmq port
        :type port: :obj: `str`
        """
        self.__connected = True
        if port is not None:
            self.__ui.cStatusLineEdit.setStyleSheet(
                "color: white;"
                "background-color: blue;")
            self.__ui.cStatusLineEdit.setText(
                "Connected (emitting via %s)" % port)
        else:
            self.__ui.cStatusLineEdit.setStyleSheet(
                "color: white;"
                "background-color: green;")
            self.__ui.cStatusLineEdit.setText("Connected")

        self.__ui.sourceTypeComboBox.setEnabled(False)
        self.__ui.pushButton.setText("&Stop")
        if self.__currentSource is not None:
            self.__currentSource.connectWidget()

    def connectFailure(self):
        """ set connection status off and display connection status
        """
        self.__connected = False
        self.sourceStateSignal.emit(0)
        self.__ui.cStatusLineEdit.setText("Trouble connecting")

        self.__ui.sourceTypeComboBox.setEnabled(True)
        self.__ui.pushButton.setText("&Start")
        if self.__currentSource is not None:
            self.__currentSource.disconnectWidget()
        # self.pushButton.setText("Retry connect")
