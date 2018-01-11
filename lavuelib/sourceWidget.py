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

""" sourceWidget """

from PyQt4 import QtCore, QtGui


class SourceWidget(QtGui.QGroupBox):

    """
    Connect and disconnect hidra service.
    """
    source_disconnect = QtCore.pyqtSignal()
    source_connect = QtCore.pyqtSignal()
    source_state = QtCore.pyqtSignal(int)
    source_servername = QtCore.pyqtSignal(str)
    source_sourcetype = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        QtGui.QGroupBox.__init__(self, parent)
        self.setTitle("Image Source")

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

        gridlayout = QtGui.QGridLayout()

        self.sourceTypeLabel = QtGui.QLabel(u"Source:")
        self.sourceTypeLabel.setToolTip(
            "image source type, e.g. Hidra, Tango, ZMQ Stream, "
            "HTTP response, Test")
        self.sourceTypeComboBox = QtGui.QComboBox()
        self.sourceTypeComboBox.setToolTip(
            "image source type, e.g. Hidra, Tango, ZMQ Stream, "
            "HTTP response, Test")
        for st in self._types:
            self.sourceTypeComboBox.addItem(st["name"])

        self.serverLabel = QtGui.QLabel(u"Server:")
        self.serverLabel.setToolTip("detector tangohost name")
        self.serverlistBox = QtGui.QComboBox()
        self.serverlistBox.addItem("Pick a server")
        self.serverlistBox.setToolTip("detector tangohost name")
        self.hostlabel = QtGui.QLabel("Client:")
        self.hostlabel.setToolTip("current host name and the hidra port")
        self.currenthost = QtGui.QLabel(u"SomeName")
        self.currenthost.setToolTip("current host name and the hidra port")

        self.attrLabel = QtGui.QLabel(u"Attribute:")
        self.attrLabel.setToolTip(
            "tango device name with its attribute, "
            "e.g. sys/tg_test/1/double_image_ro")
        self.attrLineEdit = QtGui.QLineEdit(u"")
        self.attrLineEdit.setToolTip(
            "tango device name with its attribute, "
            "e.g. sys/tg_test/1/double_image_ro")

        self.fileLabel = QtGui.QLabel(u"File Attr:")
        self.fileLabel.setToolTip(
            "tango device attribute with its filename, "
            "e.g. p00/pilatus/1/LastImageTaken")
        self.fileLineEdit = QtGui.QLineEdit(u"")
        self.fileLineEdit.setToolTip(
            "tango device attribute with its filename, "
            "e.g. p00/pilatus/1/LastImageTaken")
        self.dirLabel = QtGui.QLabel(u"Dir Attr:")
        self.dirLabel.setToolTip(
            "tango device attribute with its directory (optional), "
            "e.g. p00/pilatus/1/LastImagePath")
        self.dirLineEdit = QtGui.QLineEdit(u"")
        self.dirLineEdit.setToolTip(
            "tango device attribute with its directory (optional), "
            "e.g. p00/pilatus/1/LastImagePath")

        self.httpLabel = QtGui.QLabel(u"URL:")
        self.httpLabel.setToolTip(
            "monitor url address or hostname/api_version, "
            "e.g. http://haso228eiger/monitor/api/1.5.0/images/monitor"
            " or haso228eiger/1.5.0")
        self.httpLineEdit = QtGui.QLineEdit(u"")
        self.httpLineEdit.setToolTip(
            "monitor url address or hostname/api_version, "
            "e.g. http://haso228eiger/monitor/api/1.5.0/images/monitor"
            " or haso228eiger/1.5.0")

        self.pickleLabel = QtGui.QLabel(u"ZMQ Server:")
        self.pickleLabel.setToolTip(
            "zmq server, port and topic, hwm (optional): "
            "server:port[/topic][/hwm]"
            "\ne.g. haso228:9999/10001 or :55535")
        self.pickleLineEdit = QtGui.QLineEdit(u"")
        self.pickleLineEdit.setToolTip(
            "zmq server, port and topic, hwm (optional): "
            "server:port[/topic][/hwm]"
            "\ne.g. haso228:9999/10001 or :55535")
        self.pickleTopicLabel = QtGui.QLabel(u"DataSource:")
        self.pickleTopicLabel.setToolTip("ZMQ stream topic")
        self.pickleTopicComboBox = QtGui.QComboBox()
        self.pickleTopicComboBox.setToolTip("ZMQ stream topic")

        self.cStatusLabel = QtGui.QLabel("Status: ")
        self.cStatusLabel.setToolTip(
            "connection status"
            " and via which port the zmq security stream is being emitted")
        self.cStatus = QtGui.QLineEdit("Not connected")
        # self.cStatus.setToolTip(
        #     "connection status"
        #     " and via which port the zmq security stream is being emitted")
        self.cStatus.setReadOnly(True)
        self.cStatus.setStyleSheet("color: blue;"
                                   "background-color: yellow;")
        self.button = QtGui.QPushButton("&Start")
        self.button.setToolTip("start/stop reading images")
        self.button.setEnabled(False)

        self.button.clicked.connect(self.toggleServerConnection)

        self.setSource(self._defaultsource)
        gridlayout.addWidget(self.sourceTypeLabel, 0, 0)
        gridlayout.addWidget(self.sourceTypeComboBox, 0, 1)
        gridlayout.addWidget(self.serverLabel, 1, 0)
        gridlayout.addWidget(self.serverlistBox, 1, 1)
        gridlayout.addWidget(self.hostlabel, 2, 0)
        gridlayout.addWidget(self.currenthost, 2, 1)
        gridlayout.addWidget(self.attrLabel, 3, 0)
        gridlayout.addWidget(self.attrLineEdit, 3, 1)
        gridlayout.addWidget(self.pickleLabel, 4, 0)
        gridlayout.addWidget(self.pickleLineEdit, 4, 1)
        gridlayout.addWidget(self.pickleTopicLabel, 5, 0)
        gridlayout.addWidget(self.pickleTopicComboBox, 5, 1)
        gridlayout.addWidget(self.httpLabel, 6, 0)
        gridlayout.addWidget(self.httpLineEdit, 6, 1)
        gridlayout.addWidget(self.fileLabel, 7, 0)
        gridlayout.addWidget(self.fileLineEdit, 7, 1)
        gridlayout.addWidget(self.dirLabel, 8, 0)
        gridlayout.addWidget(self.dirLineEdit, 8, 1)
        gridlayout.addWidget(self.cStatusLabel, 9, 0)
        gridlayout.addWidget(self.cStatus, 9, 1)
        gridlayout.addWidget(self.button, 10, 1)

        self.setLayout(gridlayout)

        self.serverlistBox.currentIndexChanged.connect(self.emitHostname)
        self.sourceTypeComboBox.currentIndexChanged.connect(
            self.onSourceChanged)
        self.attrLineEdit.textEdited.connect(self.updateAttrButton)
        self.fileLineEdit.textEdited.connect(self.updateFileButton)
        self.pickleLineEdit.textEdited.connect(self.updateZMQPickleButton)
        self.httpLineEdit.textEdited.connect(self.updateHTTPButton)
        self.pickleTopicComboBox.currentIndexChanged.connect(
            self.updateZMQPickleButton)
        self.onSourceChanged()

    @QtCore.pyqtSlot()
    def onSourceChanged(self):
        self.setSource(self.sourceTypeComboBox.currentText())
        self.source_sourcetype.emit(self.sourceTypeComboBox.currentText())

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
                wg = getattr(self, hd)
                if hd in mst["hidden"]:
                    wg.hide()
                else:
                    wg.show()

            getattr(self, mst["slot"])()
        
    def setSource(self, name=None):
        if name is not None:
            self.currentSource = name
        self.updateLayout()
        self.update()

    def updateHidraButton(self):
        source = str(self.sourceTypeComboBox.currentText())
        if source != "Hidra":
            return
        if self.serverlistBox.currentText() == "Pick a server":
            self.button.setEnabled(False)
        else:
            self.button.setEnabled(True)

    @QtCore.pyqtSlot()
    def updateAttrButton(self):
        source = str(self.sourceTypeComboBox.currentText())
        if source != "Tango Attr":
            return
        if not str(self.attrLineEdit.text()).strip():
            self.button.setEnabled(False)
        else:
            self.button.setEnabled(True)
            self.source_servername.emit(str(self.attrLineEdit.text()).strip())

    @QtCore.pyqtSlot()
    def updateFileButton(self):
        source = str(self.sourceTypeComboBox.currentText())
        if source != "Tango File":
            return
        fattr = str(self.fileLineEdit.text()).strip()
        if not str(self.fileLineEdit.text()).strip():
            self.button.setEnabled(False)
        else:
            self.button.setEnabled(True)
            dattr = str(self.dirLineEdit.text()).strip()
            dt = self.dirtrans
            print("SEND %s,%s,%s" % (fattr, dattr, dt))
            sourcename = "%s,%s,%s" % (fattr, dattr, dt)
            self.source_servername.emit(sourcename)

    @QtCore.pyqtSlot()
    def updateHTTPButton(self):
        source = str(self.sourceTypeComboBox.currentText())
        if source != "HTTP responce":
            return
        url = str(self.httpLineEdit.text()).strip()
        if not url.startswith("http://") or not url.startswith("https://"):
            surl = url.split("/")
            if len(surl) == 2 and surl[0] and surl[1]:
                url = "http://%s/monitor/api/%s/images/monitor" \
                      % (surl[0], surl[1])
            else:
                url = None
        if not url:
            self.button.setEnabled(False)
        else:
            self.button.setEnabled(True)
            self.source_servername.emit(url)

    @QtCore.pyqtSlot()
    def updateZMQPickleButton(self):
        source = str(self.sourceTypeComboBox.currentText())
        if source != "ZMQ Stream":
            return
        if not str(self.pickleLineEdit.text()).strip() \
           or ":" not in str(self.pickleLineEdit.text()):
            self.button.setEnabled(False)
        else:
            try:
                _, sport = str(self.pickleLineEdit.text())\
                    .strip().split("/")[0].split(":")
                port = int(sport)
                if port > 65535 or port < 0:
                    raise Exception("Wrong port")
                self.button.setEnabled(True)
                hosturl = str(self.pickleLineEdit.text()).strip()
                if self.pickleTopicComboBox.currentIndex() >= 0:
                    text = self.pickleTopicComboBox.currentText()
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
                self.button.setEnabled(False)

    def updateButton(self):
        source = str(self.sourceTypeComboBox.currentText())
        if source != "Test":
            return
        self.button.setEnabled(True)

    @QtCore.pyqtSlot(int)
    def emitHostname(self, _):
        self.updateHidraButton()

        self.source_servername.emit(self.serverlistBox.currentText())

    def setTargetName(self, name):
        self.currenthost.setText(str(name))
        self.sortServerList(name)
        self.serverlistBox.addItems(self.sortedserverlist)

    def update(self, zmqtopics=None, dirtrans=None, autozmqtopics=None):
        text = None
        if isinstance(zmqtopics, list):
            text = str(self.pickleTopicComboBox.currentText())
            if not text or text not in zmqtopics:
                text = None
            self.zmqtopics = zmqtopics
        if autozmqtopics is not None:
            self.autozmqtopics = autozmqtopics

        if dirtrans is not None:
            self.dirtrans = dirtrans
            
        for i in reversed(range(0, self.pickleTopicComboBox.count())):
            self.pickleTopicComboBox.removeItem(i)
        self.pickleTopicComboBox.addItems(self.zmqtopics)
        self.pickleTopicComboBox.addItem("**ALL**")
        if text:
            tid = self.pickleTopicComboBox.findText(text)
            if tid > -1:
                self.pickleTopicComboBox.setCurrentIndex(tid)

    def isConnected(self):
        return self.connected

    @QtCore.pyqtSlot()
    def toggleServerConnection(self):
        # if it is connected then it's easy:
        if self.connected:
            self.source_disconnect.emit()
            self.cStatus.setStyleSheet("color: yellow;"
                                       "background-color: red;")
            self.cStatus.setText("Disconnected")
            # self.button.setText("Re-Start")
            self.button.setText("&Start")
            self.connected = False
            self.source_state.emit(0)
            self.serverlistBox.setEnabled(True)
            self.sourceTypeComboBox.setEnabled(True)
            self.pickleLineEdit.setReadOnly(False)
            if ":" in self.attrLineEdit.text():
                self.attrLineEdit.setText(u'')
                self.updateAttrButton()
            return

        else:
            self.serverlistBox.setEnabled(False)
            self.sourceTypeComboBox.setEnabled(False)
            self.source_state.emit(self.sourceTypeComboBox.currentIndex() + 1)
            self.source_connect.emit()

    def connectSuccess(self, port=None):
        """ Function doc """
        self.connected = True
        if port is not None:
            self.cStatus.setStyleSheet("color: white;"
                                       "background-color: blue;")
            self.cStatus.setText("Connected (emitting via %s)" % port)
        else:
            self.cStatus.setStyleSheet("color: white;"
                                       "background-color: green;")
            self.cStatus.setText("Connected")
        self.sourceTypeComboBox.setEnabled(False)
        self.pickleLineEdit.setReadOnly(True)
        self.button.setText("&Stop")

    def connectFailure(self):
        """ Function doc """
        self.connected = False
        self.source_state.emit(0)
        self.serverlistBox.setEnabled(True)
        self.sourceTypeComboBox.setEnabled(True)
        self.pickleLineEdit.setReadOnly(False)
        self.cStatus.setText("Trouble connecting")
        # self.button.setText("Retry connect")
        self.button.setText("&Start")

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
