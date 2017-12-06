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
#     Andre Rothkirch <andre.rothkirch@desy.de>
#

""" set of image sources """

from PyQt4 import QtCore

try:
    import hidra
    HIDRA = True
except ImportError:
    HIDRA = False

try:
    import PyTango
    PYTANGO = True
except ImportError:
    PYTANGO = False

try:
    import PIL
    PILLOW = True
except ImportError:
    PILLOW = False

import socket
import numpy as np
import random

from io import BytesIO
import imageFileHandler


class GeneralSource(object):

    def __init__(self, timeout=None):
        self.signal_host = None
        self.portnumber = "50001"
        self.target = [socket.getfqdn(), self.portnumber, 19, [".cbf"]]
        self.query = None
        self._initiated = False
        self._timeout = timeout
        self._counter = 0

    def getTarget(self):
        return self.target[0] + ":" + self.portnumber

    @QtCore.pyqtSlot(str)
    def setSignalHost(self, _):
        self._initiated = False

    def getData(self):
        self._counter += 1
        return (np.transpose([[random.randint(0, 1000)
                               for _ in range(512)] for _ in range(256)]),
                '__random_%s__' % self._counter)

    def connect(self):
        self._initiated = True
        self._counter = 0
        return True

    def disconnect(self):
        try:
            pass
        except:
            pass


class TangoAttrSource(object):

    def __init__(self, timeout=None):
        self.signal_host = None
        self.portnumber = "50001"
        self.target = [socket.getfqdn(), self.portnumber, 19, [".cbf"]]
        self.query = None
        self._initiated = False
        self._timeout = timeout
        self.aproxy = None

    def getTarget(self):
        return self.target[0] + ":" + self.portnumber

    @QtCore.pyqtSlot(str)
    def setSignalHost(self, signalhost):
        if self.signal_host != signalhost:
            self.signal_host = signalhost
            self._initiated = False

    def getData(self):

        try:
            attr = self.aproxy.read()
            return (np.transpose(attr.value),
                    '%s  (%s)' % (self.signal_host, str(attr.time)))
        except Exception as e:
            print(str(e))
            return str(e), "__ERROR__"
            pass  # this needs a bit more care
        return None, None

    def connect(self):
        try:
            if not self._initiated:
                self.aproxy = PyTango.AttributeProxy(str(self.signal_host))
            return True
        except Exception as e:
            print(str(e))
            return False

    def disconnect(self):
        try:
            pass
        except:
            pass


class HiDRASource(object):

    def __init__(self, timeout=None):
        self.signal_host = None
        self.portnumber = "50001"
        self.target = [socket.getfqdn(), self.portnumber, 19,
                       [".cbf", ".tif", ".tiff"]]
        self.query = None
        self._initiated = False
        self._timeout = timeout

    def getTargetSignalHost(self):
        return self.target[0] + ":" + self.portnumber, self.signal_host

    def getTarget(self):
        return self.target[0] + ":" + self.portnumber

    @QtCore.pyqtSlot(str)
    def setSignalHost(self, signalhost):
        if self.signal_host != signalhost:
            self.signal_host = signalhost
            self.query = hidra.Transfer("QUERY_NEXT", self.signal_host)
            self._initiated = False

    def setTargetPort(self, portnumber):
        self.portnumber = portnumber

    def connect(self):
        try:
            if not self._initiated:
                self.query.initiate(self.target)
                self._initiated = True
                self.query.start()
            return True
        except:
            if self.query is not None:
                self.query.stop()
            return False

    def disconnect(self):
        try:
            pass  # self.query.stop()
        except:
            pass

    def getData(self):
        metadata = None
        data = None
        try:
            [metadata, data] = self.query.get(self._timeout)
        except:
            pass  # this needs a bit more care

        if metadata is not None and data is not None:
            # print("data", str(data)[:10])

            if data[:10] == "###CBF: VE":
                print("[cbf source module]::metadata", metadata["filename"])
                img = imageFileHandler.CBFLoader().load(
                    np.fromstring(data[:], dtype=np.uint8))
                return np.transpose(img), metadata["filename"]
            elif data[:2] in ["II\x2A\x00", "MM\x00\x2A"]:
                print("[tif source module]::metadata", metadata["filename"])
                if PILLOW:
                    img = np.array(PIL.Image.open(BytesIO(str(data))))
                    return np.transpose(img), metadata["filename"]
                else:
                    img = imageFileHandler.TIFLoader().load(
                        np.fromstring(data[:], dtype=np.uint8))
                    return np.transpose(img), metadata["filename"]
            else:
                print(
                    "[unknown source module]::metadata", metadata["filename"])
        else:
            return None, None
