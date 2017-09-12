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

    def __init__(self, parent=None, serverdict=None):
        super(HidraWidget, self).__init__(parent)
        self.setTitle("HiDRA connection")

        self.signal_host = None
        self.target = None
        self.connected = False
        self.serverdict = serverdict
        self.sortedserverlist = []

        gridlayout = QtGui.QGridLayout()

        self.serverLabel = QtGui.QLabel(u"Server")
        self.serverlistBox = QtGui.QComboBox()
        self.serverlistBox.addItem("Pick a server")

        self.hostlabel = QtGui.QLabel("Client")
        self.currenthost = QtGui.QLabel(u"SomeName")
        
        self.cStatusLabel = QtGui.QLabel("Status: ")
        self.cStatus = QtGui.QLineEdit("Not connected")
        self.cStatus.setStyleSheet("color: blue;"
                                   "background-color: yellow;")
        self.button = QtGui.QPushButton("Connect")
        self.button.setEnabled(False)

        self.button.clicked.connect(self.toggleServerConnection)

        gridlayout.addWidget(self.serverLabel, 0, 0)
        gridlayout.addWidget(self.serverlistBox, 0, 1)
        gridlayout.addWidget(self.hostlabel, 1, 0)
        gridlayout.addWidget(self.currenthost, 1, 1)
        gridlayout.addWidget(self.cStatusLabel, 2, 0)
        gridlayout.addWidget(self.cStatus, 2, 1)
        gridlayout.addWidget(self.button, 3, 1)

        self.setLayout(gridlayout)

        self.serverlistBox.activated.connect(self.emitHostname)
        
    def emitHostname(self, index):
        if self.serverlistBox.currentText() == "Pick a server":
            self.button.setEnabled(False)
        else:
            self.button.setEnabled(True)

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
            self.button.setText("Re-Connect")
            self.connected = False
            self.hidra_state.emit(0)
            self.serverlistBox.setEnabled(True)
            return

        if not self.connected:
            self.serverlistBox.setEnabled(False)
            self.hidra_state.emit(1)
            self.hidra_connect.emit()

    def connectSuccess(self):
        """ Function doc """
        self.connected = True
        self.cStatus.setStyleSheet("color: white;"
                                   "background-color: green;")
        self.cStatus.setText("Connected")
        self.button.setText("Disconnect")

    def connectFailure(self):
        """ Function doc """
        self.connected = False
        self.hidra_state.emit(0)
        self.serverlistBox.setEnabled(True)
        self.cStatus.setText("Trouble connecting")
        self.button.setText("Retry connect")

    def sortServerList(self, name):
        # small function to sort out the server list details
        # stupid programming, but effective: search the hostname for a
        # string and return only the elements in the list that fit
        beamlines = [ 'p03', 'p08', 'p09', 'p10', 'p11']

        for bl in beamlines:
            if bl in name:
                self.sortedserverlist + self.serverdict[bl]
        self.sortedserverlist.extend(self.serverdict["pool"])
