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
import os

qt_api = os.getenv("QT_API", os.getenv('DEFAULT_QT_API', 'pyqt5'))
if qt_api != 'pyqt4':
    try:
        from PyQt5 import QtGui
        from PyQt5 import QtCore
    except Exception:
        from PyQt4 import QtGui
        from PyQt4 import QtCore
else:
    from PyQt4 import QtGui
    from PyQt4 import QtCore


""" qt checker for testing gui """


class Check(object):
    """ abstract check class
    """

    def __init__(self, path):
        """ constructor

        :param path: check item path
        :type path: :obj:`str`
        """

        #: (:obj:`str`) checker path
        self._path = path
        spath = path.split(".")
        self._lpath = spath[:-1]
        self._item = spath[-1]

    def path(self):
        """ provides the widget path

        :returns: widget path
        :rtype: :obj:`str`
        """
        return self._path

    def execute(self, dialog):
        """ abstract execute

        :param dialog: qt dialog
        :type dialog: :obj:`any`
        """

    def _getparent(self, dialog):
        """ abstract execute

        :param dialog: qt dialog
        :type dialog: :obj:`any`
        """
        parent = dialog
        for itm in self._lpath:
            if "[]," in itm:
                sitm = itm.split(",")
                itm = sitm[0][:-2]
                try:
                    parent = getattr(parent, itm)[int(sitm[1])]
                except Exception:
                    parent = getattr(parent, itm)[sitm[1]]
            else:
                parent = getattr(parent, itm)
        return parent


class CmdCheck(Check):

    def __init__(self, path, params=None):
        Check.__init__(self, path)
        """ constructor

        :param path: check item path
        :type path: :obj:`str`
        :param params: a list of wrapper parameters
        :type params: :obj:`dict` <:obj:`str`, :obj:`any`>
        """
        self._params = params

    def execute(self, dialog):
        """ execute command

        :param dialog: qt dialog
        :type dialog: :obj:`any`
        """
        parent = self._getparent(dialog)
        cmd = getattr(parent, self._item)
        if self._params:
            return cmd(**self._params)
        else:
            return cmd()


class AttrCheck(Check):

    def __init__(self, path):
        Check.__init__(self, path)
        """ constructor

        :param path: check item path
        :type path: :obj:`str`
        """

    def execute(self, dialog):
        """ execute command

        :param dialog: qt dialog
        :type dialog: :obj:`any`
        """
        parent = self._getparent(dialog)
        return getattr(parent, self._item)


class WrapAttrCheck(AttrCheck):

    def __init__(self, path, wcmd, wparams=None, wpos=0):
        AttrCheck.__init__(self, path)
        """ constructor

        :param path: check item path
        :type path: :obj:`str`
        :param wcmd: wcmd command
        :type wcmd: :obj:`func`
        :param wparams: a list of wrapper parameters
        :type wparams: :obj:`list`
        :param wpos: position of wrapping object
        :type wpos: :obj:`int`

        """
        self._wcmd = wcmd
        self._wparams = wparams
        self._wpos = wpos

    def execute(self, dialog):
        """ execute command

        :param dialog: qt dialog
        :type dialog: :obj:`any`
        """
        attr = AttrCheck.execute(self, dialog)
        if not self._wparams:
            wp = [attr]
        else:
            wp = list(self._wparams)
            wp.insert(self._wpos, attr)
        return self._wcmd(*wp)


class QtChecker(object):

    def __init__(self, app=None, dialog=None, verbose=False,
                 qtgui=None, qtcore=None):
        """ constructor

        :param app:  application object
        :type app: :class:`PyQt5.QtGui.QApplication`
        :param dialog: qt dialog
        :type dialog: :obj:`any`
        :param verbose: verbose flag
        :type verbose: :obj:`bool`
        """
        self.QtGui = qtgui or QtGui
        self.QtCore = qtcore or QtCore
        self.__app = app
        if app is None:
            self.__app = self.QtGui.QApplication([])

        self.__dialog = dialog
        self.__checks = []
        self.__results = []
        self.__verbose = verbose

    def setDialog(self, dialog):
        """ sets dialog

        :param dialog: qt dialog
        :type dialog: :obj:`any`
        """
        self.__dialog = dialog

    def setChecks(self, checks):
        """ sets check items

        :param checks: a list of Check items
        :type checks: :obj:`list` <:class:`Check`>
        """
        self.__checks = checks

    def results(self):
        """ provides a list of result objects

        :returns: a list of result objects
        :rtype: :obj:`list` <:class:`any`>
        """
        return self.__results

    def executeChecksAndClose(self, delay=1000):
        """ executes check items and close the dialog in a separate thread

        :param delay: delay time in ms
        :type delay: :obj:`int`
        """
        self.__results = []
        self.QtCore.QTimer.singleShot(1000, self._executeChecksAndClose)
        status = self.__app.exec_()
        if self.__verbose:
            print("Status %s" % status)
        return status

    def executeChecks(self, delay=1000):
        """ executes check items

        :param delay: delay time in ms in a separate thread
        :type delay: :obj:`int`
        """
        self.__results = []
        self.QtCore.QTimer.singleShot(1000, self._executeChecks)
        status = self.__app.exec_()
        if self.__verbose:
            print("Status %s" % status)
        return status

    def _executeChecksAndClose(self):
        """ executes check items and close the dialog
        """
        self._executeChecks()
        if self.__dialog:
            self.__dialog.close()
            if self.__verbose:
                print("Close Dialog")
            self.__dialog = None

    def _executeChecks(self):
        """ executes check items
        """
        for i, ch in enumerate(self.__checks):
            if self.__verbose:
                print("Execute %s: %s" % (i, ch.path()))
            self.__results.append(ch.execute(self.__dialog))

    def compareResults(self, testcase, results):
        """ compare results with use of testcase.assertEqual

        :param testcase: test case object
        :type testcase: :class:`unittest.TestCase`
        :param results: a list of template result objects
        :type results: :obj:`list` <:class:`any`>
        """
        testcase.assertEqual(len(self.__results), len(results))
        for i, rs in enumerate(self.__results):
            if self.__verbose and rs != results[i]:
                print("Difference at %s: %s <> %s" % (i, rs, results[i]))
            testcase.assertEqual(rs, results[i])
