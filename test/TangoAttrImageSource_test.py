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
#
import unittest
import os
import sys
import random
import struct
import binascii
import time
import logging
import json
import fabio
import numpy as np

import argparse
import lavuelib
import lavuelib.liveViewer
from pyqtgraph import QtGui
from pyqtgraph import QtCore
from pyqtgraph.Qt import QtTest


from qtchecker.qtChecker import (
    QtChecker, CmdCheck, ExtCmdCheck, WrapAttrCheck)

#  Qt-application
app = None

# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

if sys.version_info > (3,):
    long = int

try:
    from .LavueControllerSetUp import ControllerSetUp
    # from .LavueControllerSetUp import TangoCB
except Exception:
    from LavueControllerSetUp import ControllerSetUp
    # from LavueControllerSetUp import TangoCB

try:
    from .TestImageServerSetUp import TestImageServerSetUp
except Exception:
    from TestImageServerSetUp import TestImageServerSetUp

# Path
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(path))

#: python3 running
PY3 = (sys.version_info > (3,))


# test fixture
class TangoAttrImageSourceTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        global app
        if app is None:
            app = QtGui.QApplication([])
        app.setOrganizationName("DESY")
        app.setApplicationName("LaVue: unittests")
        app.setOrganizationDomain("desy.de")
        app.setApplicationVersion(lavuelib.__version__)

        self.__lcsu = ControllerSetUp()
        self.__tisu = TestImageServerSetUp()

        #: (:obj:`str`) lavue state
        self.__lavuestate = None

        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)
