# Copyright (C) 2017  Christoph Rosemann, DESY, Notkestr. 85, D-22607 Hamburg
# email contact: christoph.rosemann@desy.de
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


from PyQt4 import QtCore, QtGui


class HidraWidget(QtGui.QGroupBox):

    """
    Connect and disconnect hidra service.
    """
    hidra_disconnect = QtCore.pyqtSignal()
    hidra_connect = QtCore.pyqtSignal()
    hidra_state = QtCore.pyqtSignal(int)
    hidra_servername = QtCore.pyqtSignal(QtCore.QString)
    hidra_sourcetype = QtCore.pyqtSignal(QtCore.QString)

    def __init__(self, parent=None, serverdict=None):
        super(HidraWidget, self).__init__(parent)
        self.setTitle("Image Source")

        self.signal_host = None
        self.target = None
        self.connected = False
        self.serverdict = serverdict
        self.sortedserverlist = []

        self._types = parent.sourcetypes
        self._defaultsource = "Hidra"
        
        gridlayout = QtGui.QGridLayout()

        self.sourceTypeLabel = QtGui.QLabel(u"Source:")
        self.cStatusLabel = QtGui.QLabel("Status: ")
        self.sourceTypeComboBox = QtGui.QComboBox()
        for st in self._types:
            self.sourceTypeComboBox.addItem(st["name"])

        self.serverLabel = QtGui.QLabel(u"Server:")
        self.serverlistBox = QtGui.QComboBox()
        self.serverlistBox.addItem("Pick a server")
        self.hostlabel = QtGui.QLabel("Client:")
        self.currenthost = QtGui.QLabel(u"SomeName")

        self.attrLabel = QtGui.QLabel(u"Attribute:")
        self.attrLineEdit = QtGui.QLineEdit(u"")
        
        
        self.cStatusLabel = QtGui.QLabel("Status: ")
        self.cStatus = QtGui.QLineEdit("Not connected")
        self.cStatus.setStyleSheet("color: blue;"
                                   "background-color: yellow;")
        self.button = QtGui.QPushButton("Start")
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
        gridlayout.addWidget(self.cStatusLabel, 4, 0)
        gridlayout.addWidget(self.cStatus, 4, 1)
        gridlayout.addWidget(self.button, 5, 1)

        self.setLayout(gridlayout)

        self.serverlistBox.activated.connect(self.emitHostname)
        self.sourceTypeComboBox.currentIndexChanged.connect(self.onSourceChanged)
        self.attrLineEdit.textEdited.connect(self.updateAttrButton)
        self.onSourceChanged()

    def onSourceChanged(self):
        index = self.sourceTypeComboBox.currentIndex()
        self.setSource(self.sourceTypeComboBox.currentText())
        self.hidra_sourcetype.emit(self.sourceTypeComboBox.currentText())
        
    def setSource(self, name=None):
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

    def updateHidraButton(self):
        if self.serverlistBox.currentText() == "Pick a server":
            self.button.setEnabled(False)
        else:
            self.button.setEnabled(True)
        
    def updateAttrButton(self):
        if not str(self.attrLineEdit.text()).strip():
            self.button.setEnabled(False)
        else:
            self.button.setEnabled(True)

        if self.connected:
            pass
        else:
            self.hidra_servername.emit(str(self.attrLineEdit.text()).strip())
        
    def updateButton(self):
        self.button.setEnabled(True)
        
    def emitHostname(self, index):
        self.updateHidraButton()
        
        if self.connected:
            pass
        else:
            self.hidra_servername.emit(self.serverlistBox.itemText(index))

    def setTargetName(self, name):
        self.currenthost.setText(str(name))
        self.sortServerList(name)
        self.serverlistBox.addItems(self.sortedserverlist)

    def isConnected(self):
        return self.connected

    def toggleServerConnection(self):
        # if it is connected then it's easy:
        if self.connected:
            self.hidra_disconnect.emit()
            self.cStatus.setStyleSheet("color: yellow;"
                                   "background-color: red;")
            self.cStatus.setText("Disconnected")
            #self.button.setText("Re-Start")
            self.button.setText("Start")
            self.connected = False
            self.hidra_state.emit(0)
            self.serverlistBox.setEnabled(True)
            self.sourceTypeComboBox.setEnabled(True)
            return

        if not self.connected:
            self.serverlistBox.setEnabled(False)
            self.sourceTypeComboBox.setEnabled(False)
            self.hidra_state.emit(self.sourceTypeComboBox.currentIndex() + 1)
            self.hidra_connect.emit()

    def connectSuccess(self):
        """ Function doc """
        self.connected = True
        self.cStatus.setStyleSheet("color: white;"
                                   "background-color: green;")
        self.cStatus.setText("Connected")
        self.sourceTypeComboBox.setEnabled(False)
        self.button.setText("Stop")

    def connectFailure(self):
        """ Function doc """
        self.connected = False
        self.hidra_state.emit(0)
        self.serverlistBox.setEnabled(True)
        self.sourceTypeComboBox.setEnabled(True)
        self.cStatus.setText("Trouble connecting")
        self.button.setText("Retry connect")

    def setSourceType(self):
        """ set source type"""
        self.connected = False
        

    def sortServerList(self, name):
        # small function to sort out the server list details
        # stupid programming, but effective: search the hostname for a
        # string and return only the elements in the list that fit
        beamlines = [ 'p03', 'p08', 'p09', 'p10', 'p11']

        for bl in beamlines:
            if bl in name:
                self.sortedserverlist.extend(self.serverdict[bl])
        self.sortedserverlist.extend(self.serverdict["pool"])
