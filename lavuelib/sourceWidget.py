# Copyright (C) 2017  DESY, Notkestr. 85, D-22607 Hamburg
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

_testformclass, _testbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "TestSourceWidget.ui"))

_httpformclass, _httpbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "HTTPSourceWidget.ui"))

_hidraformclass, _hidrabaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "HidraSourceWidget.ui"))

_tangoattrformclass, _tangoattrbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "TangoAttrSourceWidget.ui"))

_tangofileformclass, _tangofilebaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "TangoFileSourceWidget.ui"))

_zmqformclass, _zmqbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ZMQSourceWidget.ui"))


class GeneralSourceWidget(QtGui.QWidget):

    """ general source widget """

    #: (:class:`PyQt4.QtCore.pyqtSignal`) push button enabled signal
    buttonEnabledSignal = QtCore.pyqtSignal(bool)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) source disconnected signal
    sourceDisconnect = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) source connected signal
    sourceConnect = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) source state signal
    sourceState = QtCore.pyqtSignal(int)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) source server name signal
    sourceServerName = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        QtGui.QGroupBox.__init__(self, parent)

        self.name = "Test"
        self.datasource = "GeneralSource"
        self.widgetnames = []
        self.widgets = []
        self.active = False
        self._ui = None
        self.__detached = False
        
    def updateButton(self):
        """ update slot for test source
        """
        if not self.active:
            return
        self.buttonEnabledSignal.emit(True)

    def updateMetaData(self, **kargs):
        """ update source input parameters
        """

    def _detachWidgets(self):
        """ detaches the form widgets from the gridLayout
        """
        
        for wnm in self.widgetnames:
            if hasattr(self._ui, wnm):
                wg = getattr(self._ui, wnm)
                if hasattr(self._ui, "gridLayout"):
                    self._ui.gridLayout.removeWidget(wg)
                self.widgets.append(wg)
        self.__detached = True
        


class TestSourceWidget(GeneralSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        GeneralSourceWidget.__init__(self, parent)

        self._ui = _testformclass()
        self._ui.setupUi(self)

        self.name = "Test"
        self.datasource = "GeneralSource"
        self.widgetnames = []
        self.active = False

        self._detachWidgets()


class HTTPSourceWidget(GeneralSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        GeneralSourceWidget.__init__(self, parent)

        self._ui = _httpformclass()
        self._ui.setupUi(self)

        self.name = "HTTP response"
        self.datasource = "HTTPSource"
        self.widgetnames = ["httpLabel", "httpLineEdit"]
        self.active = False

        self._detachWidgets()

class HidraSourceWidget(GeneralSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        GeneralSourceWidget.__init__(self, parent)

        self._ui = _hidraformclass()
        self._ui.setupUi(self)

        self.name = "Hidra"
        self.datasource = "HiDRASource"
        self.widgetnames = [
            "serverLabel", "serverComboBox",
            "hostLabel", "currenthostLabel"
        ]
        self.active = False

        self._detachWidgets()


class TangoAttrSourceWidget(GeneralSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        GeneralSourceWidget.__init__(self, parent)

        self._ui = _tangoattrformclass()
        self._ui.setupUi(self)

        self.name = "Tango Attribute"
        self.datasource = "TangoAttrSource"
        self.widgetnames = [
            "attrLabel", "attrLineEdit"
        ]
        self.active = False

        self._detachWidgets()


class TangoFileSourceWidget(GeneralSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        GeneralSourceWidget.__init__(self, parent)

        self._ui = _tangofileformclass()
        self._ui.setupUi(self)

        self.name = "Tango File"
        self.datasource = "TangoFileSource"
        self.widgetnames = [
            "fileLabel", "fileLineEdit",
            "dirLabel", "dirLineEdit"
        ]
        self.active = False

        self._detachWidgets()


class ZMQSourceWidget(GeneralSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        GeneralSourceWidget.__init__(self, parent)

        self._ui = _zmqformclass()
        self._ui.setupUi(self)

        self.name = "ZMQ Stream"
        self.datasource = "ZMQSource"
        self.widgetnames = [
            "pickleLabel", "pickleLineEdit",
            "pickleTopicLabel", "pickleTopicComboBox"
        ]
        self.active = False

        self._detachWidgets()