#        self.__seed = 332115341842367128541506422124286219441
        self.__rnd = random.Random(self.__seed)
        home = os.path.expanduser("~")
        self.__cfgfdir = "%s/%s" % (home, ".config/DESY")
        self.__cfgfname = "%s/%s" % (self.__cfgfdir, "LaVue: unittests.conf")
        self.__dialog = None
        self.__tangoimgcounter = 0
        self.__tangofilepattern = "%05d.tif"
        self.__tangofilepath = ""

        self.__defaultls = {
            '__timestamp__': 0.0,
            'version': lavuelib.__version__,
            'mode': 'user',
            'instance': 'test',
            'imagefile': '',
            'source': 'test',
            'configuration': '',
            'offset': '',
            'rangewindow': [None, None, None, None],
            'dsfactor': 1,
            'dsreduction': 'max',
            'filters': 0,
            'mbuffer': None,
            'channel': '',
            'bkgfile': '',
            'maskfile': '',
            'maskhighvalue': '',
            'transformation': 'none',
            'scaling': 'sqrt',
            'levels': '',
            'autofactor': '',
            'gradient': 'grey',
            'viewrange': '0,0,0,0',
            'connected': False,
            'tool': 'intensity',
            'tangodevice': 'test/lavuecontroller/00',
            'doordevice': '',
            'analysisdevice': '',
            'log': 'info',
        }

    def compareStates(self, state, defstate=None, exclude=None):
        if defstate is None:
            defstate = self.__defaultls
        if exclude is None:
            exclude = ['viewrange', '__timestamp__',
                       'configuration', 'source',
                       'doordevice']
        for ky, vl in defstate.items():
            if ky not in exclude:
                if state[ky] != vl:
                    print("%s: %s %s" % (ky, state[ky], vl))
                self.assertEqual(state[ky], vl)

    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.__seed)
        self.__lcsu.setUp()
        self.__tisu.setUp()
        home = os.path.expanduser("~")
        fname = "%s/%s" % (home, ".config/DESY/LaVue: unittests.conf")
        if os.path.exists(fname):
            print("removing '%s'" % fname)
            os.remove(fname)

    def tearDown(self):
        print("tearing down ...")
        self.__lcsu.tearDown()
        self.__tisu.tearDown()

    def getLavueState(self):
        self.__lavuestate = self.__lcsu.proxy.LavueState

    def takeNewImage(self):
        global app
        self.__tisu.proxy.StartAcq()
        li = self.__tisu.proxy.LastImage
        app.sendPostedEvents()
        # yieldCurrentThread()
        return li

    def takeNewSpectra(self):
        global app
        self.__tisu.proxy.StartAcq()
        l1 = self.__tisu.proxy.Spectrum1
        l2 = self.__tisu.proxy.Spectrum2
        app.sendPostedEvents()
        # yieldCurrentThread()
        return l1, l2

    def takeNewTangoFileImage(self):
        global app
        self.__tangoimgcounter += 1
        self.__tisu.proxy.LastImagePath = self.__tangofilepath
        self.__tisu.proxy.LastImageTaken = \
            self.__tangofilepattern % self.__tangoimgcounter
        fname = os.path.join(
            self.__tisu.proxy.LastImagePath,
            self.__tisu.proxy.LastImageTaken)
        image = fabio.open(fname)
        li = image.data
        app.sendPostedEvents()
        # yieldCurrentThread()
        return li

    def takeNewChangeEventImage(self):
        global app
        self.__tisu.proxy.ChangeEventAcq()
        li = self.__tisu.proxy.ChangeEventImage
        app.sendPostedEvents()
        # yieldCurrentThread()
        return li

    def takeNewReadyEventImage(self):
        global app
        self.__tisu.proxy.ReadyEventAcq()
        li = self.__tisu.proxy.ReadyEventImage
        app.sendPostedEvents()
        # yieldCurrentThread()
        return li

    def getControllerAttr(self, name):
        return getattr(self.__lcsu.proxy, name)

    def test_readimage(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__tisu.proxy.Init()
        self.__lavuestate = None
        lastimage = self.__tisu.proxy.LastImage.T

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/testimageserver/00/LastImage',
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='m20,20',
            gradient='thermal',
            start=True,
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck1 = QtChecker(app, dialog, True, sleep=100)
        qtck2 = QtChecker(app, dialog, True, sleep=100)
        qtck3 = QtChecker(app, dialog, True, sleep=100)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewImage"),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        print("execute")
        qtck1.executeChecks(delay=3000)
        qtck2.executeChecks(delay=6000)
        status = qtck3.executeChecksAndClose(delay=9000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, False], mask=[1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        self.assertTrue(np.allclose(res1[2], lastimage))

        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res1[3], scaledimage))

        lastimage = res1[4].T
        if not np.allclose(res2[1], lastimage):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res2[2], scaledimage))

        lastimage = res2[3].T
        self.assertTrue(np.allclose(res3[0], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res3[1], scaledimage))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/testimageserver/00/LastImage',
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=None
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_readspectra(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__tisu.proxy.Init()
        self.__lavuestate = None
        l1 = self.__tisu.proxy.Spectrum1
        l2 = self.__tisu.proxy.Spectrum2
        zs = np.zeros(dtype="float64", shape=l1.shape)
        zs[:] = np.NaN
        lastimage = np.stack([l1, zs, zs, l2], 1)
        options = argparse.Namespace(
            mode='expert',
            source='tangoattr;tangoattr',
            offset=';,3',
            configuration='test/testimageserver/00/Spectrum1;'
            'test/testimageserver/00/Spectrum2',
            instance='tgtest2',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='m20,20',
            gradient='thermal',
            start=True,
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck1 = QtChecker(app, dialog, True, sleep=100)
        qtck2 = QtChecker(app, dialog, True, sleep=100)
        qtck3 = QtChecker(app, dialog, True, sleep=100)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewSpectra"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewSpectra"),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        print("execute")
        qtck1.executeChecks(delay=3000)
        qtck2.executeChecks(delay=6000)
        status = qtck3.executeChecksAndClose(delay=9000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, False], mask=[1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
            print(res1[2] - lastimage)
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res1[3], scaledimage, equal_nan=True))

        l1, l2 = res1[4]
        lastimage = np.stack([l1, zs, zs, l2], 1)
        if not np.allclose(res2[1], lastimage, equal_nan=True):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res2[2], scaledimage, equal_nan=True))

        l1, l2 = res2[3]
        lastimage = np.stack([l1, zs, zs, l2], 1)

        self.assertTrue(np.allclose(res3[0], lastimage, equal_nan=True))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res3[1], scaledimage, equal_nan=True))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr;tangoattr',
            configuration='test/testimageserver/00/Spectrum1;'
            'test/testimageserver/00/Spectrum2',
            offset=';,3',
            instance='tgtest2',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=None
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def ttest_readspectra_color(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__tisu.proxy.Init()
        self.__lavuestate = None
        l1 = self.__tisu.proxy.Spectrum1
        l2 = self.__tisu.proxy.Spectrum2
        lsh = l1.shape
        zs = np.zeros(dtype="float64", shape=lsh)
        zs[:] = np.nan
        ll1 = np.stack([l1, zs, zs, zs], 1)
        ll2 = np.stack([zs, zs, zs, l2], 1)
        zzs = np.stack([zs, zs, zs, zs], 1)
        zzs[:] = np.nan
        lastimage = np.stack([ll1, ll2, zzs], 2)

        cfg = '[Configuration]\n' \
            'ShowSubtraction=false\n' \
            'ShowTransformations=false\n' \
            'ImageChannels=true\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr;tangoattr',
            offset=';,3',
            configuration='test/testimageserver/00/Spectrum1;'
            'test/testimageserver/00/Spectrum2',
            instance='tgtest2',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            # gradient='thermal',
            channel='rgb',
            start=True,
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck1 = QtChecker(app, dialog, True, sleep=100)
        qtck2 = QtChecker(app, dialog, True, sleep=100)
        qtck3 = QtChecker(app, dialog, True, sleep=100)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewSpectra"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewSpectra"),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        print("execute")
        qtck1.executeChecks(delay=3000)
        qtck2.executeChecks(delay=6000)
        status = qtck3.executeChecksAndClose(delay=9000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, False], mask=[1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
            print(res1[2] - lastimage)
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res1[3], scaledimage, equal_nan=True))

        l1, l2 = res1[4]
        ll1 = np.stack([l1, zs, zs, zs], 1)
        ll2 = np.stack([zs, zs, zs, l2], 1)
        lastimage = np.stack([ll1, ll2, zzs], 2)
        if not np.allclose(res2[1], lastimage, equal_nan=True):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res2[2], scaledimage, equal_nan=True))

        l1, l2 = res2[3]
        ll1 = np.stack([l1, zs, zs, zs], 1)
        ll2 = np.stack([zs, zs, zs, l2], 1)
        lastimage = np.stack([ll1, ll2, zzs], 2)

        self.assertTrue(np.allclose(res3[0], lastimage, equal_nan=True))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res3[1], scaledimage, equal_nan=True))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr;tangoattr',
            configuration='test/testimageserver/00/Spectrum1;'
            'test/testimageserver/00/Spectrum2',
            offset=';,3',
            instance='tgtest2',
            tool='rgbintensity',
            # log='debug',
            log='info',
            scaling='log',
            # levels='',
            channel='0,1,-1',
            #  gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=''
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def ttest_readimage_color(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__tisu.proxy.Init()
        self.__lavuestate = None
        l1 = self.__tisu.proxy.LastImage.T
        lsh = l1.shape
        zzs = np.zeros(dtype="float64", shape=[lsh[0], lsh[1] + 6])
        zzs[:] = np.nan
        ll1 = np.array(zzs)
        ll2 = np.array(zzs)
        ll3 = np.array(zzs)
        ll1[0:lsh[0], 0:lsh[1]] = l1
        ll2[0:lsh[0], 3:lsh[1]+3] = l1
        ll3[0:lsh[0], 6:lsh[1]+6] = l1
        lastimage = np.stack([ll1, ll2, ll3], 2)

        cfg = '[Configuration]\n' \
            'ShowSubtraction=false\n' \
            'ShowTransformations=false\n' \
            'ImageChannels=true\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr;tangoattr;tangoattr',
            offset=';,3;,6',
            configuration='test/testimageserver/00/LastImage;'
            'test/testimageserver/00/LastImage;'
            'test/testimageserver/00/LastImage',
            instance='tgtest2',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            # gradient='thermal',
            channel='rgb',
            start=True,
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck1 = QtChecker(app, dialog, True, sleep=100)
        qtck2 = QtChecker(app, dialog, True, sleep=100)
        qtck3 = QtChecker(app, dialog, True, sleep=100)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewImage"),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        print("execute")
        qtck1.executeChecks(delay=3000)
        qtck2.executeChecks(delay=6000)
        status = qtck3.executeChecksAndClose(delay=9000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, False], mask=[1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
            print(res1[2] - lastimage)
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res1[3], scaledimage, equal_nan=True))

        l1 = res1[4].T
        ll1 = np.array(zzs)
        ll2 = np.array(zzs)
        ll3 = np.array(zzs)
        ll1[0:lsh[0], 0:lsh[1]] = l1
        ll2[0:lsh[0], 3:lsh[1]+3] = l1
        ll3[0:lsh[0], 6:lsh[1]+6] = l1
        lastimage = np.stack([ll1, ll2, ll3], 2)
        if not np.allclose(res2[1], lastimage, equal_nan=True):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res2[2], scaledimage, equal_nan=True))

        l1 = res2[3].T
        ll1 = np.array(zzs)
        ll2 = np.array(zzs)
        ll3 = np.array(zzs)
        ll1[0:lsh[0], 0:lsh[1]] = l1
        ll2[0:lsh[0], 3:lsh[1]+3] = l1
        ll3[0:lsh[0], 6:lsh[1]+6] = l1
        lastimage = np.stack([ll1, ll2, ll3], 2)

        self.assertTrue(np.allclose(res3[0], lastimage, equal_nan=True))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res3[1], scaledimage, equal_nan=True))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr;tangoattr;tangoattr',
            configuration='test/testimageserver/00/LastImage;'
            'test/testimageserver/00/LastImage;'
            'test/testimageserver/00/LastImage',
            offset=';,3;,6',
            instance='tgtest2',
            tool='rgbintensity',
            # log='debug',
            log='info',
            scaling='log',
            # levels='',
            channel='0,1,2',
            #  gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=''
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_readimage_sum(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__tisu.proxy.Init()
        self.__lavuestate = None
        l1 = self.__tisu.proxy.LastImage.T
        lsh = l1.shape
        zzs = np.zeros(dtype="float64", shape=[lsh[0], lsh[1] + 6])
        zzs[:] = np.nan
        ll1 = np.array(zzs)
        ll2 = np.array(zzs)
        ll3 = np.array(zzs)
        ll1[0:lsh[0], 0:lsh[1]] = l1
        ll2[0:lsh[0], 3:lsh[1]+3] = l1
        ll3[0:lsh[0], 6:lsh[1]+6] = l1
        lastimage = np.stack([ll1, ll2, ll3], 2)
        lastimage = np.nansum(lastimage, 2)

        cfg = '[Configuration]\n' \
            'ShowSubtraction=false\n' \
            'ShowTransformations=false\n' \
            'ImageChannels=true\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr;tangoattr;tangoattr',
            offset=';,3;,6',
            configuration='test/testimageserver/00/LastImage;'
            'test/testimageserver/00/LastImage;'
            'test/testimageserver/00/LastImage',
            instance='tgtest2',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            # gradient='thermal',
            channel='sum',
            start=True,
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck1 = QtChecker(app, dialog, True, sleep=100)
        qtck2 = QtChecker(app, dialog, True, sleep=100)
        qtck3 = QtChecker(app, dialog, True, sleep=100)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewImage"),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        print("execute")
        qtck1.executeChecks(delay=3000)
        qtck2.executeChecks(delay=6000)
        status = qtck3.executeChecksAndClose(delay=9000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, False], mask=[1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
            print(res1[2] - lastimage)
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res1[3], scaledimage, equal_nan=True))

        l1 = res1[4].T
        ll1 = np.array(zzs)
        ll2 = np.array(zzs)
        ll3 = np.array(zzs)
        ll1[0:lsh[0], 0:lsh[1]] = l1
        ll2[0:lsh[0], 3:lsh[1]+3] = l1
        ll3[0:lsh[0], 6:lsh[1]+6] = l1
        lastimage = np.stack([ll1, ll2, ll3], 2)
        lastimage = np.nansum(lastimage, 2)
        if not np.allclose(res2[1], lastimage, equal_nan=True):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res2[2], scaledimage, equal_nan=True))

        l1 = res2[3].T
        ll1 = np.array(zzs)
        ll2 = np.array(zzs)
        ll3 = np.array(zzs)
        ll1[0:lsh[0], 0:lsh[1]] = l1
        ll2[0:lsh[0], 3:lsh[1]+3] = l1
        ll3[0:lsh[0], 6:lsh[1]+6] = l1
        lastimage = np.stack([ll1, ll2, ll3], 2)
        lastimage = np.nansum(lastimage, 2)

        self.assertTrue(np.allclose(res3[0], lastimage, equal_nan=True))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res3[1], scaledimage, equal_nan=True))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr;tangoattr;tangoattr',
            configuration='test/testimageserver/00/LastImage;'
            'test/testimageserver/00/LastImage;'
            'test/testimageserver/00/LastImage',
            offset=';,3;,6',
            instance='tgtest2',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            # levels='',
            channel='sum',
            #  gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=''
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_readchangeeventimage(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__tisu.proxy.Init()
        self.__lavuestate = None
        lastimage = self.__tisu.proxy.ChangeEventImage.T

        options = argparse.Namespace(
            mode='expert',
            source='tangoevents',
            configuration='test/testimageserver/00/ChangeEventImage',
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='m20,20',
            gradient='thermal',
            start=True,
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck1 = QtChecker(app, dialog, True, sleep=100)
        qtck2 = QtChecker(app, dialog, True, sleep=100)
        qtck3 = QtChecker(app, dialog, True, sleep=100)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewChangeEventImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewChangeEventImage"),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        print("execute")
        qtck1.executeChecks(delay=3000)
        qtck2.executeChecks(delay=6000)
        status = qtck3.executeChecksAndClose(delay=9000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, False], mask=[1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        self.assertTrue(np.allclose(res1[2], lastimage))

        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res1[3], scaledimage))

        lastimage = res1[4].T
        if not np.allclose(res2[1], lastimage):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res2[2], scaledimage))

        lastimage = res2[3].T
        self.assertTrue(np.allclose(res3[0], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res3[1], scaledimage))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoevents',
            configuration='test/testimageserver/00/ChangeEventImage',
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=None
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_readreadyeventimage(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__tisu.proxy.Init()
        self.__lavuestate = None
        # lastimage = self.__tisu.proxy.ReadyEventImage.T
        lastimage = None

        options = argparse.Namespace(
            mode='expert',
            source='tangoevents',
            configuration='test/testimageserver/00/ReadyEventImage',
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='m20,20',
            gradient='thermal',
            start=True,
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck1 = QtChecker(app, dialog, True, sleep=100)
        qtck2 = QtChecker(app, dialog, True, sleep=100)
        qtck3 = QtChecker(app, dialog, True, sleep=100)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewReadyEventImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewReadyEventImage"),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        print("execute")
        qtck1.executeChecks(delay=3000)
        qtck2.executeChecks(delay=6000)
        status = qtck3.executeChecksAndClose(delay=9000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, False], mask=[1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        self.assertEqual(res1[2], None)
        self.assertEqual(res1[3], None)
        # self.assertTrue(np.allclose(res1[2], lastimage))

        # scaledimage = np.clip(lastimage, 10e-3, np.inf)
        # scaledimage = np.log10(scaledimage)
        # self.assertTrue(np.allclose(res1[3], scaledimage))

        lastimage = res1[4].T
        if not np.allclose(res2[1], lastimage):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res2[2], scaledimage))

        lastimage = res2[3].T
        self.assertTrue(np.allclose(res3[0], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res3[1], scaledimage))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoevents',
            configuration='test/testimageserver/00/ReadyEventImage',
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=None
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_readtangofileimage(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__tisu.proxy.Init()
        self.__lavuestate = None
        # lastimage = self.__tisu.proxy.ReadyEventImage.T
        lastimage = None
        self.__tangoimgcounter = 0
        self.__tangofilepath = "%s/%s" % (os.path.abspath(path), "test/images")
        self.__tangofilepattern = "%05d.tif"
        options = argparse.Namespace(
            mode='expert',
            source='tangofile',
            configuration='test/testimageserver/00/LastImageTaken,'
            'test/testimageserver/00/LastImagePath',
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='m20,20',
            gradient='thermal',
            start=True,
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck1 = QtChecker(app, dialog, True, sleep=100)
        qtck2 = QtChecker(app, dialog, True, sleep=100)
        qtck3 = QtChecker(app, dialog, True, sleep=100)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewTangoFileImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewTangoFileImage"),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        print("execute")
        qtck1.executeChecks(delay=3000)
        qtck2.executeChecks(delay=6000)
        status = qtck3.executeChecksAndClose(delay=9000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, False], mask=[1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        self.assertEqual(res1[2], None)
        self.assertEqual(res1[3], None)
        # self.assertTrue(np.allclose(res1[2], lastimage))

        # scaledimage = np.clip(lastimage, 10e-3, np.inf)
        # scaledimage = np.log10(scaledimage)
        # self.assertTrue(np.allclose(res1[3], scaledimage))

        lastimage = res1[4].T
        if not np.allclose(res2[1], lastimage):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res2[2], scaledimage))

        lastimage = res2[3].T
        self.assertTrue(np.allclose(res3[0], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res3[1], scaledimage))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangofile',
            configuration='test/testimageserver/00/LastImageTaken,'
            'test/testimageserver/00/LastImagePath,{"/ramdisk/": "/gpfs/"}',
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=None
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()
