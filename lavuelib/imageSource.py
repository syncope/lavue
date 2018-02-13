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
import json
import struct

try:
    import requests
    #: (:obj:`bool`) requests imported
    REQUESTS = True
except ImportError:
    #: (:obj:`bool`) requests imported
    REQUESTS = False

try:
    import hidra
    #: (:obj:`bool`) hidra imported
    HIDRA = True
except ImportError:
    #: (:obj:`bool`) hidra imported
    HIDRA = False

try:
    import PyTango
    #: (:obj:`bool`) PyTango imported
    PYTANGO = True
except ImportError:
    #: (:obj:`bool`) PyTango imported
    PYTANGO = False

try:
    import PIL
    #: (:obj:`bool`) PIL imported
    PILLOW = True
except ImportError:
    #: (:obj:`bool`) PIL imported
    PILLOW = False

try:
    import zmq
    #: (:obj:`str`,:obj:`str`) zmq major version, zmq minor version
    ZMQMAJOR, ZMQMINOR = map(int, zmq.zmq_version().split(".")[:2])
except:
    #: (:obj:`str`,:obj:`str`) zmq major version, zmq minor version
    ZMQMAJOR, ZMQMINOR = 0, 0


import socket
import numpy as np
import random
import time
import cPickle

from io import BytesIO
from . import imageFileHandler


class BaseSource(object):

    """ source base class"""

    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        #: (:obj:`int`) timeout in ms
        self._timeout = timeout
        #: (:obj:`str`) configuration string
        self._configuration = None
        #: (:obj:`bool`) connection initiated  flag
        self._initiated = False
        #: (:obj:`int`) internal counter
        self.__counter = 0

    def getMetaData(self):
        """ get metadata

        :returns: dictionary with metadata
        :rtype: :obj:`dict` <:obj:`str`, :obj:`any`>
        """
        return {}

    @QtCore.pyqtSlot(str)
    def setConfiguration(self, configuration):
        """ set configuration

        :param configuration:  configuration string
        :type configuration: :obj:`str`
        """
        if self._configuration != configuration:
            self._configuration = configuration
            self._initiated = False

    def setTimeOut(self, timeout):
        """ set timeout

        :param timeout: timeout in ms
        :type timeout: :obj:`int`
        """
        self._timeout = timeout

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        self.__counter += 1
        return (np.transpose(
            [
                [random.randint(0, 1000) for _ in range(512)]
                for _ in range(256)
            ]),
            '__random_%s__' % self.__counter, "")

    def connect(self):
        """ connects the source
        """
        self._initiated = True
        self.__counter = 0
        return True

    def disconnect(self):
        """ disconnects the source
        """
        try:
            pass
        except:
            pass


