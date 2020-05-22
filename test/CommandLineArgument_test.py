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

import argparse
import lavuelib
import lavuelib.liveViewer
from pyqtgraph import QtGui
from pyqtgraph import QtCore
from pyqtgraph.Qt import QtTest
#  Qt-application
app = None

# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

if sys.version_info > (3,):
    unicode = str
    long = int


# test fixture
class CommandLineArgumentTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        global app
        if app is None:
            app = QtGui.QApplication([])
        app.setOrganizationName("DESY")
        app.setApplicationName("LaVue: unittests")
        app.setOrganizationDomain("desy.de")
        app.setApplicationVersion(lavuelib.__version__)

        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)
#        self.__seed = 332115341842367128541506422124286219441
        self.__rnd = random.Random(self.__seed)
        self.__dialog = None
        self.__commands = []
        self.__results = []

    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.__seed)
        home = os.path.expanduser("~")
        fname = "%s/%s" % (home, ".config/DESY/LaVue: unittests.conf")
        if os.path.exists(fname):
            print("removing '%s'" % fname)
            os.remove(fname)

    def tearDown(self):
        print("tearing down ...")

    def closeDialog(self):
        if self.__dialog:
            self.__dialog.close()
            sys.stderr.write("Close Dialog\n")
            self.__dialog = None

    def executeAndClose(self):
        for cd in self.__commands:
            cdl = cd[0].split(".")
            if cdl:
                parent = self.__dialog
                for cm in cdl[:-1]:
                    if "[]," in cm:
                        scm = cm.split(",")
                        cm = scm[0][:-2]
                        idx = int(scm[1])
                        parent = getattr(parent, cm)[idx]
                    else:
                        parent = getattr(parent, cm)
                if cdl[-1].endswith("()"):
                    cmd = getattr(parent, cdl[-1][:-2])
                    if cd[1]:
                        self.__results.append(cmd(**cd[1]))
                    else:
                        self.__results.append(cmd())
                else:
                    if len(cd) == 2:
                        self.__results.append(cd[1](
                            getattr(parent, cdl[-1])))
                    elif len(cd) == 3:
                        self.__results.append(cd[1](
                            getattr(parent, cdl[-1]), cd[2]))
                    else:
                        self.__results.append(getattr(parent, cdl[-1]))
        self.closeDialog()

    def test_run(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        options = argparse.Namespace(
            mode='user',
            instance='test',
            tool=None,
            log='info'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()
        self.__dialog = dialog
        self.__results = []
        self.__commands = [
            ["_MainWindow__lavue._LiveViewer__sourcewg.isConnected()",
             None],
            ]
        QtCore.QTimer.singleShot(1000, self.executeAndClose)
        status = app.exec_()
        self.assertEqual(status, 0)
        self.assertEqual(self.__results[0], False)

    def test_start(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        options = argparse.Namespace(
            mode='user',
            instance='test',
            tool=None,
            start=True,
            source='test',
            log='info'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()
        self.__dialog = dialog
        self.__results = []
        self.__commands = [
            ["_MainWindow__lavue._LiveViewer__sourcewg.isConnected()",
             None],
            ["_MainWindow__lavue._LiveViewer__sourcewg"
             ".toggleServerConnection()",
             None],
            ["_MainWindow__lavue._LiveViewer__sourcewg.isConnected()",
             None],
            ["_MainWindow__lavue._LiveViewer__sourcewg"
             "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
             QtTest.QTest.mouseClick, QtCore.Qt.LeftButton],
            ["_MainWindow__lavue._LiveViewer__sourcewg.isConnected()",
             None],
            ["_MainWindow__lavue._LiveViewer__sourcewg"
             "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
             QtTest.QTest.mouseClick, QtCore.Qt.LeftButton],
            ["_MainWindow__lavue._LiveViewer__sourcewg.isConnected()",
             None],
            ]
        QtCore.QTimer.singleShot(1000, self.executeAndClose)
        status = app.exec_()
        self.assertEqual(status, 0)
        self.assertEqual(self.__results[0], True)
        self.assertEqual(self.__results[1], None)
        self.assertEqual(self.__results[2], False)
        self.assertEqual(self.__results[3], None)
        self.assertEqual(self.__results[4], True)
        self.assertEqual(self.__results[5], None)
        self.assertEqual(self.__results[6], False)


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()
