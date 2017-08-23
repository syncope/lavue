# Copyright (C) 2017  Christoph Rosemann, DESY, Notkestr. 85, D-22607 Hamburg
# email contact: christoph.rosemann@desy.de
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


class hidra_widget(QtGui.QGroupBox):

    """
    Connect and disconnect hidra service.
    """
    hidra_disconnect = QtCore.pyqtSignal()
    hidra_connect = QtCore.pyqtSignal()

    def __init__(self, parent=None, signal_host=None, target=None):
        super(hidra_widget, self).__init__(parent)
        self.setTitle("HiDRA connection")

        self.signal_host = signal_host
        self.target = target
        self.connected = False

        gridlayout = QtGui.QGridLayout()

        self.serverLabel = QtGui.QLabel(u"Server")
        self.serverName = QtGui.QLabel(u"SomeName")
        self.hostlabel = QtGui.QLabel("Client")
        self.currenthost = QtGui.QLabel("None")
        self.cStatusLabel = QtGui.QLabel("Status: ")
        self.cStatus = QtGui.QLineEdit("Not connected")
        self.cStatus.setStyleSheet("color: blue;"
                                   "background-color: yellow;")
        self.button = QtGui.QPushButton("Connect")

        self.button.clicked.connect(self.toggleServerConnection)

        gridlayout.addWidget(self.serverLabel, 0, 0)
        gridlayout.addWidget(self.serverName, 0, 1)
        gridlayout.addWidget(self.hostlabel, 1, 0)
        gridlayout.addWidget(self.currenthost, 1, 1)
        gridlayout.addWidget(self.cStatusLabel, 2, 0)
        gridlayout.addWidget(self.cStatus, 2, 1)
        gridlayout.addWidget(self.button, 3, 1)

        self.setLayout(gridlayout)

    def setNames(self, names):
        self.currenthost.setText(str(names[0]))
        self.serverName.setText(str(names[1]))

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
            return

        if not self.connected:
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
        self.cStatus.setText("Trouble connecting")
        self.button.setText("Retry connect")