class TangoFileSource(BaseSource):

    """ image source as Tango attributes describing
        an image file name and its directory"""

    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        #: (:obj:`str`) configuration string
        self._configuration = None
        #: (:obj:`int`) timeout in ms
        self._timeout = timeout
        #: (:obj:`bool`) connection initiated  flag
        self._initiated = False
        #: (:class`PyTango.AttributeProxy`:)
        #:       device proxy for the image file name
        self.__fproxy = None
        #: (:class`PyTango.AttributeProxy`:)
        #:      device proxy for the image directory
        self.__dproxy = None
        #: (:dict: <:obj:`str`, :obj:`str`>)
        #:      translation dictionary for the image directory
        self.__dirtrans = {"/ramdisk/": "/gpfs/"}

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """

        try:
            filename = self.__fproxy.read().value
            if self.__dproxy:
                dattr = self.__dproxy.read().value
                filename = "%s/%s" % (dattr, filename)
                for key, val in self.__dirtrans.items():
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
        """ connects the source
        """
        try:
            fattr, dattr, dirtrans = str(
                self._configuration).strip().split(",", 2)
            self.__dirtrans = json.loads(dirtrans)
            if not self._initiated:
                self.__fproxy = PyTango.AttributeProxy(fattr)
                if dattr:
                    self.__dproxy = PyTango.AttributeProxy(dattr)
                else:
                    self.__dproxy = None
            return True
        except Exception as e:
            print(str(e))
            return False


class VDEOdecoder(object):

    """ VIDEO IMAGE LIMA decoder
    """

    def __init__(self):
        """ constructor

        :brief: It clears the local variables
        """
        #: (:obj:`str`) decoder name
        self.name = "LIMA_VIDEO_IMAGE"
        #: (:obj:`str`) decoder format
        self.format = None
        #: (:obj:`str`) data type
        self.dtype = None

        #: (:class:`numpy.ndarray`) image data
        self.__value = None
        #: ([:obj:`str`, :obj:`str`]) header and image data
        self.__data = None
        #: (:obj:`str`) struct header format
        self.__headerFormat = '!IHHqiiHHHH'
        #: (:obj:`dict` <:obj:`str`, :obj:`any` > ) header data
        self.__header = {}
        #: (:obj:`dict` <:obj:`int`, :obj:`str` > ) format modes
        self.__formatID = {0: 'B', 1: 'H', 2: 'I', 3: 'Q'}
        #: (:obj:`dict` <:obj:`int`, :obj:`str` > ) dtype modes
        self.__dtypeID = {0: 'uint8', 1: 'uint16', 2: 'uint32', 3: 'uint64'}

    def load(self, data):
        """  loads encoded data

        :param data: encoded data
        :type data: [:obj:`str`, :obj:`str`]
        """
        self.__data = data
        self.format = data[0]
        self._loadHeader(data[1][:struct.calcsize(self.__headerFormat)])
        self.__value = None

    def _loadHeader(self, headerData):
        """ loads the image header

        :param headerData: buffer with header data
        :type headerData: :obj:`str`
        """
        hdr = struct.unpack(self.__headerFormat, headerData)
        self.__header = {}
        self.__header['magic'] = hdr[0]
        self.__header['headerVersion'] = hdr[1]
        self.__header['imageMode'] = hdr[2]
        self.__header['frameNumber'] = hdr[3]
        self.__header['width'] = hdr[4]
        self.__header['height'] = hdr[5]
        self.__header['endianness'] = hdr[6]
        self.__header['headerSize'] = hdr[7]
        self.__header['padding'] = hdr[7:]

        self.dtype = self.__dtypeID[self.__header['imageMode']]

    def shape(self):
        """ provides the data shape

        :returns: the data shape if data was loaded
        :rtype: :obj:`list` <:obj:`int` >
        """
        if self.__header:
            return [self.__header['width'], self.__header['height']]

    def decode(self):
        """ provides the decoded data

        :returns: the decoded data if data was loaded
        :rtype: :class:`numpy.ndarray`
        """
        if not self.__header or not self.__data:
            return
        if not self.__value:
            image = self.__data[1][struct.calcsize(self.__headerFormat):]
            dformat = self.__formatID[self.__header['imageMode']]
            fSize = struct.calcsize(dformat)
            self.__value = np.array(
                struct.unpack(dformat * (len(image) // fSize), image),
                dtype=self.dtype).reshape(self.__header['width'],
                                          self.__header['height'])
        return self.__value


class TangoAttrSource(BaseSource):

    """ image source as IMAGE Tango attribute
    """

    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        #: (:obj:`int`) timeout in ms
        self._timeout = timeout
        #: (:obj:`str`) configuration string
        self._configuration = None
        #: (:obj:`bool`) connection initiated  flag
        self._initiated = False
        #: (:class`PyTango.AttributeProxy`:)
        #:      device proxy for the image attribute
        self.__aproxy = None
        #: (:dict: <:obj:`str`, :obj:`any`>)
        #:      dictionary of external decorders
        self.__decoders = {"LIMA_VIDEO_IMAGE": VDEOdecoder(),
                           "VIDEO_IMAGE": VDEOdecoder()}
        #: (:dict: <:obj:`str`, :obj:`str`>)
        #:      dictionary of tango decorders
        self.__tangodecoders = {
            "GRAY16": "decode_gray16",
            "GRAY8": "decode_gray8",
            "JPEG_GRAY8": "decode_gray8",
            "JPEG_RGB": "decode_rgb32",
            "RGB24": "decode_rgb32"
        }

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """

        try:
            attr = self.__aproxy.read()
            if str(attr.type) == "DevEncoded":
                avalue = attr.value
                if avalue[0] in self.__tangodecoders:
                    da = self.__aproxy.read(
                        extract_as=PyTango.ExtractAs.Nothing)
                    enc = PyTango.EncodedAttribute()
                    data = getattr(enc, self.__tangodecoders[avalue[0]])(da)
                    return (np.transpose(data),
                            '%s  (%s)' % (
                                self._configuration, str(attr.time)), "")
                else:
                    dec = self.__decoders[avalue[0]]
                    dec.load(avalue)
                    return (np.transpose(dec.decode()),
                            '%s  (%s)' % (
                                self._configuration, str(attr.time)), "")
            else:
                return (np.transpose(attr.value),
                        '%s  (%s)' % (
                            self._configuration, str(attr.time)), "")
        except Exception as e:
            print(str(e))
            return str(e), "__ERROR__", ""
            pass  # this needs a bit more care
        return None, None, None

    def connect(self):
        """ connects the source
        """
        try:
            if not self._initiated:
                self.__aproxy = PyTango.AttributeProxy(
                    str(self._configuration))
            return True
        except Exception as e:
            print(str(e))
            return False


