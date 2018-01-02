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

try:
    import zmq
    ZMQMAJOR, ZMQMINOR = map(int, zmq.zmq_version().split(".")[:2])
except:
    ZMQMAJOR, ZMQMINOR = 0, 0


import socket
import numpy as np
import random
import time
import cPickle

from io import BytesIO
import imageFileHandler


class GeneralSource(object):

    def __init__(self, timeout=None):
        self.signal_host = None
        self.portnumber = "50001"
        self.target = [socket.getfqdn()]
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
        self.target = [socket.getfqdn()]
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


class ZMQPickleSource(object):

    def __init__(self, timeout=None):
        self.signal_host = None
        self.portnumber = "50001"
        self.target = [socket.getfqdn()]
        self.query = None
        self._initiated = False
        self._timeout = timeout
        self._context = zmq.Context()
        self._socket = None
        self._counter = 0
        self._bindaddress = None
        self.__mutex = QtCore.QMutex()

    def getTarget(self):
        return self.target[0] + ":" + self.portnumber

    @QtCore.pyqtSlot(str)
    def setSignalHost(self, signalhost):
        if self.signal_host != signalhost:
            self.signal_host = signalhost
            self._initiated = False

    def getData(self):
        try:
            with QtCore.QMutexLocker(self.__mutex):
                message = self._socket.recv_multipart(flags=zmq.NOBLOCK)

            (tag,
             _array,
             _shape,
             _dtype) = message
            array = np.frombuffer(
                buffer(_array),
                dtype=cPickle.loads(_dtype)
            )
            array = array.reshape(cPickle.loads(_shape))
            self._counter += 1
            return (np.transpose(array),
                    '%s/%s (%s)' % (self._bindaddress, tag, self._counter))
        except zmq.Again as e:
            pass
        except Exception as e:
            print(str(e))
            return str(e), "__ERROR__"
        return None, None

    def connect(self):
        try:
            shost = str(self.signal_host).split("/")
            host, port = str(shost[0]).split(":")
            tag = shost[1] if len(shost) > 1 else ""
            hwm = shost[2] if len(shost) > 2 else None

            if not self._initiated:
                if self._socket:
                    self.disconnect()
                with QtCore.QMutexLocker(self.__mutex):
                    self._socket = self._context.socket(zmq.SUB)
                    if hwm is not None:
                        self._socket.set_hwm(hwm)
                    self._bindaddress = (
                        'tcp://'
                        + socket.gethostbyname(host)
                        + ':'
                        + str(port)
                    )
                    self._socket.setsockopt(zmq.SUBSCRIBE, tag)
                    self._socket.connect(self._bindaddress)
                time.sleep(0.2)
            return True
        except Exception as e:
            self.disconnect()
            print(str(e))
            return False

    def disconnect(self):
        try:
            with QtCore.QMutexLocker(self.__mutex):
                if self._socket:
                    if self._bindaddress:
                        self._socket.unbind(self._bindaddress)
                    self._socket.close(linger=0)
                    self._socket = None
        except Exception as e:
            print(str(e))
            pass
        with QtCore.QMutexLocker(self.__mutex):
            self._bindaddress = None

    def __del__(self):
        self.disconnect()
        self._context.destroy()


class HiDRASource(object):

    def __init__(self, timeout=None):
        self.signal_host = None
        self.portnumber = "50001"
        self.target = [socket.getfqdn(), self.portnumber, 19,
                       [".cbf", ".tif", ".tiff"]]
        self.query = None
        self._initiated = False
        self._timeout = timeout
        self.__mutex = QtCore.QMutex()

    def getTargetSignalHost(self):
        return self.target[0] + ":" + self.portnumber, self.signal_host

    def getTarget(self):
        return self.target[0] + ":" + self.portnumber

    @QtCore.pyqtSlot(str)
    def setSignalHost(self, signalhost):
        if self.signal_host != signalhost:
            self.signal_host = signalhost
            with QtCore.QMutexLocker(self.__mutex):
                self.query = hidra.Transfer("QUERY_NEXT", self.signal_host)
            self._initiated = False

    def setTargetPort(self, portnumber):
        self.portnumber = portnumber

    def connect(self):
        try:
            if not self._initiated:
                with QtCore.QMutexLocker(self.__mutex):
                    self.query.initiate(self.target)
                self._initiated = True
                with QtCore.QMutexLocker(self.__mutex):
                    self.query.start()
            return True
        except:
            if self.query is not None:
                with QtCore.QMutexLocker(self.__mutex):
                    self.query.stop()
            return False

    def disconnect(self):
        try:
            if self.query is not None:
                with QtCore.QMutexLocker(self.__mutex):
                    self.query.stop()
        except:
            pass

    def getData(self):
        metadata = None
        data = None
        try:
            with QtCore.QMutexLocker(self.__mutex):
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
            else:
                # elif data[:2] in ["II\x2A\x00", "MM\x00\x2A"]:
                print("[tif source module]::metadata", metadata["filename"])
                if PILLOW:
                    img = np.array(PIL.Image.open(BytesIO(str(data))))
                    return np.transpose(img), metadata["filename"]
                else:
                    img = imageFileHandler.TIFLoader().load(
                        np.fromstring(data[:], dtype=np.uint8))
                    return np.transpose(img), metadata["filename"]
            # else:
            #     print(
            #       "[unknown source module]::metadata", metadata["filename"])
        else:
            return None, None
