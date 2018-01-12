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
import requests
import json

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
from . import imageFileHandler


class GeneralSource(object):

    def __init__(self, timeout=None):
        self.signal_host = None
        self.portnumber = "50001"
        self.target = [socket.getfqdn()]
        self._initiated = False
        self.timeout = timeout
        self._counter = 0

    def getTarget(self):
        return self.target[0] + ":" + self.portnumber

    @QtCore.pyqtSlot(str)
    def setSignalHost(self, _):
        self._initiated = False

    def getData(self):
        self._counter += 1
        return (np.transpose(
            [
                [random.randint(0, 1000) for _ in range(512)]
                for _ in range(256)
            ]),
            '__random_%s__' % self._counter, "")

    def connect(self):
        self._initiated = True
        self._counter = 0
        return True

    def disconnect(self):
        try:
            pass
        except:
            pass


class TangoFileSource(object):

    def __init__(self, timeout=None):
        self.signal_host = None
        self.portnumber = "50001"
        self.target = [socket.getfqdn()]
        self._initiated = False
        self.timeout = timeout
        self.fproxy = None
        self.dproxy = None
        self.dirtrans = {"/ramdisk/": "/gpfs/"}

    def getTarget(self):
        return self.target[0] + ":" + self.portnumber

    @QtCore.pyqtSlot(str)
    def setSignalHost(self, signalhost):
        if self.signal_host != signalhost:
            self.signal_host = signalhost
            self._initiated = False

    def getData(self):

        try:
            filename = self.fproxy.read().value
            if self.dproxy:
                dattr = self.dproxy.read().value
                filename = "%s/%s" % (dattr, filename)
                for key, val in self.dirtrans.items():
                    filename = filename.replace(key, val)
            image = imageFileHandler.ImageFileHandler(
                str(filename)).getImage()

            return (np.transpose(image), '%s' % (filename), "")
        except Exception as e:
            print(str(e))
            return str(e), "__ERROR__", ""
            pass  # this needs a bit more care
        return None, None, None

    def connect(self):
        try:
            fattr, dattr, dirtrans = str(
                self.signal_host).strip().split(",", 2)
            self.dirtrans = json.loads(dirtrans)
            if not self._initiated:
                self.fproxy = PyTango.AttributeProxy(fattr)
                if dattr:
                    self.dproxy = PyTango.AttributeProxy(dattr)
                else:
                    self.dproxy = None
            return True
        except Exception as e:
            print(str(e))
            return False

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
        self._initiated = False
        self.timeout = timeout
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
                    '%s  (%s)' % (self.signal_host, str(attr.time)), "")
        except Exception as e:
            print(str(e))
            return str(e), "__ERROR__", ""
            pass  # this needs a bit more care
        return None, None, None

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


