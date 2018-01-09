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


""" statistics widget """

from PyQt4 import QtGui


class StatisticsWidget(QtGui.QGroupBox):

    """
    Display some general image statistics.
    """

    def __init__(self, parent=None):
        QtGui.QGroupBox.__init__(self, parent)

        self.setTitle("Image statistics")
        layout = QtGui.QGridLayout()

        self.scaling = "sqrt"

        scalingLabel = QtGui.QLabel("Scaling:")
        self.scaleLabel = QtGui.QLabel(self.scaling)
        self.scaleLabel.setStyleSheet("color: red;")

        maxlabel = QtGui.QLabel("maximum: ")
        maxlabel.setToolTip(
            "maximum intensity values after image preparation and scaling")
        meanlabel = QtGui.QLabel("mean: ")
        meanlabel.setToolTip(
            "mean intensity values after image preparation and scaling")
        variancelabel = QtGui.QLabel("variance: ")
        variancelabel.setToolTip(
            "variance intensity values after image preparation and scaling")
        self.roilabel = QtGui.QLabel("roi   sum: ")
        self.roilabel.setToolTip("ROI name (and its tango alias)")

        self.maxVal = QtGui.QLineEdit("Not set")
        self.maxVal.setReadOnly(True)
        self.maxVal.setToolTip(
            "maximum intensity values after image preparation and scaling")
        self.meanVal = QtGui.QLineEdit("Not set")
        self.meanVal.setReadOnly(True)
        self.meanVal.setToolTip(
            "mean intensity values after image preparation and scaling")
        self.varVal = QtGui.QLineEdit("Not set")
        self.varVal.setReadOnly(True)
        self.varVal.setToolTip(
            "variance intensity values after image preparation and scaling")
        self.roiVal = QtGui.QLineEdit("Not set")
        self.roiVal.setReadOnly(True)
        self.roiVal.setToolTip(
            "sum of intensity values after image preparation and scaling "
            "for ROI")
        layout.addWidget(scalingLabel, 0, 0)
        layout.addWidget(self.scaleLabel, 0, 1)

        layout.addWidget(maxlabel, 1, 0)
        layout.addWidget(self.maxVal, 1, 1)
        layout.addWidget(meanlabel, 2, 0)
        layout.addWidget(self.meanVal, 2, 1)
        layout.addWidget(variancelabel, 3, 0)
        layout.addWidget(self.varVal, 3, 1)
        layout.addWidget(self.roilabel, 4, 0)
        layout.addWidget(self.roiVal, 4, 1)

        self.setLayout(layout)

    def update_stats(self, meanVal, maxVal, varVal, scaling,
                     roiVal=None, lrid=""):
        if self.scaling is not scaling:
            self.scaling = scaling
        self.scaleLabel.setText(self.scaling)
        self.meanVal.setText(meanVal)
        self.maxVal.setText(maxVal)
        self.varVal.setText(varVal)
        lrid = lrid or "roi  sum: "
        self.roilabel.setText("%s" % lrid)
        if roiVal is not None:
            self.roiVal.setText(roiVal)
