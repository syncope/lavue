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

""" image widget """


from PyQt4 import QtCore, QtGui, uic

import os
import re

_intensityformclass, _intensitybaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "IntensityToolWidget.ui"))

_roiformclass, _roibaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ROIToolWidget.ui"))

_cutformclass, _cutbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "LineCutToolWidget.ui"))

_angleqformclass, _angleqbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "AngleQToolWidget.ui"))


class ToolParameters(object):
    """ tool parameters
    """
    def __init__(self):
        """ constructor

        """
        #: (:obj:`bool`) lines enabled
        self.lines = False
        #: (:obj:`bool`) rois enabled
        self.rois = False
        #: (:obj:`bool`) cuts enabled
        self.cuts = False
        #: (:obj:`bool`) qscape enabled
        self.qspace = False
        #: (:obj:`bool`) axes scaling enabled
        self.scale = False
        #: (:obj:`bool`) cut plot enabled
        self.cutplot = False
        #: (:obj:`str`) infolineedit text
        self.infolineedit = None
        #: (:obj:`str`) infolabel text
        self.infolabel = None
        #: (:obj:`str`) infolabel text
        self.infotips = None


class ToolWidget(QtGui.QWidget):
    """ tool widget
    """
    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        :param parameters: tool parameters
        :type parameters: :class:`ToolParameters`
        """
        QtGui.QWidget.__init__(self, parent)
        #: (:obj:`str`) tool name
        self.name = "None"
        #: (:class:`Ui_ToolWidget')
        #:     ui_toolwidget object from qtdesigner
        self._ui = None
        #: (:class:`ToolParameters`) tool parameters
        self.parameters = ToolParameters()

        #: (:obj:`list` < [:class:`PyQt4.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = []


class IntensityToolWidget(ToolWidget):
    """ intensity tool widget
    """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        ToolWidget.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "Intensity"

        #: (:class:`Ui_IntensityToolWidget')
        #:        ui_toolwidget object from qtdesigner
        self.__ui = _intensityformclass()
        self.__ui.setupUi(self)

        #: (:obj:`bool`) lines enabled
        self.parameters.lines = True
        #: (:obj:`bool`) axes scaling enabled
        self.parameters.scale = True
        #: (:obj:`str`) infolineedit text
        self.parameters.infolineedit = ""
        #: (:obj:`str`) infolabel text
        self.parameters.infotips = \
            "coordinate info display for the mouse pointer"

        #: (:obj:`list` < [:class:`PyQt4.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.axesPushButton.clicked, "setTicks"]
        ]


class ROIToolWidget(ToolWidget):
    """ roi tool widget
    """
    #: (:class:`PyQt4.QtCore.pyqtSignal`) apply ROI pressed signal
    applyROIPressed = QtCore.pyqtSignal(str)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) fetch ROI pressed signal
    fetchROIPressed = QtCore.pyqtSignal(str)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) roi info Changed signal
    roiInfoChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        ToolWidget.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "ROI"

        #: (:class:`Ui_ROIToolWidget') ui_toolwidget object from qtdesigner
        self.__ui = _roiformclass()
        self.__ui.setupUi(self)

        self.parameters.rois = True
        self.parameters.infolineedit = ""
        self.parameters.infolabel = "[x1, y1, x2, y2], sum: "
        self.parameters.infotips = \
            "coordinate info display for the mouse pointer"
        self.__ui.labelROILineEdit.textEdited.connect(self.updateROIButton)
        self.__ui.applyROIPushButton.clicked.connect(self._onApplyROI)
        self.__ui.fetchROIPushButton.clicked.connect(self._onFetchROI)

        #: (:obj:`list` < [:class:`PyQt4.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.applyROIPressed, "onapplyrois"],
            [self.fetchROIPressed, "onfetchrois"],
            [self.roiInfoChanged, "updateDisplayedText"],
            [self.__ui.roiSpinBox.valueChanged, "roiNrChanged"],
            ["roiLineEditChanged", self.updateApplyButton],
            ["roiAliasesChanged", self.updateROILineEdit],
            ["roiValueChanged", self.updateROIDisplayText],
            ["sardanaEnabled", self.updateROIButton]
        ]

    @QtCore.pyqtSlot()
    def _onApplyROI(self):
        text = str(self.__ui.labelROILineEdit.text())
        self.applyROIPressed.emit(text)

    @QtCore.pyqtSlot()
    def _onFetchROI(self):
        text = str(self.__ui.labelROILineEdit.text())
        self.fetchROIPressed.emit(text)

    @QtCore.pyqtSlot()
    def updateApplyButton(self):
        if not str(self.__ui.labelROILineEdit.text()).strip():
            self.__ui.applyROIPushButton.setEnabled(False)
        else:
            self.__ui.applyROIPushButton.setEnabled(True)

    @QtCore.pyqtSlot(str)
    def updateROILineEdit(self, text):
        self.labelROILineEdit.setText(text)

    @QtCore.pyqtSlot(bool)
    def updateROIButton(self, enabled):
        self.__ui.applyROIPushButton.setEnabled(enabled)
        self.__ui.fetchROIPushButton.setEnabled(enabled)

    @QtCore.pyqtSlot(int)
    def updateApplyTips(self, rid):
        if rid < 0:
            self.__ui.applyROIPushButton.setToolTip(
                "remove ROI aliases from the Door environment"
                " as well as from Active MntGrp")
        else:
            self.__ui.applyROIPushButton.setToolTip(
                "add ROI aliases to the Door environment "
                "as well as to Active MntGrp")

    @QtCore.pyqtSlot(str, int, str)
    def updateROIDisplayText(self, text, currentroi, roiVal):

        roilabel = "roi [%s]" % (currentroi + 1)
        slabel = []

        rlabel = str(self.__ui.labelROILineEdit.text())
        if rlabel:
            slabel = re.split(';|,| |\n', rlabel)
            slabel = [lb for lb in slabel if lb]
        if slabel:
            roilabel = "%s [%s]" % (
                slabel[currentroi]
                if currentroi < len(slabel) else slabel[-1],
                (currentroi + 1)
            )
        self.roiInfoChanged.emit("%s, %s = %s" % (text, roilabel, roiVal))


class LineCutToolWidget(ToolWidget):
    """ line-cut tool widget
    """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        ToolWidget.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "LineCut"

        #: (:class:`Ui_LineCutToolWidget') ui_toolwidget object from qtdesigner
        self.__ui = _cutformclass()
        self.__ui.setupUi(self)

        self.parameters.cuts = True
        self.parameters.cutplot = True
        self.parameters.infolineedit = ""
        self.parameters.infotips = \
            "coordinate info display for the mouse pointer"

        #: (:obj:`list` < [:class:`PyQt4.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.cutSpinBox.valueChanged, "cutNrChanged"],
            ["cutNumberChanged", self.onCutNumberChanged]
        ]

    @QtCore.pyqtSlot(int)
    def onCutNumberChanged(self, cid):
        self.__ui.cutSpinBox.setValue(cid)


class AngleQToolWidget(ToolWidget):
    """ angle/q tool widget
    """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        ToolWidget.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "Angle/Q"

        #: (:class:`Ui_ROIToolWidget') ui_toolwidget object from qtdesigner
        self.__ui = _angleqformclass()
        self.__ui.setupUi(self)

        self.parameters.lines = True
        self.parameters.qspace = True
        self.parameters.infolineedit = ""
        self.parameters.infotips = ""

        #: (:obj:`list` < [:class:`PyQt4.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.angleqPushButton.clicked, "geometry"],
            [self.__ui.angleqComboBox.currentIndexChanged, "onAngleQChanged"],
            ["geometryTipsChanged", self.updateTips]
        ]

    @QtCore.pyqtSlot(str)
    def updateTips(self, message):
        self.__ui.angleqPushButton.setToolTip(
            "Input physical parameters\n%s" % message)
        self.__ui.angleqComboBox.setToolTip(
            "Select the display space\n%s" % message)
        self.__ui.toolLabel.setToolTip(
            "coordinate info display for the mouse pointer\n%s" % message)