class HTTPSource(object):

    def __init__(self, timeout=None):
        self.signal_host = None
        self.portnumber = "50001"
        self.target = [socket.getfqdn()]
        self._initiated = False
        self.timeout = timeout

    def getTarget(self):
        return self.target[0] + ":" + self.portnumber

    @QtCore.pyqtSlot(str)
    def setSignalHost(self, signalhost):
        if self.signal_host != signalhost:
            self.signal_host = signalhost
            self._initiated = False

    def getData(self):
        if self.signal_host:
            try:
                response = requests.get(self.signal_host)
                if response.ok:
                    name = self.signal_host
                    data = response.content
                    if data[:10] == "###CBF: VE":
                        # print("[cbf source module]::metadata", name)
                        img = imageFileHandler.CBFLoader().load(
                            np.fromstring(data[:], dtype=np.uint8))
                        return np.transpose(img), name, ""
                    else:
                        # print("[tif source module]::metadata", name)
                        if PILLOW:
                            img = np.array(PIL.Image.open(BytesIO(str(data))))
                            return np.transpose(img), name, ""
                        else:
                            img = imageFileHandler.TIFLoader().load(
                                np.fromstring(data[:], dtype=np.uint8))
                            return np.transpose(img), name, ""
            except Exception as e:
                print(str(e))
                return str(e), "__ERROR__", ""
        return None, None, None

    def connect(self):
        try:
            if self.signal_host:
                response = requests.get(self.signal_host)
                if response.ok:
                    return True
            return False
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
        self.timeout = timeout
        self._initiated = False
        self._context = zmq.Context()
        self._socket = None
        self._counter = 0
        self._topic = "10001"
        self._bindaddress = None
        self.__mutex = QtCore.QMutex()

    def getTarget(self):
        return self.target[0] + ":" + self.portnumber

    @QtCore.pyqtSlot(str)
    def setSignalHost(self, signalhost):
        if self.signal_host != signalhost:
            self.signal_host = signalhost
            self._initiated = False
            with QtCore.QMutexLocker(self.__mutex):
                if self._socket:
                    shost = str(self.signal_host).split("/")
                    topic = shost[1] if len(shost) > 1 else ""
                    self._socket.unbind(self._bindaddress)
                    # self._socket.setsockopt(zmq.UNSUBSCRIBE, self._topic)
                    # self._socket.setsockopt(zmq.UNSUBSCRIBE, "datasource")
                    # self._socket.setsockopt(zmq.SUBSCRIBE, "datasources")
                    # self._socket.setsockopt(zmq.SUBSCRIBE, topic)
                    self._topic = topic
                    self._socket.connect(self._bindaddress)

    def getData(self):
        try:
            with QtCore.QMutexLocker(self.__mutex):
                message = self._socket.recv_multipart(flags=zmq.NOBLOCK)
            topic = None
            _array = None
            shape = None
            dtype = None
            name = None
            lmsg = None
            metadata = None

            if isinstance(message, tuple) or isinstance(message, list):
                lmsg = len(message)
                topic = message[0]
            # print("topic %s %s" % (topic, self._topic))
            if topic == "datasources" and lmsg == 3:
                (topic, _array, _metadata) = message
                metadata = cPickle.loads(_metadata)
                jmetadata = ""
                if metadata:
                    jmetadata = json.dumps(metadata)
                return ("", "", jmetadata)
            elif self._topic == "" or topic == self._topic:
                if lmsg == 3:
                    (topic, _array, _metadata) = message
                    metadata = cPickle.loads(_metadata)
                    shape = metadata["shape"]
                    dtype = metadata["dtype"]
                    if "name" in metadata:
                        name = metadata["name"]
                    else:
                        name = '%s/%s (%s)' % (
                            self._bindaddress, topic, self._counter)
                else:
                    if lmsg == 4:
                        (topic, _array, _shape, _dtype) = message
                        name = '%s/%s (%s)' % (
                            self._bindaddress, topic, self._counter)
                    elif lmsg == 5:
                        (topic, _array, _shape, _dtype, name) = message
                    dtype = cPickle.loads(_dtype)
                    shape = cPickle.loads(_shape)

            if _array:
                array = np.frombuffer(buffer(_array), dtype=dtype)
                array = array.reshape(shape)
                array = np.transpose(array)
                self._counter += 1
                jmetadata = ""
                if metadata:
                    jmetadata = json.dumps(metadata)
                return (np.transpose(array), name, jmetadata)

        except zmq.Again as e:
            pass
        except Exception as e:
            # print(str(e))
            return str(e), "__ERROR__", ""
        return None, None, None

    def connect(self):
        try:
            shost = str(self.signal_host).split("/")
            host, port = str(shost[0]).split(":")
            self._topic = shost[1] if len(shost) > 1 else ""
            hwm = int(shost[2]) if (len(shost) > 2 and shost[2]) else 1
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
                    # self._socket.setsockopt(zmq.SUBSCRIBE, self._topic)
                    # self._socket.setsockopt(zmq.SUBSCRIBE, "datasources")
                    self._socket.setsockopt(zmq.SUBSCRIBE, "")
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
        self.timeout = timeout
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
                # [metadata, data] = self.query.get()
                [metadata, data] = self.query.get(self.timeout)
        except:
            pass  # this needs a bit more care

        if metadata is not None and data is not None:
            # print("data", str(data)[:10])

            if data[:10] == "###CBF: VE":
                print("[cbf source module]::metadata", metadata["filename"])
                img = imageFileHandler.CBFLoader().load(
                    np.fromstring(data[:], dtype=np.uint8))
                return np.transpose(img), metadata["filename"], ""
            else:
                # elif data[:2] in ["II\x2A\x00", "MM\x00\x2A"]:
                print("[tif source module]::metadata", metadata["filename"])
                if PILLOW:
                    img = np.array(PIL.Image.open(BytesIO(str(data))))
                    return np.transpose(img), metadata["filename"], ""
                else:
                    img = imageFileHandler.TIFLoader().load(
                        np.fromstring(data[:], dtype=np.uint8))
                    return np.transpose(img), metadata["filename"], ""
            # else:
            #     print(
            #       "[unknown source module]::metadata", metadata["filename"])
        else:
            return None, None, None
