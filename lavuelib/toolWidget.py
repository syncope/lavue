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


from PyQt4 import QtGui, uic

import os

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
    def __init__(self, parent=None, parameters=None):
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
        self.parameters = parameters or ToolParameters()


class IntensityToolWidget(ToolWidget):
    """ intensity tool widget
    """

    def __init__(self, parent=None, parameters=None):
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


class ROIToolWidget(ToolWidget):
    """ roi tool widget
    """

    def __init__(self, parent=None, parameters=None):
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


class LineCutToolWidget(ToolWidget):
    """ line-cut tool widget
    """

    def __init__(self, parent=None, parameters=None):
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


class AngleQToolWidget(ToolWidget):
    """ angle/q tool widget
    """

    def __init__(self, parent=None, parameters=None):
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
