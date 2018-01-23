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

""" detector ticks widget """

from PyQt4 import QtGui, QtCore


class TicksWidget(QtGui.QDialog):

    """ detector ticks widget class"""

    def __init__(self, parent=None):
        """ constructor
        """

        QtGui.QDialog.__init__(self, parent)

        #: (:obj:`float`) x-coordinates of the first pixel
        self.xposition = None
        #: (:obj:`float`) y-coordinates of the first pixel
        self.yposition = None
        #: (:obj:`float`) x-scale of pixels
        self.xscale = None
        #: (:obj:`float`) y-scale of pixels
        self.yscale = None
        #: (:obj:`str`) text of x-axis
        self.xtext = None
        #: (:obj:`str`) text of y-axis
        self.ytext = None
        #: (:obj:`str`) units of x-axis
        self.xunits = None
        #: (:obj:`str`) units of y-axis
        self.yunits = None

        self.xpositionLineEdit = None
        self.ypositionLineEdit = None
        self.xscaleLineEdit = None
        self.yscaleLineEdit = None
        self.xtextLineEdit = None
        self.ytextLineEdit = None
        self.xunitsLineEdit = None
        self.yunitsLineEdit = None

    def createGUI(self):
        """ create GUI
        """

        self.setWindowTitle("Ticks")

        gridlayout = QtGui.QGridLayout()
        vlayout = QtGui.QVBoxLayout()

        xpositionLabel = QtGui.QLabel(u"Position X:")
        xpositionLabel.setToolTip(
            "x-coordinates of the first pixel")
        self.xpositionLineEdit = QtGui.QLineEdit(
            str(self.xposition if self.xposition is not None else ""))
        self.xpositionLineEdit.setToolTip(
            "x-coordinates of the first pixel")

        ypositionLabel = QtGui.QLabel(u"Position Y:")
        ypositionLabel.setToolTip(
            "y-coordinates of the first pixel")
        self.ypositionLineEdit = QtGui.QLineEdit(
            str(self.yposition if self.yposition is not None else ""))
        self.ypositionLineEdit.setToolTip(
            "y-coordinates of the first pixel")

        xscaleLabel = QtGui.QLabel(u"Scale X:")
        xscaleLabel.setToolTip("x-scale of pixels")
        self.xscaleLineEdit = QtGui.QLineEdit(str(self.xscale or ""))
        self.xscaleLineEdit.setToolTip("x-scale of pixels")

        yscaleLabel = QtGui.QLabel(u"Scale Y:")
        yscaleLabel.setToolTip("y-scale of pixels")
        self.yscaleLineEdit = QtGui.QLineEdit(str(self.yscale or ""))
        self.yscaleLineEdit.setToolTip("y-scale of pixels")

        xtextLabel = QtGui.QLabel(u"Label X:")
        xtextLabel.setToolTip("text of x-axis")
        self.xtextLineEdit = QtGui.QLineEdit(str(self.xtext or ""))
        self.xtextLineEdit.setToolTip("text of x-axis")

        ytextLabel = QtGui.QLabel(u"Label Y:")
        ytextLabel.setToolTip("text of y-axis")
        self.ytextLineEdit = QtGui.QLineEdit(str(self.ytext or ""))
        self.ytextLineEdit.setToolTip("text of y-axis")

        xunitsLabel = QtGui.QLabel(u"Units X:")
        xunitsLabel.setToolTip("units of x-axis")
        self.xunitsLineEdit = QtGui.QLineEdit(str(self.xunits or ""))
        self.xunitsLineEdit.setToolTip("units of x-axis")

        yunitsLabel = QtGui.QLabel(u"Units Y:")
        yunitsLabel.setToolTip("units of y-axis")
        self.yunitsLineEdit = QtGui.QLineEdit(str(self.yunits or ""))
        self.yunitsLineEdit.setToolTip("units of y-axis")

        gridlayout.addWidget(xpositionLabel, 0, 0)
        gridlayout.addWidget(self.xpositionLineEdit, 0, 1)
        gridlayout.addWidget(ypositionLabel, 1, 0)
        gridlayout.addWidget(self.ypositionLineEdit, 1, 1)
        gridlayout.addWidget(xscaleLabel, 2, 0)
        gridlayout.addWidget(self.xscaleLineEdit, 2, 1)
        gridlayout.addWidget(yscaleLabel, 3, 0)
        gridlayout.addWidget(self.yscaleLineEdit, 3, 1)
        gridlayout.addWidget(xtextLabel, 4, 0)
        gridlayout.addWidget(self.xtextLineEdit, 4, 1)
        gridlayout.addWidget(ytextLabel, 5, 0)
        gridlayout.addWidget(self.ytextLineEdit, 5, 1)
        gridlayout.addWidget(xunitsLabel, 6, 0)
        gridlayout.addWidget(self.xunitsLineEdit, 6, 1)
        gridlayout.addWidget(yunitsLabel, 7, 0)
        gridlayout.addWidget(self.yunitsLineEdit, 7, 1)

        self.buttonBox = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok
            | QtGui.QDialogButtonBox.Cancel)
        vlayout.addLayout(gridlayout)
        vlayout.addWidget(self.buttonBox)
        self.setLayout(vlayout)
        self.buttonBox.button(
            QtGui.QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.buttonBox.button(
            QtGui.QDialogButtonBox.Ok).clicked.connect(self.accept)

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        try:
            self.xposition = float(self.xpositionLineEdit.text())
        except:
            self.xposition = None

        try:
            self.yposition = float(self.ypositionLineEdit.text())
        except:
            self.yposition = None

        try:
            xscale = float(self.xscaleLineEdit.text())
            if xscale <= 0:
                self.xscale = None
            else:
                self.xscale = xscale
        except:
            self.xscale = None

        try:
            yscale = float(self.yscaleLineEdit.text())
            if yscale <= 0:
                self.yscale = None
            else:
                self.yscale = yscale
        except:
            self.yscale = None

        self.xtext = str(self.xtextLineEdit.text()) or ""
        self.ytext = str(self.ytextLineEdit.text()) or ""
        self.xunits = str(self.xunitsLineEdit.text()) or ""
        self.yunits = str(self.yunitsLineEdit.text()) or ""
        QtGui.QDialog.accept(self)
