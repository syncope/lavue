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

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "SourceGroupBox.ui"))


class SourceGroupBox(QtGui.QGroupBox):
    """ image source selection
    """

    #: (:class:`PyQt4.QtCore.pyqtSignal`) source disconnected signal
    sourceDisconnect = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) source connected signal
    sourceConnect = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) source state signal
    sourceState = QtCore.pyqtSignal(int)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) source server name signal
    sourceServerName = QtCore.pyqtSignal(str)

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

        #: (:class:`PyQt4.QtCore.QMutex`) zmq datasource mutex
        self.__mutex = QtCore.QMutex()

        #: (:obj:`bool`) if image source connected
        self.__connected = False

        #: (:obj:`dict` < :obj:`str`, :obj:`list` <:obj:`str`> >)
        #:  server dictionary
        self.__serverdict = {}

        #: (:obj:`list` <:obj:`str`> >) sorted server list
        self.__sortedserverlist = []
        #: (:obj:`str`) current source
        self.__currentSource = ""

        #: (:obj:`list` <:obj:`str`> >) zmq source datasources
        self.__zmqtopics = []
        #: (:obj:`bool`) automatic zmq topics enabled
        self.__autozmqtopics = False

        #: (:obj:`str`) json dictionary with directory
        #:               and file name translation
        self.__dirtrans = '{"/ramdisk/": "/gpfs/"}'

        #: (:obj:`list` < {"name": :obj:`str`,
        #:                 "datasource": :obj:`str`,
        #:                 "slot": :obj:`str`,
        #:                 "hidden": :obj:`list` <:obj:`str`> >
        #:               } > )
        #:  source types, their corresponding datasource classes,
        #:  slots form checks and widgets to hide.
        self.__types = sourcetypes or []
        #:  (:obj:`str`) default datasource
        self.__defaultsource = "Hidra"

        for st in self.__types:
            self.__ui.sourceTypeComboBox.addItem(st["name"])

        self.__ui.pushButton.clicked.connect(self.toggleServerConnection)

        self.__setSource(self.__defaultsource, disconnect=False)

        self.__ui.serverComboBox.currentIndexChanged.connect(
            self.updateHidraButton)
        self.__ui.sourceTypeComboBox.currentIndexChanged.connect(
            self._onSourceChanged)
        self.__ui.attrLineEdit.textEdited.connect(self.updateAttrButton)
        self.__ui.fileLineEdit.textEdited.connect(self.updateFileButton)
        self.__ui.dirLineEdit.textEdited.connect(self.updateFileButton)
        self.__ui.pickleLineEdit.textEdited.connect(self.updateZMQButton)
        self.__ui.httpLineEdit.textEdited.connect(self.updateHTTPButton)
        self.__ui.pickleTopicComboBox.currentIndexChanged.connect(
            self._updateZMQComboBox)
        self._onSourceChanged()

    @QtCore.pyqtSlot()
    def _onSourceChanged(self):
        """ update current source widgets
        """
        self.__setSource(self.__ui.sourceTypeComboBox.currentText())

    def updateLayout(self):
        """ update source layout
        """
        name = self.__currentSource
        allhidden = set()
        mst = None
        for st in self.__types:
            allhidden.update(st["hidden"])
            if name == st["name"]:
                mst = st
        if mst:
            for hd in allhidden:
                wg = getattr(self.__ui, hd)
                if hd in mst["hidden"]:
                    wg.hide()
                else:
                    wg.show()

            getattr(self, mst["slot"])()

    def __setSource(self, name=None, disconnect=True):
        """ set source with the given name

        :param name: source name
        :type name: :obj:`str`
        :param disconnect: disconnect signals on update
        :type disconnect: :obj:`bool`
        """
        if name is not None:
            self.__currentSource = name
        self.updateLayout()
        self.updateMetaData(disconnect=disconnect)

    def updateHidraButton(self):
        """ update slot for Hidra source
        """
        source = str(self.__ui.sourceTypeComboBox.currentText())
        if source != "Hidra":
            return
        if self.__ui.serverComboBox.currentText() == "Pick a server":
            self.__ui.pushButton.setEnabled(False)
        else:
            self.__ui.pushButton.setEnabled(True)
            self.sourceServerName.emit(
                str(self.__ui.serverComboBox.currentText()))

    @QtCore.pyqtSlot()
    def updateAttrButton(self):
        """ update slot for Tango attribute source
        """
        source = str(self.__ui.sourceTypeComboBox.currentText())
        if source != "Tango Attribute":
            return
        if not str(self.__ui.attrLineEdit.text()).strip():
            self.__ui.pushButton.setEnabled(False)
        else:
            self.__ui.pushButton.setEnabled(True)
            self.sourceServerName.emit(
                str(self.__ui.attrLineEdit.text()).strip())

    @QtCore.pyqtSlot()
    def updateFileButton(self):
        """ update slot for Tango file source
        """
        source = str(self.__ui.sourceTypeComboBox.currentText())
        if source != "Tango File":
            return
        fattr = str(self.__ui.fileLineEdit.text()).strip()
        if not str(self.__ui.fileLineEdit.text()).strip():
            self.__ui.pushButton.setEnabled(False)
        else:
            self.__ui.pushButton.setEnabled(True)
            dattr = str(self.__ui.dirLineEdit.text()).strip()
            dt = self.__dirtrans
            sourcename = "%s,%s,%s" % (fattr, dattr, dt)
            self.sourceServerName.emit(sourcename)

    @QtCore.pyqtSlot()
    def updateHTTPButton(self):
        """ update slot for HTTP response source
        """
        source = str(self.__ui.sourceTypeComboBox.currentText())
        if source != "HTTP responce":
            return
        url = str(self.__ui.httpLineEdit.text()).strip()
        if not url.startswith("http://") or not url.startswith("https://"):
            surl = url.split("/")
            if len(surl) == 2 and surl[0] and surl[1]:
                url = "http://%s/monitor/api/%s/images/monitor" \
                      % (surl[0], surl[1])
            else:
                url = None
        if not url:
            self.__ui.pushButton.setEnabled(False)
        else:
            self.__ui.pushButton.setEnabled(True)
            self.sourceServerName.emit(url)

    @QtCore.pyqtSlot()
    def _updateZMQComboBox(self):
        """ update ZMQ datasource combobox
        """
        disconnected = False
        if self.__connected:
            disconnected = True
            self.sourceState.emit(0)
        self.updateZMQButton()
        if disconnected:
            self.sourceState.emit(
                self.__ui.sourceTypeComboBox.currentIndex() + 1)
            self.sourceConnect.emit()

    @QtCore.pyqtSlot()
    def updateZMQButton(self, disconnect=True):
        """ update slot for ZMQ source
        """
        with QtCore.QMutexLocker(self.__mutex):
            if disconnect:
                self.__ui.pickleTopicComboBox.currentIndexChanged.disconnect(
                    self._updateZMQComboBox)
            source = str(self.__ui.sourceTypeComboBox.currentText())
            if source != "ZMQ Stream":
                return
            if not str(self.__ui.pickleLineEdit.text()).strip() \
               or ":" not in str(self.__ui.pickleLineEdit.text()):
                self.__ui.pushButton.setEnabled(False)
            else:
                try:
                    _, sport = str(self.__ui.pickleLineEdit.text())\
                        .strip().split("/")[0].split(":")
                    port = int(sport)
                    if port > 65535 or port < 0:
                        raise Exception("Wrong port")
                    self.__ui.pushButton.setEnabled(True)
                    hosturl = str(self.__ui.pickleLineEdit.text()).strip()
                    if self.__ui.pickleTopicComboBox.currentIndex() >= 0:
                        text = self.__ui.pickleTopicComboBox.currentText()
                        if text == "**ALL**":
                            text = ""
                        shost = hosturl.split("/")
                        if len(shost) > 2:
                            shost[1] = str(text)
                        else:
                            shost.append(str(text))
                        hosturl = "/".join(shost)
                    self.sourceServerName.emit(hosturl)
                except:
                    self.__ui.pushButton.setEnabled(False)
            if disconnect:
                self.__ui.pickleTopicComboBox.currentIndexChanged.connect(
                    self._updateZMQComboBox)

    def updateButton(self):
        """ update slot for test source
        """
        source = str(self.__ui.sourceTypeComboBox.currentText())
        if source != "Test":
            return
        self.__ui.pushButton.setEnabled(True)

    def setTargetName(self, name):
        """ set target name

        :param name: source name
        :type name: :obj:`str`
        """
        self.__ui.currenthostLabel.setText(str(name))
        self.__sortServerList(name)
        self.__ui.serverComboBox.addItems(self.__sortedserverlist)

    def updateMetaData(
            self,
            zmqtopics=None, dirtrans=None, autozmqtopics=None,
            datasources=None, disconnect=True, serverdict=None):
        """ update source input parameters

        :param zmqtopics: zmq source topics
        :type zmqtopics: :obj:`list` <:obj:`str`> >
        :param dirtrans: json dictionary with directory
                         and file name translation
        :type dirtrans: :obj:`str`
        :param autozmqtopics: automatic zmq topics enabled
        :type autozmqtopics: :obj:`bool`
        :param datasources: automatic zmq source topics
        :type datasources: :obj:`list` <:obj:`str`> >
        :param disconnect: disconnect on update
        :type disconnect: :obj:`bool`
        :param serverdict: server dictionary
        :type serverdict: :obj:`dict` < :obj:`str`, :obj:`list` <:obj:`str`> >
        """

        if disconnect:
            with QtCore.QMutexLocker(self.__mutex):
                self.__ui.pickleTopicComboBox.currentIndexChanged.disconnect(
                    self._updateZMQComboBox)
        text = None
        if isinstance(serverdict, dict):
            self.__serverdict = serverdict
        if isinstance(zmqtopics, list):
            with QtCore.QMutexLocker(self.__mutex):
                text = str(self.__ui.pickleTopicComboBox.currentText())
            if not text or text not in zmqtopics:
                text = None
            self.__zmqtopics = zmqtopics
        if autozmqtopics is not None:
            self.__autozmqtopics = autozmqtopics
        if self.__autozmqtopics:
            if isinstance(datasources, list):
                with QtCore.QMutexLocker(self.__mutex):
                    text = str(self.__ui.pickleTopicComboBox.currentText())
                if not text or text not in datasources:
                    text = None
                self.__zmqtopics = datasources
        if dirtrans is not None:
            self.__dirtrans = dirtrans
        with QtCore.QMutexLocker(self.__mutex):
            for i in reversed(range(0, self.__ui.pickleTopicComboBox.count())):
                self.__ui.pickleTopicComboBox.removeItem(i)
            self.__ui.pickleTopicComboBox.addItems(self.__zmqtopics)
            self.__ui.pickleTopicComboBox.addItem("**ALL**")
            if text:
                tid = self.__ui.pickleTopicComboBox.findText(text)
                if tid > -1:
                    self.__ui.pickleTopicComboBox.setCurrentIndex(tid)
        if disconnect:
            self.updateZMQButton(disconnect=False)
            with QtCore.QMutexLocker(self.__mutex):
                self.__ui.pickleTopicComboBox.currentIndexChanged.connect(
                    self._updateZMQComboBox)

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
            self.sourceDisconnect.emit()
            self.__ui.cStatusLineEdit.setStyleSheet(
                "color: yellow;"
                "background-color: red;")
            self.__ui.cStatusLineEdit.setText("Disconnected")
            self.__ui.pushButton.setText("&Start")
            self.__connected = False
            self.sourceState.emit(0)
            self.__ui.serverComboBox.setEnabled(True)
            self.__ui.sourceTypeComboBox.setEnabled(True)
            self.__ui.pickleLineEdit.setReadOnly(False)
            if ":" in self.__ui.attrLineEdit.text():
                self.__ui.attrLineEdit.setText(u'')
                if self.__currentSource == "Tango Attribute":
                    self.updateAttrButton()
            return

        else:
            self.__ui.serverComboBox.setEnabled(False)
            self.__ui.sourceTypeComboBox.setEnabled(False)
            self.sourceState.emit(
                self.__ui.sourceTypeComboBox.currentIndex() + 1)
            self.sourceConnect.emit()

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
        self.__ui.pickleLineEdit.setReadOnly(True)
        self.__ui.pushButton.setText("&Stop")

    def connectFailure(self):
        """ set connection status off and display connection status
        """
        self.__connected = False
        self.sourceState.emit(0)
        self.__ui.serverComboBox.setEnabled(True)
        self.__ui.sourceTypeComboBox.setEnabled(True)
        self.__ui.pickleLineEdit.setReadOnly(False)
        self.__ui.cStatusLineEdit.setText("Trouble connecting")
        # self.pushButton.setText("Retry connect")
        self.__ui.pushButton.setText("&Start")

    def __sortServerList(self, name):
        """ small function to sort out the server list details.
        It searches the hostname for a
        string and return only the elements in the list that fit

        :param name: beamline name
        :type name: :obj:`str`
        """
        #
        beamlines = ['p03', 'p08', 'p09', 'p10', 'p11']

        for bl in beamlines:
            if bl in name:
                self.__sortedserverlist.extend(self.__serverdict[bl])
        self.__sortedserverlist.extend(self.__serverdict["pool"])
