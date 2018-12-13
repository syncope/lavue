#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of the LavueController project
#
# GPL 2
#
# Distributed under the terms of the GPL license.
# See LICENSE.txt for more info.
"""Contain the tests for the Lavue Controller."""

# Path
import sys
import os
import subprocess
import numpy as np
import time
import unittest
import PyTango

# Path
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(path))

#: python3 running
PY3 = (sys.version_info > (3,))


# Device test case
class LavueControllerTest(unittest.TestCase):
    """Test case for packet generation."""

    def __init__(self, methodName):
        """ constructor

        :param methodName: name of the test method
        """
        unittest.TestCase.__init__(self, methodName)
        self.instance = 'TEST'
        self.device = 'test/lavuecontroller/00'
        self.new_device_info_controller = PyTango.DbDevInfo()
        self.new_device_info_controller._class = "LavueController"
        self.new_device_info_controller.server = "LavueController/%s" % \
                                                self.instance
        self.new_device_info_controller.name = self.device
        self.proxy = None

        if PY3:
            if os.path.isfile("../LavueController"):
                self._startserver = \
                    "cd ..; python3 ./LavueController %s &" % self.instance
            else:
                self._startserver = \
                    "python3 LavueController %s &" % self.instance
        else:
            if os.path.isfile("../LavueController"):
                self._startserver = \
                    "cd ..; python2 ./LavueController %s &" % self.instance
            else:
                self._startserver = \
                    "python2 LavueController %s &" % self.instance
        self._grepserver = \
            "ps -ef | grep 'LavueController %s' | grep -v grep" % \
            self.instance

    def setUp(self):
        print("\nsetting up ...")
        db = PyTango.Database()
        db.add_device(self.new_device_info_controller)
        db.add_server(
            self.new_device_info_controller.server,
            self.new_device_info_controller)
        self._psub = subprocess.call(
            self._startserver,
            stdout=None,
            stderr=None, shell=True)
        sys.stdout.write("waiting for server ")

        found = False
        cnt = 0
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                dp = PyTango.DeviceProxy(self.new_device_info_controller.name)
                time.sleep(0.1)
                if dp.state() == PyTango.DevState.ON:
                    found = True
            except Exception:
                found = False
            cnt += 1
        print("")
        self.proxy = dp

    def tearDown(self):
        print("tearing down ...")
        db = PyTango.Database()
        db.delete_server(self.new_device_info_controller.server)

        if PY3:
            with subprocess.Popen(self._grepserver,
                                  stdout=subprocess.PIPE,
                                  shell=True) as proc:
                try:
                    outs, errs = proc.communicate(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    outs, errs = proc.communicate()
                res = str(outs, "utf8").split("\n")
                for r in res:
                    sr = r.split()
                    if len(sr) > 2:
                        subprocess.call(
                            "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                            shell=True)
        else:
            pipe = subprocess.Popen(self._grepserver,
                                    stdout=subprocess.PIPE,
                                    shell=True).stdout

            res = str(pipe.read()).split("\n")
            for r in res:
                sr = r.split()
                if len(sr) > 2:
                    subprocess.call(
                        "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                        shell=True)
            pipe.close()

        self.proxy = None

    def test_properties(self):
        # test the properties
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))

    def test_State(self):
        """Test for State"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))

    def test_Status(self):
        """Test for Status"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))

    def test_BeamCenterX(self):
        """Test for BeamCenterX"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))

    def test_BeamCenterY(self):
        """Test for BeamCenterY"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))

    def test_DetectorDistance(self):
        """Test for DetectorDistance"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))

    def test_DetectorROIs(self):
        """Test for DetectorROIs"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))

    def test_DetectorROIsValues(self):
        """Test for DetectorROIsValues"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))

    def test_Energy(self):
        """Test for Energy"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))


def main():
    """ main function"""
    unittest.main()


# Main execution
if __name__ == "__main__":
    main()
