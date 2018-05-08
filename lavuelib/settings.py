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
#     Christoph Rosemann <christoph.rosemann@desy.de>
#     Jan Kotanski <jan.kotanski@desy.de>
#


""" live viewer image display base it on a qt dialog """


from PyQt4 import QtCore
import zmq


class Settings(object):

    """ lavue configuration settings """

    def __init__(self):
        """ constructor
        """

        #: (:obj:`bool`) sardana enabled
        self.sardana = True
        #: (:obj:`bool`) add rois to sardana
        self.addrois = True
        #: (:obj:`bool`) search for security stream port automatically
        self.secautoport = True
        #: (:obj:`bool`) show intensity hostogram
        self.showhisto = True
        #: (:obj:`bool`) show mask widget
        self.showmask = False
        #: (:obj:`bool`) show mask widget
        self.showstats = True
        #: (:obj:`bool`) show bakcground subtraction widget
        self.showsub = True
        #: (:obj:`bool`) show transformation widget
        self.showtrans = True
        #: (:obj:`bool`) show intensity scale widget
        self.showscale = True
        #: (:obj:`bool`) show intensity levels widget
        self.showlevels = True
        #: (:obj:`bool`) image aspect ratio locked
        self.aspectlocked = False
        #: (:obj:`bool`) auto down sample
        self.autodownsample = False
        #: (:obj:`str`) security stream port
        self.secport = "5657"
        #: (:obj:`str`) hidra data port
        self.hidraport = "50001"
        #: (:obj:`int`) image source timeout for connection
        self.timeout = 3000
        #: (:class:`zmq.Context`) zmq context
        self.seccontext = zmq.Context()
        #: (:class:`zmq.Socket`) zmq security stream socket
        self.secsocket = self.seccontext.socket(zmq.PUB)
        #: (:obj:`bool`) security stream enabled
        self.secstream = False
        #: (:obj:`bool`) security stream options
        self.secsockopt = ""
        #: (:obj:`float`) refresh rate
        self.refreshrate = 0.1
        #: (:obj:`bool`) interrupt on error
        self.interruptonerror = True
        #: (:obj:`str`) last image file name
        self.imagename = None
        #: (:obj:`bool`) statistics without scaling
        self.statswoscaling = False
        #: (:obj:`list` < :obj:`str` > ) zmq source topics
        self.zmqtopics = []
        #: (:obj:`bool`) automatic zmq source topics
        self.autozmqtopics = False
        #: (:obj:`str`) file name translation json dictionary
        self.dirtrans = '{"/ramdisk/": "/gpfs/"}'
        #: (:obj:`str`) JSON dictionary with {label: tango attribute}
        #  for Tango Attribute source
        self.tangoattrs = '{}'
        #: (:obj:`str`) door device name
        self.doorname = ""
        #: (:obj:`bool`) nexus file source keeps the file open
        self.nxsopen = False
        #: (:obj:`bool`) nexus file source starts from the last image
        self.nxslast = False
        #: (:obj:`list` < :obj:`str`>) hidra detector server list
        self.detservers = []
        #: (:obj:`bool`) store detector geometry
        self.storegeometry = False

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

    def load(self, settings):
        """ load settings

        :param settings: QSettings object
        :type settings: :class:`PyQt4.QtCore.QSettings`
        :returns: error messages list
        :rtype: :obj:`list` < (:obj:`str`, :obj:`str`) >
        """
        status = []
        qstval = str(settings.value("Configuration/Sardana").toString())
        if qstval.lower() == "false":
            self.sardana = False
        else:
            self.sardana = True
        qstval = str(settings.value("Configuration/AddROIs").toString())
        if qstval.lower() == "false":
            self.addrois = False
        qstval = str(settings.value("Configuration/SecAutoPort").toString())
        if qstval.lower() == "false":
            self.secautoport = False
        qstval = str(settings.value(
            "Configuration/ShowSubtraction").toString())
        if qstval.lower() == "false":
            self.showsub = False
        qstval = str(settings.value(
            "Configuration/ShowTransformations").toString())
        if qstval.lower() == "false":
            self.showtrans = False
        qstval = str(settings.value(
            "Configuration/ShowIntensityScaling").toString())
        if qstval.lower() == "false":
            self.showscale = False
        qstval = str(settings.value(
            "Configuration/ShowIntensityLevels").toString())
        if qstval.lower() == "false":
            self.showlevels = False
        qstval = str(settings.value("Configuration/ShowHistogram").toString())
        if qstval.lower() == "false":
            self.showhisto = False
        qstval = str(settings.value("Configuration/ShowMaskWidget").toString())
        if qstval.lower() == "true":
            self.showmask = True
        qstval = str(settings.value("Configuration/ShowStatistics").toString())
        if qstval.lower() == "false":
            self.showstats = False
        qstval = str(settings.value("Configuration/AspectLocked").toString())
        if qstval.lower() == "true":
            self.aspectlocked = True
        qstval = str(settings.value("Configuration/AutoDownSample").toString())
        if qstval.lower() == "true":
            self.autodownsample = True
        qstval = str(settings.value("Configuration/NXSFileOpen").toString())
        if qstval.lower() == "true":
            self.nxsopen = True
        qstval = str(settings.value("Configuration/NXSLastImage").toString())
        if qstval.lower() == "true":
            self.nxslast = True
        qstval = str(settings.value("Configuration/SecPort").toString())
        try:
            int(qstval)
            self.secport = str(qstval)
        except:
            pass
        qstval = str(settings.value("Configuration/HidraDataPort").toString())
        try:
            int(qstval)
            self.hidraport = str(qstval)
        except:
            pass
        qstval = str(settings.value("Configuration/SourceTimeout").toString())
        try:
            int(qstval)
            self.timeout = int(qstval)
        except:
            pass
        qstval = str(settings.value("Configuration/SecStream").toString())
        if qstval.lower() == "true":
            try:
                if self.secautoport:
                    self.secsockopt = "tcp://*:*"
                    self.secsocket.bind(self.secsockopt)
                    self.secport = self.secsocket.getsockopt(
                        zmq.LAST_ENDPOINT).split(":")[-1]
                else:
                    self.secsockopt = "tcp://*:%s" % self.secport
                    self.secsocket.bind(self.secsockopt)
                self.secstream = True
            except:
                self.secstream = False
                import traceback
                value = traceback.format_exc()
                text = "lavue: Cannot connect to: %s" % self.secsockopt
                status = [(text, value)]

        try:
            self.refreshrate = float(
                settings.value("Configuration/RefreshRate").toString())
        except:
            pass

        qstval = str(
            settings.value("Configuration/InterruptOnError").toString())
        if qstval.lower() == "false":
            self.interruptonerror = False
        elif qstval.lower() == "true":
            self.interruptonerror = True
        qstval = str(
            settings.value("Configuration/LastImageFileName").toString())
        if qstval:
            self.imagename = qstval
        qstval = str(
            settings.value(
                "Configuration/StatisticsWithoutScaling").toString())
        if qstval.lower() == "true":
            self.statswoscaling = True

        qstval = \
            settings.value("Configuration/ZMQStreamTopics").toList()
        if qstval:
            self.zmqtopics = [str(tp.toString()) for tp in qstval]

        qstval = \
            settings.value("Configuration/HidraDetectorServers").toList()
        if qstval:
            self.detservers = [str(tp.toString()) for tp in qstval]

        qstval = str(settings.value(
            "Configuration/AutoZMQStreamTopics").toString())
        if qstval.lower() == "true":
            self.autozmqtopics = True
        qstval = str(
            settings.value("Configuration/DirectoryTranslation").toString())
        if qstval:
            self.dirtrans = qstval

        qstval = str(
            settings.value("Configuration/TangoAttributes").toString())
        if qstval:
            self.tangoattrs = qstval

        qstval = str(
            settings.value("Configuration/StoreGeometry").toString())
        if qstval.lower() == "true":
            self.storegeometry = True

        try:
            self.centerx = float(
                settings.value("Tools/CenterX").toString())
        except:
            pass
        try:
            self.centery = float(
                settings.value("Tools/CenterY").toString())
        except:
            pass
        try:
            self.energy = float(
                settings.value("Tools/Energy").toString())
        except:
            pass

        try:
            self.pixelsizex = float(
                settings.value("Tools/PixelSizeX").toString())
        except:
            pass
        try:
            self.pixelsizey = float(
                settings.value("Tools/PixelSizeY").toString())
        except:
            pass
        try:
            self.detdistance = float(
                settings.value("Tools/DetectorDistance").toString())
        except:
            pass
        return status

    def store(self, settings):
        """ Stores settings in QSettings object

        :param settings: QSettings object
        :type settings: :class:`PyQt4.QtCore.QSettings`
        """
        settings.setValue(
            "Configuration/AddROIs",
            QtCore.QVariant(self.addrois))
        settings.setValue(
            "Configuration/ShowSubtraction",
            QtCore.QVariant(self.showsub))
        settings.setValue(
            "Configuration/ShowTransformations",
            QtCore.QVariant(self.showtrans))
        settings.setValue(
            "Configuration/ShowIntensityScaling",
            QtCore.QVariant(self.showscale))
        settings.setValue(
            "Configuration/ShowIntensityLevels",
            QtCore.QVariant(self.showlevels))
        settings.setValue(
            "Configuration/ShowHistogram",
            QtCore.QVariant(self.showhisto))
        settings.setValue(
            "Configuration/ShowMaskWidget",
            QtCore.QVariant(self.showmask))
        settings.setValue(
            "Configuration/ShowStatistics",
            QtCore.QVariant(self.showstats))
        settings.setValue(
            "Configuration/RefreshRate",
            QtCore.QVariant(self.refreshrate))
        settings.setValue(
            "Configuration/SecPort",
            QtCore.QVariant(self.secport))
        settings.setValue(
            "Configuration/HidraDataPort",
            QtCore.QVariant(self.hidraport))
        settings.setValue(
            "Configuration/SecAutoPort",
            QtCore.QVariant(self.secautoport))
        settings.setValue(
            "Configuration/SecStream",
            QtCore.QVariant(self.secstream))
        settings.setValue(
            "Configuration/Sardana",
            QtCore.QVariant(self.sardana))
        settings.setValue(
            "Configuration/InterruptOnError",
            QtCore.QVariant(self.interruptonerror))
        settings.setValue(
            "Configuration/SourceTimeout",
            QtCore.QVariant(self.timeout))
        settings.setValue(
            "Configuration/AspectLocked",
            QtCore.QVariant(self.aspectlocked))
        settings.setValue(
            "Configuration/AutoDownSample",
            QtCore.QVariant(self.autodownsample))
        settings.setValue(
            "Configuration/LastImageFileName",
            QtCore.QVariant(self.imagename))
        settings.setValue(
            "Configuration/StatisticsWithoutScaling",
            QtCore.QVariant(self.statswoscaling))
        settings.setValue(
            "Configuration/ZMQStreamTopics",
            QtCore.QVariant(self.zmqtopics))
        settings.setValue(
            "Configuration/HidraDetectorServers",
            QtCore.QVariant(self.detservers))
        settings.setValue(
            "Configuration/AutoZMQStreamTopics",
            QtCore.QVariant(self.autozmqtopics))
        settings.setValue(
            "Configuration/DirectoryTranslation",
            QtCore.QVariant(self.dirtrans))
        settings.setValue(
            "Configuration/TangoAttributes",
            QtCore.QVariant(self.tangoattrs))
        settings.setValue(
            "Configuration/NXSLastImage",
            QtCore.QVariant(self.nxslast))
        settings.setValue(
            "Configuration/NXSFileOpen",
            QtCore.QVariant(self.nxsopen))
        settings.setValue(
            "Configuration/StoreGeometry",
            QtCore.QVariant(self.storegeometry))

        if not self.storegeometry:
            self.centerx = 0.0
            self.centery = 0.0
            self.energy = 0.0
            self.pixelsizex = 0.0
            self.pixelsizey = 0.0
            self.detdistance = 0.0

        settings.setValue(
            "Tools/CenterX",
            QtCore.QVariant(self.centerx))
        settings.setValue(
            "Tools/CenterY",
            QtCore.QVariant(self.centery))
        settings.setValue(
            "Tools/Energy",
            QtCore.QVariant(self.energy))
        settings.setValue(
            "Tools/PixelSizeX",
            QtCore.QVariant(self.pixelsizex))
        settings.setValue(
            "Tools/PixelSizeY",
            QtCore.QVariant(self.pixelsizey))
        settings.setValue(
            "Tools/DetectorDistance",
            QtCore.QVariant(self.detdistance))
