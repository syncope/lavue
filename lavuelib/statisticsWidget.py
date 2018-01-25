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

from PyQt4 import QtGui, uic
import os


class StatisticsWidget(QtGui.QGroupBox):

    """
    Display some general image statistics.
    """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        QtGui.QGroupBox.__init__(self, parent)
        self.__ui = uic.loadUi(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "ui", "StatisticsWidget.ui"), self)

        #: (:obj: `str`) scale label
        self.__scaling = "sqrt"
        self.__ui.scaleLabel.setText(self.__scaling)

    def updateStatistics(self, mean, maximum, variance, scaling,
                         roisum=None, roilabel=""):
        """ update image statistic values

        :param meanparent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        if self.__scaling is not scaling:
            self.__scaling = scaling
        self.__ui.scaleLabel.setText(self.__scaling)
        self.__ui.meanLineEdit.setText(mean)
        self.__ui.maxLineEdit.setText(maximum)
        self.__ui.varianceLineEdit.setText(variance)
        roilabel = roilabel or "roi sum:"
        self.__ui.roiLabel.setText("%s" % roilabel)
        if roisum is not None:
            self.__ui.roiLineEdit.setText(roisum)