class HTTPSource(BaseSource):

    """ image source as HTTP request response
    """

    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        #: (:obj:`str`) configuration string
        self._configuration = None
        #: (:obj:`int`) timeout in ms
        self._timeout = timeout
        #: (:obj:`bool`) connection initiated  flag
        self._initiated = False

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        if self._configuration:
            try:
                response = requests.get(self._configuration)
                if response.ok:
                    name = self._configuration
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
        """ connects the source
        """
        try:
            if self._configuration:
                response = requests.get(self._configuration)
                if response.ok:
                    return True
            return False
        except Exception as e:
            print(str(e))
            return False


class ZMQSource(BaseSource):

    """ image source as ZMQ stream"""

    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        #: (:obj:`str`) configuration string
        self._configuration = None
        #: (:obj:`int`) timeout in ms
        self._timeout = timeout
        #: (:obj:`bool`) connection initiated  flag
        self._initiated = False

        #: (:class:`zmq.Context`) zmq context
        self.__context = zmq.Context()
        #: (:class:`zmq.Socket`) zmq socket
        self.__socket = None
        #: (:obj:`int`) internal counter
        self.__counter = 0
        #: (:obj:`str`) zmq topic
        self.__topic = "10001"
        #: (:obj:`str`) zmq bind address
        self.__bindaddress = None
        #: (:class:`PyQt4.QtCore.QMutex`) zmq bind address
        self.__mutex = QtCore.QMutex()

    @QtCore.pyqtSlot(str)
    def setConfiguration(self, configuration):
        """ set configuration

        :param configuration:  configuration string
        :type configuration: :obj:`str`
        """
        if self._configuration != configuration:
            self._configuration = configuration
            self._initiated = False
            with QtCore.QMutexLocker(self.__mutex):
                if self.__socket:
                    shost = str(self._configuration).split("/")
                    topic = shost[1] if len(shost) > 1 else ""
                    self.__socket.unbind(self.__bindaddress)
                    self.__socket.setsockopt(zmq.UNSUBSCRIBE, self.__topic)
                    self.__socket.setsockopt(zmq.UNSUBSCRIBE, "datasources")
                    self.__socket.setsockopt(zmq.SUBSCRIBE, "datasources")
                    self.__socket.setsockopt(zmq.SUBSCRIBE, topic)
                    self.__topic = topic
                    self.__socket.connect(self.__bindaddress)

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        try:
            with QtCore.QMutexLocker(self.__mutex):
                message = self.__socket.recv_multipart(flags=zmq.NOBLOCK)
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
            # print("topic %s %s" % (topic, self.__topic))
            if topic == "datasources" and lmsg == 2:
                (topic, _metadata) = message
                metadata = cPickle.loads(_metadata)
                if "shape" in metadata:
                    metadata.pop("shape")
                if "dtype" in metadata:
                    metadata.pop("dtype")
                jmetadata = ""
                if metadata:
                    jmetadata = json.dumps(metadata)
                return ("", "", jmetadata)
            elif topic == "datasources" and lmsg == 3:
                (topic, _, _metadata) = message
                metadata = cPickle.loads(_metadata)
                if "shape" in metadata:
                    metadata.pop("shape")
                if "dtype" in metadata:
                    metadata.pop("dtype")
                jmetadata = ""
                if metadata:
                    jmetadata = json.dumps(metadata)
                return ("", "", jmetadata)
            elif self.__topic == "" or topic == self.__topic:
                if lmsg == 3:
                    (topic, _array, _metadata) = message
                    metadata = cPickle.loads(_metadata)
                    shape = metadata["shape"]
                    dtype = metadata["dtype"]
                    if "name" in metadata:
                        name = metadata["name"]
                    else:
                        name = '%s/%s (%s)' % (
                            self.__bindaddress, topic, self.__counter)
                else:
                    if lmsg == 4:
                        (topic, _array, _shape, _dtype) = message
                        name = '%s/%s (%s)' % (
                            self.__bindaddress, topic, self.__counter)
                    elif lmsg == 5:
                        (topic, _array, _shape, _dtype, name) = message
                    dtype = cPickle.loads(_dtype)
                    shape = cPickle.loads(_shape)

            if _array:
                array = np.frombuffer(buffer(_array), dtype=dtype)
                array = array.reshape(shape)
                array = np.transpose(array)
                self.__counter += 1
                jmetadata = ""
                if metadata:
                    metadata.pop("shape")
                    metadata.pop("dtype")
                    try:
                        jmetadata = json.dumps(metadata)
                    except:
                        pass
                return (np.transpose(array), name, jmetadata)

        except zmq.Again as e:
            pass
        except Exception as e:
            # print(str(e))
            return str(e), "__ERROR__", ""
        return None, None, None

    def connect(self):
        """ connects the source
        """
        try:
            shost = str(self._configuration).split("/")
            host, port = str(shost[0]).split(":")
            self.__topic = shost[1] if len(shost) > 1 else ""
            hwm = int(shost[2]) if (len(shost) > 2 and shost[2]) else 2
            if not self._initiated:
                if self.__socket:
                    self.disconnect()
                with QtCore.QMutexLocker(self.__mutex):
                    self.__socket = self.__context.socket(zmq.SUB)
                    if hwm is not None:
                        self.__socket.set_hwm(hwm)
                    self.__bindaddress = (
                        'tcp://'
                        + socket.gethostbyname(host)
                        + ':'
                        + str(port)
                    )
                    self.__socket.setsockopt(zmq.SUBSCRIBE, self.__topic)
                    self.__socket.setsockopt(zmq.SUBSCRIBE, "datasources")
                    # self.__socket.setsockopt(zmq.SUBSCRIBE, "")
                    self.__socket.connect(self.__bindaddress)
                time.sleep(0.2)
            return True
        except Exception as e:
            self.disconnect()
            print(str(e))
            return False

    def disconnect(self):
        """ disconnects the source
        """
        try:
            with QtCore.QMutexLocker(self.__mutex):
                if self.__socket:
                    if self.__bindaddress:
                        self.__socket.unbind(self.__bindaddress)
                    self.__socket.close(linger=0)
                    self.__socket = None
        except Exception as e:
            print(str(e))
            pass
        with QtCore.QMutexLocker(self.__mutex):
            self.__bindaddress = None

    def __del__(self):
        """ destructor
        """
        self.disconnect()
        self.__context.destroy()


