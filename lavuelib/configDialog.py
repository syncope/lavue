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
#     Jan Kotanski <jan.kotanski@desy.de>
#     Christoph Rosemann <christoph.rosemann@desy.de>
#

""" configuration widget """

from .qtuic import uic
import pyqtgraph as _pg
from pyqtgraph import QtCore, QtGui
import os
import json

from . import edDictDialog

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ConfigDialog.ui"))


class ConfigDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtGui.QDialog.__init__(self, parent)

        #: (:class:`Ui_ConfigDialog') ui_dialog object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`str`) device name of sardana door
        self.door = ""
        #: (:obj:`bool`) sardana enabled
        self.sardana = True
        #: (:obj:`bool`) add rois enabled
        self.addrois = True
        #: (:obj:`bool`) security stream enabled
        self.secstream = False
        #: (:obj:`str`) security stream port
        self.secport = "5657"
        #: (:obj:`str`) hidra data port
        self.hidraport = "50001"
        #: (:obj:`bool`) find security stream port automatically
        self.secautoport = True
        #: (:obj:`float`) refresh rate
        self.refreshrate = 0.2
        #: (:obj:`bool`) show color distribution histogram widget
        self.showhisto = True
        #: (:obj:`bool`) show color distribution additional histogram widget
        self.showaddhisto = False
        #: (:obj:`bool`) show mask widget
        self.showmask = False
        #: (:obj:`bool`) show high value mask widget
        self.showhighvaluemask = False
        #: (:obj:`bool`) show statistics widget
        self.showstats = True
        #: (:obj:`bool`) zero mask enabled
        self.zeromask = False

        #: (:obj:`bool`) show bakcground subtraction widget
        self.showsub = True
        #: (:obj:`bool`) show transformation widget
        self.showtrans = True
        #: (:obj:`bool`) show filter widget
        self.showfilters = False
        #: (:obj:`bool`) show intensity scale widget
        self.showscale = True
        #: (:obj:`bool`) show intensity levels widget
        self.showlevels = True

        #: (:obj:`int`) image source timeout in ms
        self.timeout = 3000
        #: (:obj:`bool`) aspect ratio locked
        self.aspectlocked = False
        #: (:obj:`bool`) statistics without intensity scaling
        self.statswoscaling = True
        #: (:obj:`bool`) auto down sample
        self.autodownsample = False
        #: (:obj:`bool`) keep original coordinates
        self.keepcoords = False
        #: (:obj:`bool`) lazy image slider
        self.lazyimageslider = False

        #: (:obj:`list` < :obj:`str`>) hidra detector server list
        self.detservers = []

        #: (:obj:`list` < :obj:`str`>) list of topics for ZMQ stream source
        self.zmqtopics = []
        #: (:obj:`bool`) topics for ZMQ stream source fetched from the stream
        self.autozmqtopics = False

        #: (:obj:`bool`) interrupt on error
        self.interruptonerror = True

        #: (:obj:`str`) JSON dictionary with directory and filename translation
        #  for Tango file source
        self.dirtrans = '{"/ramdisk/": "/gpfs/"}'

        #: (:obj:`str`) JSON dictionary with {label: tango attribute}
        #  for Tango Attribute source
        self.tangoattrs = '{}'
        #: (:obj:`str`) JSON dictionary with {label: tango attribute}
        #  for Tango Attribute Events source
        self.tangoevattrs = '{}'
        #: (:obj:`str`) JSON dictionary with {label: file tango attribute}
        #  for Tango Attribute source
        self.tangofileattrs = '{}'
        #: (:obj:`str`) JSON dictionary with {label: dir tango attribute}
        #  for Tango Attribute source
        self.tangodirattrs = '{}'
        #: (:obj:`str`) JSON dictionary with {label: url}
        #  for HTTP responce source
        self.httpurls = '{}'
        #: (:obj:`str`) JSON dictionary with {label: <server:port>}
        #  for ZMQ source
        self.zmqservers = '{}'

        #: (:obj:`bool`) nexus file source keeps the file open
        self.nxsopen = False
        #: (:obj:`bool`) nexus file source starts from the last image
        self.nxslast = False
        #: (:obj:`bool`) store detector geometry
        self.storegeometry = False
        #: (:obj:`bool`) fetch geometry from source
        self.geometryfromsource = False
        #: (:obj:`str`) json list with filters
        self.filters = "[]"
        #: (:obj:`str`) json list with rois colors
        self.roiscolors = "[]"
        #: (:obj:`list`<:class:`pyqtgraph.ColorButton`>)
        #    list with rois color widgets
        self.__roiswidgets = []
        #: (:obj:`bool`) show all rois flag
        self.showallrois = False
        #: (:obj:`bool`) send rois to LavueController flag
        self.sendrois = False
        #: (:obj:`bool`) store display parameters for specific sources
        self.sourcedisplay = False
        #: (:obj:`dict` <:obj: `str`, :obj: `str` >) object title dictionary
        self.__objtitles = {}

    def eventFilter(self, obj, event):
        """ event filter

        :param obj: qt object
        :type obj: :class: `pyqtgraph.QtCore.QObject`
        :param event: qt event
        :type event: :class: `pyqtgraph.QtCore.QEvent`
        :returns: status flag
        :rtype: :obj:`bool`
        """
        if repr(obj) not in self.__objtitles.keys():
            return False
        if event.type() in \
           [QtCore.QEvent.MouseButtonPress, QtCore.QEvent.KeyPress]:
            if event.type() == QtCore.QEvent.KeyPress:
                if event.key() != QtCore.Qt.Key_Space:
                    return False
            record = json.loads(str(obj.text()).strip() or "{}")
            if not isinstance(record, dict):
                record = {}
            dform = edDictDialog.EdDictDialog(self)
            dform.record = record
            dform.title = self.__objtitles[repr(obj)]
            dform.createGUI()
            dform.exec_()
            if dform.dirty:
                for key in list(record.keys()):
                    if not str(key).strip():
                        record.pop(key)
                obj.setText(json.dumps(record))
            return True
        return False

    def createGUI(self):
        """ create GUI
        """
        self.__ui.rateDoubleSpinBox.setValue(self.refreshrate)
        self.__ui.aspectlockedCheckBox.setChecked(self.aspectlocked)
        self.__ui.downsampleCheckBox.setChecked(self.autodownsample)
        self.__ui.keepCoordsCheckBox.setChecked(self.keepcoords)
        self.__ui.lazyimageCheckBox.setChecked(self.lazyimageslider)
        self.__ui.statsscaleCheckBox.setChecked(not self.statswoscaling)
        self.__ui.sardanaCheckBox.setChecked(self.sardana)
        self.__ui.doorLineEdit.setText(self.door)
        self.__ui.addroisCheckBox.setChecked(self.addrois)
        self.__ui.secstreamCheckBox.setChecked(self.secstream)
        self.__ui.zeromaskCheckBox.setChecked(self.zeromask)
        self.__ui.secautoportCheckBox.setChecked(self.secautoport)
        self.__ui.secportLineEdit.setText(self.secport)
        self.__ui.hidraportLineEdit.setText(self.hidraport)
        self.__ui.showhistoCheckBox.setChecked(self.showhisto)
        self.__ui.showaddhistoCheckBox.setChecked(self.showaddhisto)
        self.__ui.showmaskCheckBox.setChecked(self.showmask)
        self.__ui.showmaskhighCheckBox.setChecked(self.showhighvaluemask)
        self.__ui.showstatsCheckBox.setChecked(self.showstats)
        self.__ui.showsubCheckBox.setChecked(self.showsub)
        self.__ui.showtransCheckBox.setChecked(self.showtrans)
        self.__ui.showfiltersCheckBox.setChecked(self.showfilters)
        self.__ui.showscaleCheckBox.setChecked(self.showscale)
        self.__ui.showlevelsCheckBox.setChecked(self.showlevels)
        self.__ui.timeoutLineEdit.setText(str(self.timeout))
        self.__ui.zmqtopicsLineEdit.setText(" ".join(self.zmqtopics))
        self.__ui.detserversLineEdit.setText(" ".join(self.detservers))
        self.__ui.autozmqtopicsCheckBox.setChecked(self.autozmqtopics)
        self.__ui.interruptCheckBox.setChecked(self.interruptonerror)
        self.__ui.dirtransLineEdit.setText(self.dirtrans)
        self.__ui.attrLineEdit.setText(self.tangoattrs)
        self.__ui.evattrLineEdit.setText(self.tangoevattrs)
        self.__ui.fileattrLineEdit.setText(self.tangofileattrs)
        self.__ui.dirattrLineEdit.setText(self.tangodirattrs)
        self.__ui.zmqserversLineEdit.setText(self.zmqservers)
        self.__ui.urlsLineEdit.setText(self.httpurls)
        self.__ui.nxsopenCheckBox.setChecked(self.nxsopen)
        self.__ui.nxslastCheckBox.setChecked(self.nxslast)
        self.__ui.storegeometryCheckBox.setChecked(self.storegeometry)
        self.__ui.fetchgeometryCheckBox.setChecked(self.geometryfromsource)
        self.__ui.sendroisCheckBox.setChecked(self.sendrois)
        self.__ui.showallroisCheckBox.setChecked(self.showallrois)
        self.__ui.sourcedisplayCheckBox.setChecked(self.sourcedisplay)

        self.__ui.urlsLineEdit.installEventFilter(self)
        self.__objtitles[repr(self.__ui.urlsLineEdit)] = \
            "HTTP responce url string"
        self.__ui.attrLineEdit.installEventFilter(self)
        self.__objtitles[repr(self.__ui.attrLineEdit)] = \
            "Tango device/attribute name"
        self.__ui.evattrLineEdit.installEventFilter(self)
        self.__objtitles[repr(self.__ui.evattrLineEdit)] = \
            "Tango device/attribute name"
        self.__ui.fileattrLineEdit.installEventFilter(self)
        self.__objtitles[repr(self.__ui.fileattrLineEdit)] = \
            "Tango file device/attribute name"
        self.__ui.dirattrLineEdit.installEventFilter(self)
        self.__objtitles[repr(self.__ui.dirattrLineEdit)] = \
            "Tango directory device/attribute name"
        self.__ui.dirtransLineEdit.installEventFilter(self)
        self.__objtitles[repr(self.__ui.dirtransLineEdit)] = \
            "directory translation dictionary"
        self.__ui.zmqserversLineEdit.installEventFilter(self)
        self.__objtitles[repr(self.__ui.zmqserversLineEdit)] = \
            "zmq server:port name"

        self._updateSecPortLineEdit(self.secautoport)
        self.__ui.secautoportCheckBox.stateChanged.connect(
            self._updateSecPortLineEdit)
        self.__ui.plusroiPushButton.clicked.connect(
            self._addROIColorWidget)
        self.__ui.minusroiPushButton.clicked.connect(
            self._removeROIColorWidget)

        self.__setROIsColorsWidgets()
        self.__setFiltersWidget()

    def __setFiltersWidget(self):
        """ updates filter tab  widget
        """
        self.__ui.addupPushButton = self.__ui.filterButtonBox.addButton(
            "Insert Row &Above", QtGui.QDialogButtonBox.ActionRole)
        self.__ui.adddownPushButton = self.__ui.filterButtonBox.addButton(
            "Insert Row &Below", QtGui.QDialogButtonBox.ActionRole)
        # self.__ui.editPushButton = self.__ui.filterButtonBox.addButton(
        #     "&Edit", QtGui.QDialogButtonBox.ActionRole)
        self.__ui.removePushButton = self.__ui.filterButtonBox.addButton(
            "&Delete Row", QtGui.QDialogButtonBox.ActionRole)
        self.__populateTable(0)
        self.__ui.addupPushButton.clicked.connect(self.__addup)
        self.__ui.adddownPushButton.clicked.connect(self.__adddown)
        # self.__ui.editPushButton.clicked.connect(self.__edit)
        self.__ui.filterTableWidget.itemChanged.connect(
            self.__tableItemChanged)
        # self.__ui.filterTableWidget.itemDoubleClicked.connect(self.__edit)
        self.__ui.removePushButton.clicked.connect(self.__remove)

    def __updateRecord(self):
        fltlist = []
        for i in range(self.__ui.filterTableWidget.rowCount()):
            item = self.__ui.filterTableWidget.item(i, 0)
            if item is not None:
                fltname = item.data(QtCore.Qt.EditRole)
                if hasattr(fltname, "toString"):
                    fltname = fltname.toString()
            else:
                fltname = ""
            item2 = self.__ui.filterTableWidget.item(i, 1)
            if item2 is not None:
                params = item2.data(QtCore.Qt.EditRole)
                if hasattr(params, "toString"):
                    params = params.toString()
            else:
                params = ""
            fltlist.append([fltname or "", params or ""])
        filters = json.dumps(fltlist)
        if self.filters != filters:
            self.filters = filters
            return True
        return False

    @QtCore.pyqtSlot("QTableWidgetItem*")
    def __tableItemChanged(self, item):
        """ changes the current value of the variable

        :param item: current item
        :type item: :class:`QtGui.QTableWidgetItem`
        """
        self.__updateRecord()

    @QtCore.pyqtSlot()
    def __addup(self):
        """ adds a new record into the table
        """
        row = self.__ui.filterTableWidget.currentRow()
        fltlist = json.loads(self.filters)
        if row >= 0 and row <= len(fltlist):
            fltlist.insert(row, ["", ""])
        else:
            fltlist.insert(0, ["", ""])

        self.filters = json.dumps(fltlist)
        self.__populateTable()
        self.__updateRecord()

    @QtCore.pyqtSlot()
    def __adddown(self):
        """ adds a new record into the table
        """
        row = self.__ui.filterTableWidget.currentRow()
        fltlist = json.loads(self.filters)
        if row >= 0 and row <= len(fltlist):
            fltlist.insert(row + 1, ["", ""])
        else:
            fltlist.append(["", ""])

        self.filters = json.dumps(fltlist)
        self.__populateTable()
        self.__updateRecord()

    @QtCore.pyqtSlot()
    def __remove(self):
        """ removes the current record from the table
        """
        row = self.__ui.filterTableWidget.currentRow()
        fltlist = json.loads(self.filters)
        if row >= 0 and row < len(fltlist):

            flt, params = fltlist[row]
            if QtGui.QMessageBox.question(
                    self, "Removing Filter",
                    'Would you like  to remove "%s": "%s" ?' % (flt, params),
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                    QtGui.QMessageBox.Yes) == QtGui.QMessageBox.No:
                return
            fltlist.pop(row)
            self.filters = json.dumps(fltlist)
            self.__populateTable()
            self.__updateRecord()

    def __populateTable(self, selected=None):
        """ populates the group table

        :param selected: selected property
        :type selected: :obj:`str`
        """
        fltlist = json.loads(self.filters)
        self.__ui.filterTableWidget.clear()
        sitem = None
        self.__ui.filterTableWidget.setSortingEnabled(False)
        self.__ui.filterTableWidget.setRowCount(len(fltlist))
        headers = ["package.module.class or package.module.function",
                   "initialization parameters"]
        self.__ui.filterTableWidget.setColumnCount(len(headers))
        self.__ui.filterTableWidget.setHorizontalHeaderLabels(headers)
        for row, fltparams in enumerate(fltlist):
            flt, params = fltparams
            item = QtGui.QTableWidgetItem(flt or "")
            item.setData(QtCore.Qt.EditRole, (flt or ""))
            self.__ui.filterTableWidget.setItem(row, 0, item)

            item2 = QtGui.QTableWidgetItem(params or "")
            item2.setData(QtCore.Qt.EditRole, (params or ""))
            self.__ui.filterTableWidget.setItem(row, 1, item2)
        self.__ui.filterTableWidget.resizeColumnsToContents()
        self.__ui.filterTableWidget.setSelectionMode(
            QtGui.QAbstractItemView.SingleSelection)
        # self.__ui.filterTableWidget.horizontalHeader(
        # ).setStretchLastSection(True)
        if hasattr(self.__ui.filterTableWidget.horizontalHeader(),
                   "setSectionResizeMode"):
            self.__ui.filterTableWidget.horizontalHeader().\
                setSectionResizeMode(1, QtGui.QHeaderView.Stretch)
        else:
            self.__ui.filterTableWidget.horizontalHeader().\
                setResizeMode(1, QtGui.QHeaderView.Stretch)
        if sitem is not None:
            sitem.setSelected(True)
            self.__ui.filterTableWidget.setCurrentItem(sitem)

    def __setROIsColorsWidgets(self):
        """ updates ROIs colors widgets
        """
        roiscolors = json.loads(self.roiscolors)
        while len(self.__roiswidgets) > len(roiscolors):
            self._removeROIColorWidget()
        for cid, color in enumerate(roiscolors):
            if cid >= len(self.__roiswidgets):
                self._addROIColorWidget(tuple(color))

    @QtCore.pyqtSlot()
    def _addROIColorWidget(self, color=None):
        """ add ROIs colors widgets

        :param color: color to be added
        :type color: (int, int, int)
        """
        if color is None:
            color = (255, 255, 255)
        cb = _pg.ColorButton(self, color)
        self.__roiswidgets.append(cb)
        self.__ui.colorHorizontalLayout.addWidget(cb)

    @QtCore.pyqtSlot()
    def _removeROIColorWidget(self):
        """ updates ROIs colors widgets
        """
        cb = self.__roiswidgets.pop()
        cb.hide()
        self.__ui.colorHorizontalLayout.removeWidget(cb)

    def __readROIsColors(self):
        """ takes ROIs colors from rois widgets
        """
        colors = []
        for roiswg in self.__roiswidgets:
            colors.append(list(roiswg.color(mode='byte')[:3]))
        self.roiscolors = json.dumps(colors)

    @QtCore.pyqtSlot(int)
    def _updateSecPortLineEdit(self, value):
        """ updates zmq security port lineedit widget

        :param value: if False or 0 set widget enable otherwise disable
        :param value: :obj:`int` or  :obj:`bool`
        """
        if value:
            self.__ui.secportLineEdit.setEnabled(False)
        else:
            self.__ui.secportLineEdit.setEnabled(True)

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        self.sardana = self.__ui.sardanaCheckBox.isChecked()
        self.door = str(self.__ui.doorLineEdit.text()).strip()
        self.addrois = self.__ui.addroisCheckBox.isChecked()
        self.hidraport = str(self.__ui.hidraportLineEdit.text()).strip()
        self.secstream = self.__ui.secstreamCheckBox.isChecked()
        self.zeromask = self.__ui.zeromaskCheckBox.isChecked()
        self.secautoport = self.__ui.secautoportCheckBox.isChecked()
        self.refreshrate = float(self.__ui.rateDoubleSpinBox.value())
        self.showsub = self.__ui.showsubCheckBox.isChecked()
        self.showtrans = self.__ui.showtransCheckBox.isChecked()
        self.showfilters = self.__ui.showfiltersCheckBox.isChecked()
        self.showscale = self.__ui.showscaleCheckBox.isChecked()
        self.showlevels = self.__ui.showlevelsCheckBox.isChecked()
        self.showhisto = self.__ui.showhistoCheckBox.isChecked()
        self.showaddhisto = self.__ui.showaddhistoCheckBox.isChecked()
        self.showmask = self.__ui.showmaskCheckBox.isChecked()
        self.showhighvaluemask = self.__ui.showmaskhighCheckBox.isChecked()
        self.showstats = self.__ui.showstatsCheckBox.isChecked()
        self.aspectlocked = self.__ui.aspectlockedCheckBox.isChecked()
        self.autodownsample = self.__ui.downsampleCheckBox.isChecked()
        self.keepcoords = self.__ui.keepCoordsCheckBox.isChecked()
        self.lazyimageslider = self.__ui.lazyimageCheckBox.isChecked()
        self.statswoscaling = not self.__ui.statsscaleCheckBox.isChecked()
        self.nxsopen = self.__ui.nxsopenCheckBox.isChecked()
        self.nxslast = self.__ui.nxslastCheckBox.isChecked()
        self.storegeometry = self.__ui.storegeometryCheckBox.isChecked()
        self.geometryfromsource = self.__ui.fetchgeometryCheckBox.isChecked()
        self.sendrois = self.__ui.sendroisCheckBox.isChecked()
        self.showallrois = self.__ui.showallroisCheckBox.isChecked()
        self.sourcedisplay = self.__ui.sourcedisplayCheckBox.isChecked()

        try:
            dirtrans = str(self.__ui.dirtransLineEdit.text()).strip()
            mytr = json.loads(dirtrans)
            if isinstance(mytr, dict):
                self.dirtrans = dirtrans
        except Exception as e:
            print(str(e))
            self.__ui.dirtransLineEdit.setFocus(True)
            return
        try:
            attr = str(self.__ui.attrLineEdit.text()).strip()
            mytr = json.loads(attr)
            if isinstance(mytr, dict):
                self.tangoattrs = attr
        except Exception as e:
            print(str(e))
            self.__ui.attrLineEdit.setFocus(True)
            return
        try:
            attr = str(self.__ui.evattrLineEdit.text()).strip()
            mytr = json.loads(attr)
            if isinstance(mytr, dict):
                self.tangoevattrs = attr
        except Exception as e:
            print(str(e))
            self.__ui.evattrLineEdit.setFocus(True)
            return
        try:
            fileattr = str(self.__ui.fileattrLineEdit.text()).strip()
            mytr = json.loads(fileattr)
            if isinstance(mytr, dict):
                self.tangofileattrs = fileattr
        except Exception as e:
            print(str(e))
            self.__ui.fileattrLineEdit.setFocus(True)
            return
        try:
            dirattr = str(self.__ui.dirattrLineEdit.text()).strip()
            mytr = json.loads(dirattr)
            if isinstance(mytr, dict):
                self.tangodirattrs = dirattr
        except Exception as e:
            print(str(e))
            self.__ui.dirattrLineEdit.setFocus(True)
            return
        try:
            zmqservers = str(self.__ui.zmqserversLineEdit.text()).strip()
            mytr = json.loads(zmqservers)
            if isinstance(mytr, dict):
                self.zmqservers = zmqservers
        except Exception as e:
            print(str(e))
            self.__ui.zmqserversLineEdit.setFocus(True)
            return
        try:
            urls = str(self.__ui.urlsLineEdit.text()).strip()
            mytr = json.loads(urls)
            if isinstance(mytr, dict):
                self.httpurls = urls
        except Exception as e:
            print(str(e))
            self.__ui.urlsLineEdit.setFocus(True)
            return
        zmqtopics = str(self.__ui.zmqtopicsLineEdit.text()).strip().split(" ")
        self.zmqtopics = [tp for tp in zmqtopics if tp]
        detservers = str(
            self.__ui.detserversLineEdit.text()).strip().split(" ")
        self.autozmqtopics = self.__ui.autozmqtopicsCheckBox.isChecked()
        self.interruptonerror = self.__ui.interruptCheckBox.isChecked()
        self.detservers = [ds for ds in detservers if ds]
        try:
            self.timeout = int(self.__ui.timeoutLineEdit.text())
        except Exception:
            self.__ui.timeoutLineEdit.setFocus(True)
            return
        try:
            self.secport = str(self.__ui.secportLineEdit.text()).strip()
            int(self.secport)
        except Exception:
            self.__ui.secportLineEdit.setFocus(True)
            return
        try:
            self.hidraport = str(self.__ui.hidraportLineEdit.text()).strip()
            int(self.hidraport)
        except Exception:
            self.__ui.hidraportLineEdit.setFocus(True)
            return
        self.__readROIsColors()
        QtGui.QDialog.accept(self)
