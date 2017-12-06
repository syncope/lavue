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

# this a simple file handler that loads image files
# and delivers just the actual array

import numpy as np

try:
    import fabio
    FABIO = True
except:
    FABIO = False
try:
    import PIL
    PILLOW = True
except:
    PILLOW = False


class ImageFileHandler():

    '''Simple file handler class.
       Reads image from file and returns the numpy array.'''

    def __init__(self, fname):
        self._image = None
        self._data = None
        try:
            if FABIO:
                self._image = fabio.open(fname)
                self._data = self._image.data
            elif PILLOW:
                self._image = PIL.Image.open(fname)
                self._data = np.array(self._image)
        except:
            try:
                if FABIO and PILLOW:
                    self._image = PIL.Image.open(fname)
                    self._data = np.array(self._image)
            except:
                pass

    def getImage(self):
        return self._data