class HiDRASource(BaseSource):

    """ hidra image source"""

    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        #: (:obj:`str`) configuration string
        self._configuration = None
        #: (:obj:`int`) timeout in ms
        self._timeout = timeout
        #: (:obj:`bool`) connection initiated  flag
        self._initiated = False

        #: (:obj:`str`) hidra port number
        self.__portnumber = "50001"
        #: (:obj:`list` < :obj:`str`, :obj:`str`,
        #:   :obj:`int` :obj:`list` < :obj:`str`> >) hidra target:
        #:   [host name, portnumber, priority, a list of extensions]
        self.__target = [socket.getfqdn(), self.__portnumber, 19,
                         [".cbf", ".tif", ".tiff"]]
        #: (:class:`hidra.transfer.Transfer`) hidra query
        self.__query = None
        #: (:class:`PyQt4.QtCore.QMutex`) zmq bind address
        self.__mutex = QtCore.QMutex()

    def getMetaData(self):
        """ get metadata

        :returns: dictionary with metadata
        :rtype: :obj:`dict` <:obj:`str`, :obj:`any`>
        """
        return {"targetname": self.__target[0] + ":" + self.__portnumber}

    @QtCore.pyqtSlot(str)
    def setConfiguration(self, configuration):
        """ set configuration

        :param configuration:  configuration string
        :type configuration: :obj:`str`
        """
        if self._configuration != configuration:
            self._configuration = configuration
            with QtCore.QMutexLocker(self.__mutex):
                self.__query = hidra.Transfer(
                    "QUERY_NEXT", self._configuration)
            self._initiated = False

    def connect(self):
        """ connects the source
        """
        try:
            if not self._initiated:
                with QtCore.QMutexLocker(self.__mutex):
                    self.__query.initiate(self.__target)
                self._initiated = True
                with QtCore.QMutexLocker(self.__mutex):
                    self.__query.start()
            return True
        except:
            if self.__query is not None:
                with QtCore.QMutexLocker(self.__mutex):
                    self.__query.stop()
            return False

    def disconnect(self):
        """ disconnects the source
        """
        try:
            if self.__query is not None:
                with QtCore.QMutexLocker(self.__mutex):
                    self.__query.stop()
        except:
            pass

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        metadata = None
        data = None
        try:
            with QtCore.QMutexLocker(self.__mutex):
                # [metadata, data] = self.__query.get()
                [metadata, data] = self.__query.get(self._timeout)
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
