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


class BaseSourceWidget(QtGui.QWidget):

    """ general source widget """

    #: (:class:`PyQt4.QtCore.pyqtSignal`) push button enabled signal
    buttonEnabledSignal = QtCore.pyqtSignal(bool)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) source state signal
    sourceStateSignal = QtCore.pyqtSignal(int)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) source server name signal
    configurationSignal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        QtGui.QGroupBox.__init__(self, parent)

        #: (:obj:`str`) source name
        self.name = "Test"
        #: (:obj:`str`) datasource class name
        self.datasource = "BaseSource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = []
        #: (:obj:`list` <:class:`PyQt4.QtGui.QWidget`>) subwidget objects
        self.widgets = []
        #: (:obj:`bool`) source widget active
        self.active = False
        #: (:obj:`bool`) source widget connected
        self._connected = False
        #: (:class:`Ui_BaseSourceWidget')
        #:     ui_sourcewidget object from qtdesigner
        self._ui = None
        #: (:obj:`bool`) source widget detached
        self.__detached = False

    def updateButton(self):
        """ update slot for test source
        """
        if not self.active:
            return
        self.buttonEnabledSignal.emit(True)

    def updateMetaData(self, **kargs):
        """ update source input parameters

        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False

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


class TestSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _testformclass()
        self._ui.setupUi(self)

        self._detachWidgets()


class HTTPSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _httpformclass()
        self._ui.setupUi(self)

        #: (:obj:`str`) source name
        self.name = "HTTP response"
        #: (:obj:`str`) datasource class name
        self.datasource = "HTTPSource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = ["httpLabel", "httpLineEdit"]

        self._detachWidgets()

        self._ui.httpLineEdit.textEdited.connect(self.updateButton)

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for HTTP response source
        """
        if not self.active:
            return
        url = str(self._ui.httpLineEdit.text()).strip()
        if not url.startswith("http://") or not url.startswith("https://"):
            surl = url.split("/")
            if len(surl) == 2 and surl[0] and surl[1]:
                url = "http://%s/monitor/api/%s/images/monitor" \
                      % (surl[0], surl[1])
            else:
                url = None
        if not url:
            self.buttonEnabledSignal.emit(False)
        else:
            self.buttonEnabledSignal.emit(True)
            self.configurationSignal.emit(url)

    def updateMetaData(self, **kargs):
        """ update source input parameters

        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """


class HidraSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _hidraformclass()
        self._ui.setupUi(self)

        #: (:obj:`str`) source name
        self.name = "Hidra"
        #: (:obj:`str`) datasource class name
        self.datasource = "HiDRASource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "serverLabel", "serverComboBox",
            "hostLabel", "currenthostLabel"
        ]
        #: (:obj:`dict` < :obj:`str`, :obj:`list` <:obj:`str`> >)
        #:  server dictionary
        self.__serverdict = {}

        #: (:obj:`list` <:obj:`str`> >) sorted server list
        self.__sortedserverlist = []

        self._detachWidgets()

        self._ui.serverComboBox.currentIndexChanged.connect(
            self.updateButton)

    def updateButton(self):
        """ update slot for Hidra source
        """
        if not self.active:
            return
        if self._ui.serverComboBox.currentText() == "Pick a server":
            self.buttonEnabledSignal.emit(False)
        else:
            self.configurationSignal.emit(
                str(self._ui.serverComboBox.currentText()))
            self.buttonEnabledSignal.emit(True)

    def updateMetaData(self, serverdict=None, targetname=None, **kargs):
        """ update source input parameters

        :param serverdict: server dictionary
        :type serverdict: :obj:`dict` < :obj:`str`, :obj:`list` <:obj:`str`> >
        :param targetname: source targetname
        :type targetname: :obj:`str`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if isinstance(serverdict, dict):
            self.__serverdict = serverdict
        if targetname is not None:
            self._ui.currenthostLabel.setText(str(targetname))
            self.__sortServerList(targetname)
            for i in reversed(range(0, self._ui.serverComboBox.count())):
                self._ui.serverComboBox.removeItem(i)
            self._ui.serverComboBox.addItems(self.__sortedserverlist)

    def __sortServerList(self, name):
        """ small function to sort out the server list details.
        It searches the hostname for a
        string and return only the elements in the list that fit

        :param name: beamline name
        :type name: :obj:`str`
        """
        #
        beamlines = ['p03', 'p08', 'p09', 'p10', 'p11']

        self.__sortedserverlist = []
        for bl in beamlines:
            if bl in name:
                self.__sortedserverlist.extend(self.__serverdict[bl])
        self.__sortedserverlist.extend(self.__serverdict["pool"])

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.serverComboBox.setEnabled(False)

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.serverComboBox.setEnabled(True)


class TangoAttrSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _tangoattrformclass()
        self._ui.setupUi(self)

        #: (:obj:`str`) source name
        self.name = "Tango Attribute"
        #: (:obj:`str`) datasource class name
        self.datasource = "TangoAttrSource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "attrLabel", "attrLineEdit"
        ]

        self._detachWidgets()

        self._ui.attrLineEdit.textEdited.connect(self.updateButton)

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for Tango attribute source
        """
        if not self.active:
            return
        if not str(self._ui.attrLineEdit.text()).strip():
            self.buttonEnabledSignal.emit(False)
        else:
            self.buttonEnabledSignal.emit(True)
            self.configurationSignal.emit(
                str(self._ui.attrLineEdit.text()).strip())

    def updateMetaData(self, **kargs):
        """ update source input parameters
        """

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        if ":" in self._ui.attrLineEdit.text():
            self._ui.attrLineEdit.setText(u'')
            self.updateButton()


class TangoFileSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _tangofileformclass()
        self._ui.setupUi(self)

        #: (:obj:`str`) source name
        self.name = "Tango File"
        #: (:obj:`str`) datasource class name
        self.datasource = "TangoFileSource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "fileLabel", "fileLineEdit",
            "dirLabel", "dirLineEdit"
        ]

        #: (:obj:`str`) json dictionary with directory
        #:               and file name translation
        self.__dirtrans = '{"/ramdisk/": "/gpfs/"}'

        self._detachWidgets()

        self._ui.fileLineEdit.textEdited.connect(self.updateButton)
        self._ui.dirLineEdit.textEdited.connect(self.updateButton)

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for Tango file source
        """
        if not self.active:
            return
        fattr = str(self._ui.fileLineEdit.text()).strip()
        if not str(self._ui.fileLineEdit.text()).strip():
            self.buttonEnabledSignal.emit(False)
        else:
            self.buttonEnabledSignal.emit(True)
            dattr = str(self._ui.dirLineEdit.text()).strip()
            dt = self.__dirtrans
            sourcename = "%s,%s,%s" % (fattr, dattr, dt)
            self.configurationSignal.emit(sourcename)

    def updateMetaData(self, dirtrans=None, **kargs):
        """ update source input parameters

        :param dirtrans: json dictionary with directory
                         and file name translation
        :type dirtrans: :obj:`str`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if dirtrans is not None:
            self.__dirtrans = dirtrans


class ZMQSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _zmqformclass()
        self._ui.setupUi(self)

        #: (:obj:`str`) source name
        self.name = "ZMQ Stream"
        #: (:obj:`str`) datasource class name
        self.datasource = "ZMQSource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "pickleLabel", "pickleLineEdit",
            "pickleTopicLabel", "pickleTopicComboBox"
        ]

        #: (:obj:`list` <:obj:`str`> >) zmq source datasources
        self.__zmqtopics = []
        #: (:obj:`bool`) automatic zmq topics enabled
        self.__autozmqtopics = False

        #: (:class:`PyQt4.QtCore.QMutex`) zmq datasource mutex
        self.__mutex = QtCore.QMutex()

        self._detachWidgets()
        self._ui.pickleLineEdit.textEdited.connect(self.updateButton)
        self._ui.pickleTopicComboBox.currentIndexChanged.connect(
            self._updateZMQComboBox)

    @QtCore.pyqtSlot()
    def updateButton(self, disconnect=True):
        """ update slot for ZMQ source
        """
        if not self.active:
            return
        with QtCore.QMutexLocker(self.__mutex):
            if disconnect:
                self._ui.pickleTopicComboBox.currentIndexChanged.disconnect(
                    self._updateZMQComboBox)
            if not str(self._ui.pickleLineEdit.text()).strip() \
               or ":" not in str(self._ui.pickleLineEdit.text()):
                self.buttonEnabledSignal.emit(False)
            else:
                try:
                    _, sport = str(self._ui.pickleLineEdit.text())\
                        .strip().split("/")[0].split(":")
                    port = int(sport)
                    if port > 65535 or port < 0:
                        raise Exception("Wrong port")
                    self.buttonEnabledSignal.emit(True)
                    hosturl = str(self._ui.pickleLineEdit.text()).strip()
                    if self._ui.pickleTopicComboBox.currentIndex() >= 0:
                        text = self._ui.pickleTopicComboBox.currentText()
                        if text == "**ALL**":
                            text = ""
                        shost = hosturl.split("/")
                        if len(shost) > 2:
                            shost[1] = str(text)
                        else:
                            shost.append(str(text))
                        hosturl = "/".join(shost)
                    self.configurationSignal.emit(hosturl)
                except:
                    self.buttonEnabledSignal.emit(False)
            if disconnect:
                self._ui.pickleTopicComboBox.currentIndexChanged.connect(
                    self._updateZMQComboBox)

    @QtCore.pyqtSlot()
    def _updateZMQComboBox(self):
        """ update ZMQ datasource combobox
        """
        disconnected = False
        if self._connected:
            disconnected = True
            self.sourceStateSignal.emit(0)
        self.updateButton()
        if disconnected:
            self.sourceStateSignal.emit(-1)

    def updateMetaData(
            self,
            zmqtopics=None, autozmqtopics=None,
            datasources=None, disconnect=True, **kargs):
        """ update source input parameters

        :param zmqtopics: zmq source topics
        :type zmqtopics: :obj:`list` <:obj:`str`> >
        :param autozmqtopics: automatic zmq topics enabled
        :type autozmqtopics: :obj:`bool`
        :param datasources: automatic zmq source topics
        :type datasources: :obj:`list` <:obj:`str`> >
        :param disconnect: disconnect on update
        :type disconnect: :obj:`bool`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """

        if disconnect:
            with QtCore.QMutexLocker(self.__mutex):
                self._ui.pickleTopicComboBox.currentIndexChanged.disconnect(
                    self._updateZMQComboBox)
        text = None
        updatecombo = False
        if isinstance(zmqtopics, list):
            with QtCore.QMutexLocker(self.__mutex):
                text = str(self._ui.pickleTopicComboBox.currentText())
            if not text or text not in zmqtopics:
                text = None
            self.__zmqtopics = zmqtopics
            updatecombo = True
        if autozmqtopics is not None:
            self.__autozmqtopics = autozmqtopics
        if self.__autozmqtopics:
            updatecombo = True
            with QtCore.QMutexLocker(self.__mutex):
                text = str(self._ui.pickleTopicComboBox.currentText())
            if isinstance(datasources, list):
                if not text or text not in datasources:
                    text = None
                self.__zmqtopics = datasources
        if updatecombo is True:
            with QtCore.QMutexLocker(self.__mutex):
                for i in reversed(
                        range(0, self._ui.pickleTopicComboBox.count())):
                    self._ui.pickleTopicComboBox.removeItem(i)
                self._ui.pickleTopicComboBox.addItems(self.__zmqtopics)
                self._ui.pickleTopicComboBox.addItem("**ALL**")
                if text:
                    tid = self._ui.pickleTopicComboBox.findText(text)
                    if tid > -1:
                        self._ui.pickleTopicComboBox.setCurrentIndex(tid)
        if disconnect:
            self.updateButton(disconnect=False)
            with QtCore.QMutexLocker(self.__mutex):
                self._ui.pickleTopicComboBox.currentIndexChanged.connect(
                    self._updateZMQComboBox)

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.pickleLineEdit.setReadOnly(True)

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.pickleLineEdit.setReadOnly(False)
