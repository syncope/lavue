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
import time
import socket
import numpy as np

from PyQt4 import QtCore, QtGui

from . import hidra_cbf_source as hcs
from . import GradientItem as GI

from . import gradientChoiceWidget
from . import hidraWidget
from . import imageWidget
from . import intensityScalingWidget
from . import levelsWidget
from . import statisticsWidget
from . import preparationBoxWidget
from . import imageFileHandler
try:
    from hidraServerList import HidraServerList
except:
    print("Cannot read the list of HiDRA servers.")
    print("Alternate method not yet implemented.")

# magic numbers:
GLOBALREFRESHRATE = .1  # refresh rate if the data source is running in seconds


class HidraLiveViewer(QtGui.QDialog):
    '''The master class for the dialog, contains all other widget and handles communication.'''
    update_state = QtCore.pyqtSignal(int)

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
               print("MUTED ACCESS IS NOT POSSIBLE")

    # subclass for threading
    class dataFetchThread(QtCore.QThread):
        newDataName = QtCore.pyqtSignal(str)

        def __init__(self, datasource, alist):
            QtCore.QThread.__init__(self)
            self.data_source = datasource
            self._list = alist
            self._isConnected = False
            
        def run(self):
            while(True):    
                time.sleep(GLOBALREFRESHRATE)
                if(self._isConnected):
                     img, name = self.data_source.getData()
                     if name is not None:
                        self._list.addData(name, img)
                        self.newDataName.emit(name)
                else:
                    pass

        def changeStatus(self, status):
            self._isConnected = status


    def __init__(self, parent=None, signal_host=None, target=None):
        super(HidraLiveViewer, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.sourcetypes = [
            {"name": "Hidra",
             "datasource":"HiDRA_cbf_source",
             "slot": "updateHidraButton",
             "hidden": ["attrLabel", "attrLineEdit"]},
            {"name": "Tango",
             "datasource":"TangoAttrSource",
             "slot": "updateAttrButton",
             "hidden": ["hostlabel", "currenthost",
                        "serverLabel", "serverlistBox"]},
            {"name": "Test",
             "datasource":"GeneralSource",
             "slot": "updateButton",
             "hidden": ["hostlabel", "currenthost",
                        "serverLabel", "serverlistBox",
                        "attrLabel", "attrLineEdit"]},
        ]    
    

        # instantiate the data source
        # here: hardcoded the hidra cbf source!
        # future possibility: use abstract interface and factory for concrete instantiation

        # note: host and target are defined in another place
        # self.data_source = hcs.HiDRA_cbf_source()
        self.data_source = hcs.GeneralSource()

        # WIDGET DEFINITIONS
        # instantiate the widgets and declare the parent
        self.hidraW = hidraWidget.HidraWidget(
            parent=self, serverdict=HidraServerList)
        self.prepBoxW = preparationBoxWidget.PreparationBoxWidget(parent=self)
        self.scalingW = intensityScalingWidget.IntensityScalingWidget(parent=self)
        self.levelsW = levelsWidget.LevelsWidget(parent=self)
        self.gradientW = gradientChoiceWidget.GradientChoiceWidget(parent=self)
        self.statsW = statisticsWidget.StatisticsWidget(parent=self)
        self.imageW = imageWidget.ImageWidget(parent=self)

        
        #~ self.maskW = self.prepBoxW.maskW
        self.bkgSubW = self.prepBoxW.bkgSubW
        self.trafoW = self.prepBoxW.trafoW

        # keep a reference to the "raw" image and the current filename
        self.raw_image = None
        self.image_name = None
        self.display_image = None

        self.background_image = None
        self.doBkgSubtraction = False
        
        self.mask_image = None
        self.maskIndices = None
        self.applyImageMask = False

        self._signalhost = None

        self.trafoName = "None"
        
        # LAYOUT DEFINITIONS
        # the dialog layout is side by side
        globallayout = QtGui.QHBoxLayout()

        # define left hand side layout: vertical
        vlayout = QtGui.QVBoxLayout()

        # place widgets on the layouts
        # first the vertical layout on the left side
        
        # first element is supposed to be tabbed:
        vlayout.addWidget(self.hidraW)
        vlayout.addWidget(self.prepBoxW)
        vlayout.addWidget(self.scalingW)
        vlayout.addWidget(self.levelsW)
        vlayout.addWidget(self.gradientW)
        vlayout.addWidget(self.statsW)

        # then the vertical layout on the --global-- horizontal one
        globallayout.addLayout(vlayout, 1)
        globallayout.addWidget(self.imageW, 10)

        self.setLayout(globallayout)
        self.setWindowTitle("laVue: Live Image Viewer")

        # SIGNAL LOGIC::

        # signal from intensity scaling widget:
        self.scalingW.changedScaling.connect(self.scale)
        self.scalingW.changedScaling.connect(self.plot)
        self.scalingW.changedScaling.connect(self.levelsW.setScalingLabel)

        # signal from limit setting widget
        self.levelsW.changeMinLevel.connect(self.imageW.setMinLevel)
        self.levelsW.changeMaxLevel.connect(self.imageW.setMaxLevel)
        self.levelsW.autoLevels.connect(self.imageW.setAutoLevels)
        self.levelsW.levelsChanged.connect(self.plot)

        # connecting signals from hidra widget:
        self.hidraW.hidra_connect.connect(self.connect_hidra)
        self.hidraW.hidra_connect.connect(self.startPlotting)

        self.hidraW.hidra_disconnect.connect(self.stopPlotting)
        self.hidraW.hidra_disconnect.connect(self.disconnect_hidra)

        # gradient selector
        self.gradientW.chosenGradient.connect(self.imageW.changeGradient)

        # simple mutable caching object for data exchange with thread
        # [blocked state | image name | image data]
        # during read+write access state is set to blocked to avoid conflict
        self.exchangelist = self.exchangeList()
        
        self.dataFetcher = self.dataFetchThread(self.data_source, self.exchangelist)
        self.dataFetcher.newDataName.connect(self.getNewData)
        # ugly !!! sent current state to the data fetcher...
        self.update_state.connect(self.dataFetcher.changeStatus)
        self.hidraW.hidra_state.connect(self.updateSource)
        
        self.bkgSubW.bkgFileSelection.connect(self.prepareBKGSubtraction)
        self.bkgSubW.useCurrentImageAsBKG.connect(self.setCurrentImageAsBKG)
        self.bkgSubW.applyBkgSubtractBox.stateChanged.connect(self.checkBKGSubtraction)
        #~ self.maskW.maskFileSelection.connect(self.prepareMasking)
        #~ self.maskW.applyMaskBox.stateChanged.connect(self.checkMasking)

        # signals from transformation widget
        self.trafoW.activatedTransformation.connect(self.assessTransformation)

        # set the right target name for the hidra display at initialization
        self.hidraW.setTargetName(self.data_source.getTarget())
        # self.hidraW.hidra_servername.connect(self.data_source.setSignalHost)
        self.hidraW.hidra_servername.connect(self.setSignalHost)

    def setSignalHost(self, signalhost):
        self._signalhost = signalhost
        
    def updateSource(self, status):
        print("STATUS %s" % status)
        if status:
            self.data_source = getattr(hcs,self.sourcetypes[status - 1]["datasource"])()
            self.dataFetcher.data_source = self.data_source
            if self._signalhost:
                self.data_source.setSignalHost(self._signalhost)
                print ("SH %s" % self._signalhost)
        self.update_state.emit(status)    
        
        
    def plot(self):
        """ The main command of the live viewer class: draw a numpy array with the given name."""
        # prepare or preprocess the raw image if present:
        self.prepareImage()
        
        # perform transformation 
        self.transform()
        
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

    def prepareImage(self):
        if(self.raw_image is None):
            return
        self.display_image = self.raw_image
        
        if self.doBkgSubtraction and self.background_image is not None:
            # simple subtraction
            self.display_image = self.raw_image - self.background_image
        #~ if self.applyImageMask and self.maskIndices is not None:
            #~ # set all masked (non-zero values) to zero by index
            #~ self.display_image[self.maskIndices] = 0
            
    def scale(self, scalingType):
        if(self.display_image is None):
            return
        if scalingType == "sqrt":
            self.display_image = np.clip(self.display_image, 0, np.inf)
            self.display_image = np.sqrt(self.display_image)
        elif scalingType == "log":
            self.display_image = np.clip(self.display_image, 10e-3, np.inf)
            self.display_image = np.log10(self.display_image)

    def transform(self):
        '''Do the image transformation on the given numpy array.'''
        if self.display_image is None or self.trafoName is "None":
            return
        # !!! there is a place, where indices go to die...
        # somewhere, the ordering of the indices gets messed up
        # to rectify the situation and not mislead users, 
        # make the transformation, so that at least the name fits
        elif self.trafoName == "flipud":
            self.display_image = np.fliplr(self.display_image)
        elif self.trafoName == "rotate90":
            self.display_image = np.rot90(self.display_image)
        elif self.trafoName == "mirror":
            self.display_image = np.flipud(self.display_image)
    
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
        if(self.display_image is not None):
            return np.amin(self.display_image), np.amax(self.display_image)

    def checkMasking(self, state):
        self.applyImageMask = state
        if self.applyImageMask and self.mask_image is None:
            self.maskW.noImage()

    #~ def prepareMasking(self, imagename):
        #~ '''Get the mask image, select non-zero elements and store the indices.'''
        #~ self.mask_image = imageFileHandler.ImageFileHandler(str(imagename)).getImage()
        #~ self.maskIndices = np.nonzero(self.mask_image !=0)

    def checkBKGSubtraction(self, state):
        self.doBkgSubtraction = state
        if self.doBkgSubtraction and self.background_image is None:
            self.bkgSubW.setDisplayedName("")

    def prepareBKGSubtraction(self, imagename):
        self.background_image = imageFileHandler.ImageFileHandler(str(imagename)).getImage()

    def setCurrentImageAsBKG(self):
        if self.raw_image is not None:
            self.background_image = self.raw_image
            self.bkgSubW.setDisplayedName(str(self.image_name))
        else:
            self.bkgSubW.setDisplayedName("")

    def assessTransformation(self, trafoName):
        self.trafoName = trafoName
