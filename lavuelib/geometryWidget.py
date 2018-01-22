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

""" detector geometry widget """

from PyQt4 import QtGui, QtCore


class GeometryWidget(QtGui.QDialog):

    """ detector geometry widget class"""

    def __init__(self, parent=None):
        """ constructor
        """

        QtGui.QDialog.__init__(self, parent)

        #: (:obj:`float`) x-coordinates of the center of the image
        self.centerx = 0.0
        #: (:obj:`float`) y-coordinates of the center of the image
        self.centery = 0.0
        #: (:obj:`float`) energy in eV
        self.energy = 0.0
        #: (:obj:`float`) pixel x-size in um
        self.pixelsizex = 0.0
        #: (:obj:`float`) pixel y-size in um
        self.pixelsizey = 0.0
        #: (:obj:`float`) detector distance in mm
        self.detdistance = 0.0

        self.centerxLineEdit = None
        self.centeryLineEdit = None
        self.energyLineEdit = None
        self.pixelsizexLineEdit = None
        self.pixelsizeyLineEdit = None
        self.detdistanceLineEdit = None

    def createGUI(self):
        """ create GUI
        """

        self.setWindowTitle("Geometry")

        gridlayout = QtGui.QGridLayout()
        vlayout = QtGui.QVBoxLayout()

        centerxLabel = QtGui.QLabel(u"Center X [pixels]:")
        centerxLabel.setToolTip(
            " x-coordinates of the center of the image in pixels")
        self.centerxLineEdit = QtGui.QLineEdit(str(self.centerx))
        self.centerxLineEdit.setToolTip(
            " x-coordinates of the center of the image in pixels")

        centeryLabel = QtGui.QLabel(u"Center Y [pixels]:")
        centeryLabel.setToolTip(
            " y-coordinates of the center of the image in pixels")
        self.centeryLineEdit = QtGui.QLineEdit(str(self.centery))
        self.centeryLineEdit.setToolTip(
            " y-coordinates of the center of the image in pixels")

        energyLabel = QtGui.QLabel(u"Energy [eV]:")
        energyLabel.setToolTip("light energy in eV")
        self.energyLineEdit = QtGui.QLineEdit(str(self.energy))
        self.energyLineEdit.setToolTip("light energy in eV")

        pixelsizexLabel = QtGui.QLabel(u"Pixel x-size [um]:")
        pixelsizexLabel.setToolTip("pixel x-size in microns")
        self.pixelsizexLineEdit = QtGui.QLineEdit(str(self.pixelsizex))
        self.pixelsizexLineEdit.setToolTip("pixel x-size in microns")

        pixelsizeyLabel = QtGui.QLabel(u"Pixel y-size [um]:")
        pixelsizeyLabel.setToolTip("pixel y-size in microns")
        self.pixelsizeyLineEdit = QtGui.QLineEdit(str(self.pixelsizey))
        self.pixelsizeyLineEdit.setToolTip("pixel y-size in microns")

        detdistanceLabel = QtGui.QLabel(u"Detector distance [mm]:")
        detdistanceLabel.setToolTip("Detector distance in mm")
        self.detdistanceLineEdit = QtGui.QLineEdit(str(self.detdistance))
        self.detdistanceLineEdit.setToolTip("Detector distance in mm")

        gridlayout.addWidget(centerxLabel, 0, 0)
        gridlayout.addWidget(self.centerxLineEdit, 0, 1)
        gridlayout.addWidget(centeryLabel, 1, 0)
        gridlayout.addWidget(self.centeryLineEdit, 1, 1)
        gridlayout.addWidget(energyLabel, 2, 0)
        gridlayout.addWidget(self.energyLineEdit, 2, 1)
        gridlayout.addWidget(pixelsizexLabel, 3, 0)
        gridlayout.addWidget(self.pixelsizexLineEdit, 3, 1)
        gridlayout.addWidget(pixelsizeyLabel, 4, 0)
        gridlayout.addWidget(self.pixelsizeyLineEdit, 4, 1)
        gridlayout.addWidget(detdistanceLabel, 5, 0)
        gridlayout.addWidget(self.detdistanceLineEdit, 5, 1)

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
            self.centerx = float(self.centerxLineEdit.text())
        except:
            self.centerxLineEdit.setFocus()
            return

        try:
            self.centery = float(self.centeryLineEdit.text())
        except:
            self.centeryLineEdit.setFocus()
            return

        try:
            energy = float(self.energyLineEdit.text())
            if energy <= 0:
                raise Exception("Wrong value")
            else:
                self.energy = energy
        except:
            self.energyLineEdit.setFocus()
            return

        try:
            pixelsizex = float(self.pixelsizexLineEdit.text())
            if pixelsizex <= 0:
                raise Exception("Wrong value")
            else:
                self.pixelsizex = pixelsizex
        except:
            self.pixelsizexLineEdit.setFocus()
            return

        try:
            pixelsizey = float(self.pixelsizeyLineEdit.text())
            if pixelsizey <= 0:
                raise Exception("Wrong value")
            else:
                self.pixelsizey = pixelsizey
        except:
            self.pixelsizeyLineEdit.setFocus()
            return

        try:
            detdistance = float(self.detdistanceLineEdit.text())
            if detdistance <= 0:
                raise Exception("Wrong value")
            else:
                self.detdistance = detdistance
        except:
            self.detdistanceLineEdit.setFocus()
            return

        QtGui.QDialog.accept(self)
