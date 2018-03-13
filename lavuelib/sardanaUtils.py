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
#     Christoph Rosemann <christoph.rosemann@desy.de>
#

""" sardana utils """

import pickle
import json
import time

try:
    import PyTango
    #: (:obj:`bool`) PyTango imported
    PYTANGO = True
except ImportError:
    #: (:obj:`bool`) PyTango imported
    PYTANGO = False


class SardanaUtils(object):

    """ sardanamacro server"""

    def __init__(self):
        """ constructor """
        #: (:class:`PyTango.Database`) tango database
        try:
            self.__db = PyTango.Database()
        except Exception as e:
            print(str(e))
            self.__db = None

    @classmethod
    def openProxy(cls, device, counter=1000):
        """ opens device proxy of the given device

        :param device: device name
        :type device: :obj:`str`
        :returns: DeviceProxy of device
        :rtype: :class:`PyTango.DeviceProxy`
        """
        found = False
        cnt = 0
        cnfServer = PyTango.DeviceProxy(str(device))

        while not found and cnt < counter:
            if cnt > 1:
                time.sleep(0.01)
            try:
                cnfServer.ping()
                found = True
            except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
                time.sleep(0.01)
                found = False
                if cnt == counter - 1:
                    raise
            cnt += 1

        return cnfServer

    def getMacroServer(self, door):
        """ door macro server device name

        :param door: door device name
        :type door: :obj:`str`
        :returns: macroserver device proxy
        :rtype: :class:`PyTango.DeviceProxy`
        """
        if not door:
            raise Exception("Door '%s' cannot be found" % door)
        sdoor = door.split("/")
        tangohost = None
        if len(sdoor) > 1 and ":" in sdoor[0]:
            door = "/".join(sdoor[1:])
            tangohost = sdoor[0]
        if tangohost or not self.__db:
            host, port = tangohost.split(":")
            db = PyTango.Database(host, int(port))
        else:
            db = self.__db

        servers = db.get_device_exported_for_class("MacroServer").value_string
        ms = None

        for server in servers:
            dp = None
            if tangohost and ":" not in server:
                msname = "%s/%s" % (tangohost, server)
            else:
                msname = str(server)
            try:
                dp = self.openProxy(msname)
            except Exception as e:
                print(str(e))
                dp = None
            if hasattr(dp, "DoorList"):
                lst = dp.DoorList
                if lst and (door in lst or
                            ("%s/%s" % (tangohost, door) in lst)):
                    ms = dp
                    break
        return ms

    def getScanEnv(self, door, params=None):
        """ fetches Scan Environment Data

        :param door: door device
        :type door: :obj:`str`
        :returns: JSON String with important variables
        :rtype: :obj:`str`
        """
        params = params or []
        res = {}
        msp = self.getMacroServer(door)
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                for var in params:
                    if var in dc['new'].keys():
                        res[var] = dc['new'][var]
        return json.dumps(res)

    def getDeviceName(self, cname, db=None):
        """ finds device of give class

        :param cname: device class name
        :type cname: :obj:`str`
        :param db: tango database
        :type db: :class:`PyTango.Database`
        :returns: device name if exists
        :rtype: :obj:`str`
        """

        if db is None:
            db = self.__db
        try:
            servers = db.get_device_exported_for_class(cname).value_string
        except:
            servers = []
        device = ''
        for server in servers:
            try:
                dp = self.openProxy(str(server))
                dp.ping()
                device = server
                break
            except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
                pass
        return device

    def setScanEnv(self, door, jdata):
        """ stores Scan Environment Data

        :param door: door device
        :type door: :obj:`str`
        :param jdata: JSON String with important variables
        :type jdata: :obj:`str`
        """
        data = json.loads(jdata)
        msp = self.getMacroServer(door)
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                for var in data.keys():
                    dc['new'][str(var)] = self.toString(data[var])
                pk = pickle.dumps(dc)
                msp.Environment = ['pickle', pk]

    def wait(self, name=None, proxy=None, maxcount=100):
        """ stores Scan Environment Data

        :param name: device name
        :type name: :obj:`str`
        :param proxy: door device proxy
        :type proxy: :obj:`str`
        :param maxcount: number of 0.01s to wait
        :type maxcount:  :obj:`int`
        """
        if proxy is None:
            proxy = self.openProxy(name)
        for _ in range(maxcount):
            if proxy.state() == PyTango.DevState.ON:
                break
            time.sleep(0.01)

    def runMacro(self, door, command, wait=True):
        """ stores Scan Environment Data

        :param door: door device
        :type door: :obj:`str`
        :param command: list with the macro name and its parameters
        :type command: :obj:`list` <:obj:`str`>
        :param wait: wait till macro is finished
        :type wait: :obj:`bool`
        """
        doorproxy = self.openProxy(door)
        msp = self.getMacroServer(door)
        ml = msp.MacroList
        if len(command) == 0:
            raise Exception("Macro %s not found" % str(command))
        elif not command[0]:
            raise Exception("Macro %s not found" % str(command))
        elif command[0] not in ml:
            raise Exception("Macro '%s' not found" % str(command[0]))
        state = str(doorproxy.state())
        if state != "ON":
            raise Exception("Door in state '%s'" % str(state))

        try:
            doorproxy.RunMacro(command)
        except PyTango.DevFailed as e:
            if e.args[0].reason == 'API_CommandNotAllowed':
                self.wait(proxy=doorproxy)
                doorproxy.RunMacro(command)
            else:
                raise
        if wait:
            self.wait(proxy=doorproxy)
            warn = doorproxy.warning
            res = doorproxy.result
            return res, warn
        else:
            return None, None

    @classmethod
    def toString(cls, obj):
        """ converts list/dict/object of unicode/string to string object

        :param obj: given unicode/string object
        :type obj: `any`
        :returns: string object
        :rtype: :obj:`str`
        """
        if isinstance(obj, unicode):
            return str(obj)
        elif isinstance(obj, list):
            return [cls.toString(el) for el in obj]
        elif isinstance(obj, dict):
            return dict([(cls.toString(key), cls.toString(value))
                         for key, value in obj.iteritems()])
        else:
            return obj
