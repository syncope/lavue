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

""" image display widget """

import pyqtgraph as _pg
import math

_VMAJOR, _VMINOR, _VPATCH = _pg.__version__.split(".") \
    if _pg.__version__ else ("0", "9", "0")


class AxesParameters(object):
    """ axes parameters
    """

    def __init__(self):
        """ constructor
        """

        #: (:obj:`tuple` <:obj:`float`, :obj:`float`> ) image scale (x,y)
        self.scale = None
        #: (:obj:`tuple` <:obj:`float`, :obj:`float`> )
        #    position of the first pixel
        self.position = None
        #: (:obj:`str`) label of x-axis
        self.xtext = None
        #: (:obj:`str`) label of y-axis
        self.ytext = None
        #: (:obj:`str`) units of x-axis
        self.xunits = None
        #: (:obj:`str`) units of y-axis
        self.yunits = None


class GeometryParameters(object):
    """ axes parameters
    """

    def __init__(self):
        """ constructor
        """

        #: (:obj:`bool`) enabled flag
        self.enabled = False
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
        #: (:obj:`int`) geometry space index -> 0: angle, 1 q-space
        self.gspaceindex = 0

    def pixel2theta(self, xdata, ydata):
        """ converts coordinates from pixel positions to theta angles

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        :returns: x-theta, y-theta, total-theta
        :rtype: (:obj:`float`, :obj:`float`, :obj:`float`)
        """

        xcentered = xdata - self.centerx
        ycentered = ydata - self.centery
        thetax = math.atan(
            xcentered * self.pixelsizex/1000. / self.detdistance)
        thetay = math.atan(
            ycentered * self.pixelsizey/1000. / self.detdistance)
        r = math.sqrt((xcentered * self.pixelsizex / 1000.) ** 2
                      + (ycentered * self.pixelsizex / 1000.) ** 2)
        thetatotal = math.atan(r/self.detdistance)*180/math.pi
        return thetax, thetay, thetatotal

    def pixel2q(self, xdata, ydata):
        """ converts coordinates from pixel positions to q-space coordinates

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        :returns: q_x, q_y, q_total
        :rtype: (:obj:`float`, :obj:`float`, :obj:`float`)
        """
        thetax, thetay, thetatotal = self.pixel2theta(
            xdata, ydata)
        wavelength = 12400./self.energy
        qx = 4 * math.pi / wavelength * math.sin(thetax/2.)
        qz = 4 * math.pi / wavelength * math.sin(thetay/2.)
        q = 4 * math.pi / wavelength * math.sin(thetatotal/2.)
        return qx, qz, q

    def info(self):
        """ provides geometry messate

        :returns: geometry text
        :rtype: :obj:`unicode`
        """

        return u"geometry:\n" \
            u"  center = (%s, %s) pixels\n" \
            u"  pixel_size = (%s, %s) \u00B5m\n" \
            u"  detector_distance = %s mm\n" \
            u"  energy = %s eV" % (
                self.centerx,
                self.centery,
                self.pixelsizex,
                self.pixelsizey,
                self.detdistance,
                self.energy
            )


class ROIsParameters(object):
    """ rois parameters
    """

    def __init__(self):
        """ constructor
        """
        #: (:obj:`bool`) enabled flag
        self.enabled = False
        #: (:obj:`int`) current roi id
        self.current = 0
        #: (:obj:`list` < [int, int, int, int] > )
        #: x1,y1,x2,y2 rois coordinates
        self.coords = [[10, 10, 60, 60]]


class CutsParameters(object):
    """ cuts parameters
    """

    def __init__(self):
        """ constructor
        """
        #: (:obj:`bool`) enabled flag
        self.enabled = False
        #: (:obj:`int`) current cut id
        self.current = 0
        #: (:obj:`list` < [int, int, int, int] > )
        #: x1,y1,x2,y2 rois coordinates
        self.coords = [[10, 10, 60, 10]]


class IntensityParameters(object):
    """ intensity parameters
    """

    def __init__(self):
        """ constructor
        """
        #: (:obj:`bool`) do background substraction
        self.dobkgsubtraction = False
        #: (:obj:`bool`) calculate statistics without scaling
        self.statswoscaling = False
        #: (:obj:`bool`) intensity scaling
        self.scaling = "sqrt"
