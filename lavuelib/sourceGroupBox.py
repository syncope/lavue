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

""" sourceGroupBox """

from PyQt4 import QtCore, QtGui, uic
import os

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "SourceGroupBox.ui"))

class SourceGroupBox(QtGui.QGroupBox):

    """
    Connect and disconnect hidra service.
    """
    source_disconnect = QtCore.pyqtSignal()
    source_connect = QtCore.pyqtSignal()
    source_state = QtCore.pyqtSignal(int)
    source_servername = QtCore.pyqtSignal(str)
    source_sourcetype = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        QtGui.QGroupBox.__init__(self, parent)

        #: (:class:`Ui_SourceGroupBox') ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        self.__mutex = QtCore.QMutex()

        self.signal_host = None
        self.target = None
        self.connected = False
        self.serverdict = {}
        self.sortedserverlist = []
        self.currentSource = ""

        self.zmqtopics = []
        self.autozmqtopics = False
        self.dirtrans = '{"/ramdisk/": "/gpfs/"}'

        self._types = parent.sourcetypes
        self._defaultsource = "Hidra"

        for st in self._types:
            self.__ui.sourceTypeComboBox.addItem(st["name"])

        self.__ui.pushButton.clicked.connect(self.toggleServerConnection)

        self.setSource(self._defaultsource, disconnect=False)

        self.__ui.serverComboBox.currentIndexChanged.connect(self.emitHostname)
        self.__ui.sourceTypeComboBox.currentIndexChanged.connect(
            self.onSourceChanged)
        self.__ui.attrLineEdit.textEdited.connect(self.updateAttrButton)
        self.__ui.fileLineEdit.textEdited.connect(self.updateFileButton)
        self.__ui.dirLineEdit.textEdited.connect(self.updateFileButton)
        self.__ui.pickleLineEdit.textEdited.connect(self.updateZMQPickleButton)
        self.__ui.httpLineEdit.textEdited.connect(self.updateHTTPButton)
        self.__ui.pickleTopicComboBox.currentIndexChanged.connect(
            self.updateZMQComboBox)
        self.onSourceChanged()

    @QtCore.pyqtSlot()
    def onSourceChanged(self):
        self.setSource(self.__ui.sourceTypeComboBox.currentText())
        self.source_sourcetype.emit(self.__ui.sourceTypeComboBox.currentText())

    def updateLayout(self):
        name = self.currentSource
        allhidden = set()
        mst = None
        for st in self._types:
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

    def setSource(self, name=None, disconnect=True):
        if name is not None:
            self.currentSource = name
        self.updateLayout()
        self.update(disconnect=disconnect)

    def updateHidraButton(self):
        source = str(self.__ui.sourceTypeComboBox.currentText())
        if source != "Hidra":
            return
        if self.__ui.serverComboBox.currentText() == "Pick a server":
            self.__ui.pushButton.setEnabled(False)
        else:
            self.__ui.pushButton.setEnabled(True)

    @QtCore.pyqtSlot()
    def updateAttrButton(self):
        source = str(self.__ui.sourceTypeComboBox.currentText())
        if source != "Tango Attribute":
            return
        if not str(self.__ui.attrLineEdit.text()).strip():
            self.__ui.pushButton.setEnabled(False)
        else:
            self.__ui.pushButton.setEnabled(True)
            self.source_servername.emit(str(self.__ui.attrLineEdit.text()).strip())

    @QtCore.pyqtSlot()
    def updateFileButton(self):
        source = str(self.__ui.sourceTypeComboBox.currentText())
        if source != "Tango File":
            return
        fattr = str(self.__ui.fileLineEdit.text()).strip()
        if not str(self.__ui.fileLineEdit.text()).strip():
            self.__ui.pushButton.setEnabled(False)
        else:
            self.__ui.pushButton.setEnabled(True)
            dattr = str(self.__ui.dirLineEdit.text()).strip()
            dt = self.dirtrans
            sourcename = "%s,%s,%s" % (fattr, dattr, dt)
            self.source_servername.emit(sourcename)

    @QtCore.pyqtSlot()
    def updateHTTPButton(self):
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
            self.source_servername.emit(url)

    @QtCore.pyqtSlot()
    def updateZMQComboBox(self):
        disconnected = False
        if self.connected:
            disconnected = True
            self.source_state.emit(0)
        self.updateZMQPickleButton()
        if disconnected:
            self.source_state.emit(self.__ui.sourceTypeComboBox.currentIndex() + 1)
            self.source_connect.emit()

    @QtCore.pyqtSlot()
    def updateZMQPickleButton(self, disconnect=True):
        with QtCore.QMutexLocker(self.__mutex):
            if disconnect:
                self.__ui.pickleTopicComboBox.currentIndexChanged.disconnect(
                    self.updateZMQComboBox)
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
                    self.source_servername.emit(hosturl)
                except:
                    self.__ui.pushButton.setEnabled(False)
            if disconnect:
                self.__ui.pickleTopicComboBox.currentIndexChanged.connect(
                    self.updateZMQComboBox)

    def updateButton(self):
        source = str(self.__ui.sourceTypeComboBox.currentText())
        if source != "Test":
            return
        self.__ui.pushButton.setEnabled(True)

    @QtCore.pyqtSlot(int)
    def emitHostname(self, _):
        self.updateHidraButton()

        self.source_servername.emit(self.__ui.serverComboBox.currentText())

    def setTargetName(self, name):
        self.__ui.currenthostLabel.setText(str(name))
        self.sortServerList(name)
        self.__ui.serverComboBox.addItems(self.sortedserverlist)

    def update(self, zmqtopics=None, dirtrans=None, autozmqtopics=None,
               datasources=None, disconnect=True):
        if disconnect:
            with QtCore.QMutexLocker(self.__mutex):
                self.__ui.pickleTopicComboBox.currentIndexChanged.disconnect(
                    self.updateZMQComboBox)
        text = None
        if isinstance(zmqtopics, list):
            with QtCore.QMutexLocker(self.__mutex):
                text = str(self.__ui.pickleTopicComboBox.currentText())
            if not text or text not in zmqtopics:
                text = None
            self.zmqtopics = zmqtopics
        if autozmqtopics is not None:
            self.autozmqtopics = autozmqtopics
        if self.autozmqtopics:
            if isinstance(datasources, list):
                with QtCore.QMutexLocker(self.__mutex):
                    text = str(self.__ui.pickleTopicComboBox.currentText())
                if not text or text not in datasources:
                    text = None
                self.zmqtopics = datasources
        if dirtrans is not None:
            self.dirtrans = dirtrans
        with QtCore.QMutexLocker(self.__mutex):
            for i in reversed(range(0, self.__ui.pickleTopicComboBox.count())):
                self.__ui.pickleTopicComboBox.removeItem(i)
            self.__ui.pickleTopicComboBox.addItems(self.zmqtopics)
            self.__ui.pickleTopicComboBox.addItem("**ALL**")
            if text:
                tid = self.__ui.pickleTopicComboBox.findText(text)
                if tid > -1:
                    self.__ui.pickleTopicComboBox.setCurrentIndex(tid)
        if disconnect:
            self.updateZMQPickleButton(disconnect=False)
            with QtCore.QMutexLocker(self.__mutex):
                self.__ui.pickleTopicComboBox.currentIndexChanged.connect(
                    self.updateZMQComboBox)

    def isConnected(self):
        return self.connected

    @QtCore.pyqtSlot()
    def toggleServerConnection(self):
        # if it is connected then it's easy:
        if self.connected:
            self.source_disconnect.emit()
            self.__ui.cStatusLineEdit.setStyleSheet("color: yellow;"
                                       "background-color: red;")
            self.__ui.cStatusLineEdit.setText("Disconnected")
            # self.__ui.pushButton.setText("Re-Start")
            self.__ui.pushButton.setText("&Start")
            self.connected = False
            self.source_state.emit(0)
            self.__ui.serverComboBox.setEnabled(True)
            self.__ui.sourceTypeComboBox.setEnabled(True)
            self.__ui.pickleLineEdit.setReadOnly(False)
            if ":" in self.__ui.attrLineEdit.text():
                self.__ui.attrLineEdit.setText(u'')
                self.updateAttrButton()
            return

        else:
            self.__ui.serverComboBox.setEnabled(False)
            self.__ui.sourceTypeComboBox.setEnabled(False)
            self.source_state.emit(self.__ui.sourceTypeComboBox.currentIndex() + 1)
            self.source_connect.emit()

    def connectSuccess(self, port=None):
        """ Function doc """
        self.connected = True
        if port is not None:
            self.__ui.cStatusLineEdit.setStyleSheet("color: white;"
                                       "background-color: blue;")
            self.__ui.cStatusLineEdit.setText("Connected (emitting via %s)" % port)
        else:
            self.__ui.cStatusLineEdit.setStyleSheet("color: white;"
                                       "background-color: green;")
            self.__ui.cStatusLineEdit.setText("Connected")
        self.__ui.sourceTypeComboBox.setEnabled(False)
        self.__ui.pickleLineEdit.setReadOnly(True)
        self.__ui.pushButton.setText("&Stop")

    def connectFailure(self):
        """ Function doc """
        self.connected = False
        self.source_state.emit(0)
        self.__ui.serverComboBox.setEnabled(True)
        self.__ui.sourceTypeComboBox.setEnabled(True)
        self.__ui.pickleLineEdit.setReadOnly(False)
        self.__ui.cStatusLineEdit.setText("Trouble connecting")
        # self.pushButton.setText("Retry connect")
        self.__ui.pushButton.setText("&Start")

    def setSourceType(self):
        """ set source type"""
        self.connected = False

    def sortServerList(self, name):
        # small function to sort out the server list details
        # stupid programming, but effective: search the hostname for a
        # string and return only the elements in the list that fit
        beamlines = ['p03', 'p08', 'p09', 'p10', 'p11']

        for bl in beamlines:
            if bl in name:
                self.sortedserverlist.extend(self.serverdict[bl])
        self.sortedserverlist.extend(self.serverdict["pool"])
