# Copyright (C) 2017  Christoph Rosemann, DESY, Notkestr. 85, D-22607 Hamburg
# email contact: christoph.rosemann@desy.de
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


# first try for a live viewer image display
# base it on a qt dialog
# this is just the formal definition of the graphical elements !

from __future__ import print_function
from __future__ import unicode_literals

import sys
import math
import time
import socket
import numpy as np

from PyQt4 import QtCore, QtGui

from . import hidra_cbf_source as hcs
from . import GradientItem as GI

from . import gradientChoiceWidget
from . import hidraWidget
from . import imageDisplayWidget
from . import imageWidget
from . import intensityScalingWidget
from . import levelsWidget
from . import statisticsWidget
from . import transformationsWidget
from . import maskWidget
from . import bkgSubtractionWidget


import mystery

# magic numbers:
GLOBALREFRESHRATE = .1  # refresh rate if the data source is running in seconds


class HidraLiveViewer(QtGui.QDialog):
    '''The master class for the dialog, contains all other widget and handles communication.'''

    # subclass for data caching
    class exchangeList(list):
        def __init__(self,*args):
            list.__init__(self, *args)
            self.mute = False
            self.append(None)
            self.append(None)

        def addData(self, name, data):
            if self.mute is False:
                self.mute = True
                self[0] = name
                self[1] = data
                self.mute = False
            else:
                pass # print(" MUTED ACCESS IS NOT POSSIBLE")

        def readData(self):
            if self.mute is False:
                self.mute = True
                a, b = self[0], self[1]
                self.mute = False
                return a, b
            else:
               print(" MUTED ACCESS IS NOT POSSIBLE")

    # subclass for threading
    class dataFetchThread(QtCore.QThread):
        newDataName = QtCore.pyqtSignal(str)

        def __init__(self, datasource, alist):
            QtCore.QThread.__init__(self)
            self.data_source = datasource
            self._list = alist
            
        def run(self):
            while(True):
                time.sleep(GLOBALREFRESHRATE)
                img, name = self.data_source.getData()
                if name is not None:
                    self._list.addData(name, img)
                    self.newDataName.emit(name)

    def __init__(self, parent=None, signal_host=None, target=None):
        super(HidraLiveViewer, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # instantiate the data source
        # here: hardcoded the hidra cbf source!
        # future possibility: use abstract interface and factory for concrete instantiation

        # note: host and target are defined here and in another place
        self.data_source = hcs.HiDRA_cbf_source(
                                                mystery.signal_host,
                                                mystery.target,
                                                GLOBALREFRESHRATE*900)

        # WIDGET DEFINITIONS
        # instantiate the widgets and declare the parent
        self.hidraW = hidraWidget.HidraWidget(parent=self)
        self.maskW = maskWidget.MaskWidget(parent=self)
        self.bkgSubW = bkgSubtractionWidget.BkgSubtractionkWidget(parent=self)
        self.trafoW = transformationsWidget.TransformationsWidget(parent=self)
        self.scalingW = intensityScalingWidget.IntensityScalingWidget(parent=self)
        self.statsW = statisticsWidget.StatisticsWidget(parent=self)
        self.levelsW = levelsWidget.LevelsWidget(parent=self)
        self.gradientW = gradientChoiceWidget.GradientChoiceWidget(parent=self)
        self.imageW = imageWidget.ImageWidget(parent=self)

        # set the right names for the hidra display at initialization
        self.hidraW.setNames(self.data_source.getTargetSignalHost())

        # keep a reference to the "raw" image and the current filename
        self.raw_image = None
        self.image_name = None
        self.display_image = None
        
        # LAYOUT DEFINITIONS
        # the dialog layout is side by side
        globallayout = QtGui.QHBoxLayout()

        # define left hand side layout: vertical
        vlayout = QtGui.QVBoxLayout()

        # place widgets on the layouts
        # first the vertical layout on the left side
        
        # first element is supposed to be tabbed:
        vlayout.addWidget(self.hidraW)
        tabwidget = QtGui.QTabWidget()
        tabwidget.addTab(self.maskW, "Masking")
        tabwidget.addTab(self.bkgSubW, "Bkg Subtraction")
        
        vlayout.addWidget(tabwidget)
        vlayout.addWidget(self.trafoW)
        vlayout.addWidget(self.scalingW)
        vlayout.addWidget(self.statsW)
        vlayout.addWidget(self.levelsW)
        vlayout.addWidget(self.gradientW)

        # then the vertical layout on the --global-- horizontal one
        globallayout.addLayout(vlayout, 1)
        globallayout.addWidget(self.imageW, 10)

        self.setLayout(globallayout)
        self.setWindowTitle("laVue: Live Image Viewer")

        # SIGNAL LOGIC::
                
        # signals from transformation widget
        #~ self.trafoW.changeFlip.connect(print)
        #~ self.trafoW.changeMirror.connect(print)
        #~ self.trafoW.changeRotate.connect(print)

        # signal from intensity scaling widget:
        self.scalingW.changedScaling.connect(self.scale)
        self.scalingW.changedScaling.connect(self.plot)

        # signal from limit setting widget
        self.levelsW.changeMinLevel.connect(self.imageW.setMinLevel)
        self.levelsW.changeMaxLevel.connect(self.imageW.setMaxLevel)
        self.levelsW.autoLevels.connect(self.imageW.setAutoLevels)
        self.levelsW.levelsChanged.connect(self.plot)

        # connecting signals from hidra widget:
        self.hidraW.hidra_connect.connect(self.connect_hidra)
       # self.hidraW.hidra_connect.connect(self.dataFetcher.connect_hidra)
        self.hidraW.hidra_connect.connect(self.startPlotting)

        self.hidraW.hidra_disconnect.connect(self.stopPlotting)
        self.hidraW.hidra_disconnect.connect(self.disconnect_hidra)
        #self.hidraW.hidra_disconnect.connect(self.dataFetcher.disconnect_hidra)

        # gradient selector
        self.gradientW.chosenGradient.connect(self.imageW.changeGradient)

        # simple mutable caching object for data exchange with thread
        # [blocked state | image name | image data]
        # during read+write access state is set to blocked to avoid conflict
        self.exchangelist = self.exchangeList()
        
        self.dataFetcher = self.dataFetchThread(self.data_source, self.exchangelist)
        self.dataFetcher.newDataName.connect(self.getNewData)
        
        #~ self.bkgSubW.bkgFileSelection.connect(print)
        #~ self.maskW.maskFileSelection.connect(print)

    def plot(self):
        """ The main command of the live viewer class: draw a numpy array with the given name."""
        # use the internal raw image to create a display image with chosen scaling
        self.scale(self.scalingW.getCurrentScaling())

        # calculate the stats for this
        maxVal, meanVal, varVal, minVal = self.calcStats()

        # update the statistics display
        self.statsW.update_stats(meanVal, maxVal, varVal, self.scalingW.getCurrentScaling())

        # if needed, update the levels display
        if(self.levelsW.isAutoLevel()):
            self.levelsW.updateLevels(float(minVal), float(maxVal))

        # calls internally the plot function of the plot widget
        self.imageW.plot(self.display_image, self.image_name)

    # mode changer: start plotting mode
    def startPlotting(self):
        # only start plotting if the connection is really established
        if not self.hidraW.isConnected():
            return
        self.dataFetcher.start()

    # mode changer: stop plotting mode
    def stopPlotting(self):
        if self.dataFetcher is not None:
            pass
            #self.dataFetcher.quit()
            #~ self.dataFetcher.wait()

    # call the connect function of the hidra interface
    def connect_hidra(self):
        if self.data_source is None:
            print ("No data source is defined, this will result in trouble.")
            #self.data_source = hcs.HiDRA_cbf_source(mystery.signal_host, mystery.target)
        if not self.data_source.connect():
            self.hidraW.connectFailure()
            print(
                "<WARNING> The HiDRA connection could not be established. Check the settings.")
        else:
            self.hidraW.connectSuccess()

    # call the disconnect function of the hidra interface
    def disconnect_hidra(self):
        self.data_source.disconnect()
        #self.data_source = None

    def getNewData(self, name):
        # check if data is there at all
        if name is None:
            return
        # first time: 
        if self.image_name is None:
            self.image_name, self.raw_image = self.exchangelist.readData()
        # check if data is really new
        elif str(self.image_name) is not str(name):
            self.image_name, self.raw_image = self.exchangelist.readData()
        self.plot()

    def scale(self, scalingType):
        if(self.raw_image is None):
            return
        self.display_image = self.raw_image

        if scalingType == "sqrt":
            self.display_image = np.clip(self.raw_image, 0, np.inf)
            self.display_image = np.sqrt(self.display_image)
        elif scalingType == "log":
            self.display_image = np.clip(self.raw_image, 10e-3, np.inf)
            self.display_image = np.log10(self.display_image)

    def transform(self, trafoshort):
        '''Do the image transformation on the given numpy array.'''
        if(self.raw_image is None):
            return
        return
        #~ if self.rotate90.isChecked():
        #~ display_img = np.transpose(display_img)
        #~ if self.flip.isChecked():
        #~ display_img = np.flipud(display_img)
        #~ if self.mirror.isChecked():
        #~ display_img = np.fliplr(display_img)

    def calcStats(self):
        if self.display_image is not None:
            maxval = np.amax(self.display_image)
            meanval = np.mean(self.display_image)
            varval = np.var(self.display_image)
            # automatic maximum clipping to hardcoded value
            checkval = meanval + 10*np.sqrt(varval)
            if (maxval > checkval):
                maxval = checkval
            return (str("%.4f" % maxval),
                    str("%.4f" % meanval),
                    str("%.4f" % varval),
                    str("%.3f" % np.amin(self.display_image)))
        else:
            return "0.", "0.", "0.", "0."

    def getInitialLevels(self):
        if(self.raw_image is not None):
            return np.amin(self.raw_image), np.amax(self.raw_image)
