# author: Ch. Rosemann, DESY
# email: christoph.rosemann@desy.de


# first try for a live viewer image display
# base it on a qt dialog
# this is just the formal definition of the graphical elements !

from __future__ import print_function
from __future__ import unicode_literals

import sys
import math
import socket
import pyqtgraph as pg
import numpy as np

from PyQt4 import QtCore, QtGui

import hidra_cbf_source as hcs
import GradientItem as GI
import mystery


class HidraLiveViewer(QtGui.QDialog):
    '''The master class for the dialog, contains all other widget and handles communication.'''
    
    def __init__(self, parent=None, signal_host=None, target=None):
        super(HidraLiveViewer, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # instantiate the data source
        # here: hardcoded the hidra cbf source!
        # future possibility: use abstract interface and factory for concrete instantiation

        # note: host and target are defined here and in another place
        self.data_source = hcs.HiDRA_cbf_source(
                                mystery.signal_host, mystery.target)
        # time in [ms] between calls to hidra
        self.waittime = 500

        # WIDGET DEFINITIONS
        # instantiate the widgets and declare the parent
        self.hidraW = hidra_widget(parent=self)
        self.trafoW = imagetransformations_widget(parent=self)
        self.scalingW = intensityscaling_widget(parent=self)
        self.statsW = statistics_widget(parent=self)
        self.levelsW = levels_widget(parent=self)
        self.gradientW = gradientChooser_widget(parent=self)
        self.imageW = image_widget(parent=self)

        # set the right names for the hidra display at initialization
        self.hidraW.setNames(self.data_source.getTargetSignalHost())

        # keep a reference to the "raw" image and the current filename
        self.raw_image = None
        self.image_name = None
        self.display_image = None
        #~ self.plotLevels = [.1,1.]
        #~ self.initialPlotLevelsSet = False
        
        # LAYOUT DEFINITIONS
        # the dialog layout is side by side
        globallayout = QtGui.QHBoxLayout()

        # define left hand side layout: vertical
        vlayout = QtGui.QVBoxLayout()

        # place widgets on the layouts
        # first the vertical layout on the left side
        vlayout.addWidget(self.hidraW)
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
        self.hidraW.hidra_connect.connect(self.startPlotting)

        self.hidraW.hidra_disconnect.connect(self.stopPlotting)
        self.hidraW.hidra_disconnect.connect(self.disconnect_hidra)

        # gradient selector
        self.gradientW.chosenGradient.connect(self.imageW.changeGradient)

        # timer logic for hidra
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.waittime)
        
        self.timer.timeout.connect(self.getNewData)
        self.timer.timeout.connect(self.plot)


    def plot(self):
        """ The main command of the live viewer class: draw a numpy array with the given name."""
        # use the internal raw image to create a display image with chosen scaling
        self.scale(self.scalingW.getCurrentScaling())

        # calculate the stats for this
        maxVal, meanVal, varVal, minVal =  self.calcStats()

        # update the statistics display
        self.statsW.update_stats(maxVal, meanVal, varVal, self.scalingW.getCurrentScaling())

        # if needed, update the levels display
        if(self.levelsW.isAutoLevel()):
            self.levelsW.updateLevels(float(minVal), float(maxVal))

        # calls internally the plot function of the plot widget
        self.imageW.plot(self.display_image, self.image_name)

    def plot2(self, img, name):
        """Convenience function for testing, uses given image and name for display."""
        self.image_name = name
        self.raw_image = img
        self.plot()

    # mode changer: start plotting mode
    def startPlotting(self):
        # only start plotting if the connection is really established
        if not self.hidraW.isConnected():
            return
        self.timer.start()

    # mode changer: stop plotting mode
    def stopPlotting(self):
        self.timer.stop()

    # call the connect function of the hidra interface
    def connect_hidra(self):
        if not self.data_source.connect():
            self.hidraW.connectFailure()
            print(
                "<WARNING> The HiDRA connection could not be established. Check the settings.")
        else:
            self.hidraW.connectSuccess()

    # call the disconnect function of the hidra interface
    def disconnect_hidra(self):
        self.data_source.disconnect()

    def getNewData(self):
        self.raw_image, self.image_name = self.data_source.getData()
        # the internal data object is copied to allow for internal conversions
        self.display_image = self.raw_image

    def scale(self, scalingType):
        if( self.raw_image is None):
            print("No image is loaded, continuing.")
            return
        self.display_image = self.raw_image

        if scalingType == "sqrt":
            np.clip(self.display_image, 0, np.inf)
            self.display_image = np.sqrt(self.display_image)
        elif scalingType == "log":
            np.clip(self.display_image, 10e-3, np.inf)
            self.display_image = np.log10(self.display_image)

    def transform(self, trafoshort):
        '''Do the image transformation on the given numpy array.'''
        return
        #~ if self.rotate90.isChecked():
            #~ display_img = np.transpose(display_img)
        #~ if self.flip.isChecked():
            #~ display_img = np.flipud(display_img)
        #~ if self.mirror.isChecked():
            #~ display_img = np.fliplr(display_img)

    def calcStats(self):
        if self.display_image is not None:
            return (str("%.4f" % np.amax(self.display_image)),
                    str("%.4f" % np.mean(self.display_image)),
                    str("%.4f" % np.var(self.display_image)) ,
                    str("%.3f" % np.amin(self.display_image)))
        else:
            return  "0.",  "0.",  "0.",  "0." 

    def getInitialLevels(self):
        if(self.raw_image != None):
            return  np.amin(self.raw_image), np.amax(self.raw_image)


class hidra_widget(QtGui.QGroupBox):

    """
    Connect and disconnect hidra service.
    """
    hidra_disconnect = QtCore.pyqtSignal()
    hidra_connect = QtCore.pyqtSignal()

    def __init__(self, parent=None, signal_host=None, target=None):
        super(hidra_widget, self).__init__(parent)
        self.setTitle("HiDRA connection")

        self.signal_host = signal_host
        self.target = target
        self.connected = False

        gridlayout = QtGui.QGridLayout()

        self.serverLabel = QtGui.QLabel(u"Server")
        self.serverName = QtGui.QLabel(u"SomeName")
        self.hostlabel = QtGui.QLabel("Client")
        self.currenthost = QtGui.QLabel("None")
        self.cStatusLabel = QtGui.QLabel("Status: ")
        self.cStatus = QtGui.QLineEdit("Not connected")
        self.cStatus.setStyleSheet("color: blue;"
                                   "background-color: yellow;")
        self.button = QtGui.QPushButton("Connect")

        self.button.clicked.connect(self.toggleServerConnection)

        gridlayout.addWidget(self.serverLabel, 0, 0)
        gridlayout.addWidget(self.serverName, 0, 1)
        gridlayout.addWidget(self.hostlabel, 1, 0)
        gridlayout.addWidget(self.currenthost, 1, 1)
        gridlayout.addWidget(self.cStatusLabel, 2, 0)
        gridlayout.addWidget(self.cStatus, 2, 1)
        gridlayout.addWidget(self.button, 3, 1)

        self.setLayout(gridlayout)

    def setNames(self, names):
        self.currenthost.setText(str(names[0]))
        self.serverName.setText(str(names[1]))

    def isConnected(self):
        return self.connected

    def toggleServerConnection(self):
        # if it is connected then it's easy:
        if self.connected:
            self.hidra_disconnect.emit()
            self.cStatus.setStyleSheet("color: yellow;"
                                   "background-color: red;")
            self.cStatus.setText("Disconnected")
            self.button.setText("Re-Connect")
            self.connected = False
            return

        if not self.connected:
            self.hidra_connect.emit()

    def connectSuccess(self):
        """ Function doc """
        self.connected = True
        self.cStatus.setStyleSheet("color: white;"
                                   "background-color: green;")
        self.cStatus.setText("Connected")
        self.button.setText("Disconnect")

    def connectFailure(self):
        """ Function doc """
        self.connected = False
        self.cStatus.setText("Trouble connecting")
        self.button.setText("Retry connect")


class intensityscaling_widget(QtGui.QGroupBox):

    """
    Select how the image intensity is supposed to be scaled.
    """
    changedScaling = QtCore.pyqtSignal(QtCore.QString)

    def __init__(self, parent=None):
        super(intensityscaling_widget, self).__init__(parent)

        self.setTitle("Intensity display scaling")
        self.current = "sqrt"
        horizontallayout = QtGui.QHBoxLayout()

        self.sqrtbutton = QtGui.QRadioButton(u"sqrt")
        self.linbutton = QtGui.QRadioButton(u"linear")
        self.logbutton = QtGui.QRadioButton(u"log")

        self.linbutton.toggled.connect(self.setCurrentScaling)
        self.logbutton.toggled.connect(self.setCurrentScaling)
        self.sqrtbutton.toggled.connect(self.setCurrentScaling)
        self.sqrtbutton.setChecked(True)

        horizontallayout.addWidget(self.sqrtbutton)
        horizontallayout.addWidget(self.linbutton)
        horizontallayout.addWidget(self.logbutton)

        self.setLayout(horizontallayout)

    def getCurrentScaling(self):
        return self.current

    def setCurrentScaling(self, scaling):
        if self.linbutton.isChecked():
            self.current = "lin"
        elif self.logbutton.isChecked():
            self.current = "log"
        else:
            self.current = "sqrt"
        self.changedScaling.emit(self.current)


class levels_widget(QtGui.QGroupBox):

    """
    Set minimum and maximum displayed values.
    """

    changeMinLevel = QtCore.pyqtSignal(float)
    changeMaxLevel = QtCore.pyqtSignal(float)
    autoLevels = QtCore.pyqtSignal(int) # bool does not work...
    levelsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(levels_widget, self).__init__(parent)

        self.setTitle("Set display levels")

        # keep internal var for auto levelling toggle
        self.auto = True
        
        self.autoLevelBox = QtGui.QCheckBox(u"Automatic levels")
        self.autoLevelBox.setChecked(True)
       
        #~ informLabel = QtGui.QLabel("Linear scale, affects only display!")
        minLabel = QtGui.QLabel("minimum value: ")
        maxLabel = QtGui.QLabel("maximum value: ")

        self.minVal = 0.1
        self.maxVal = 1.

        self.minValSB = QtGui.QDoubleSpinBox()
        self.minValSB.setMinimum(0.)
        self.maxValSB = QtGui.QDoubleSpinBox()
        self.maxValSB.setMinimum(1.)
        self.maxValSB.setMaximum(10e20)
        self.applyButton = QtGui.QPushButton("Apply levels")

        layout = QtGui.QGridLayout()
        #~ layout.addWidget(informLabel, 0, 0)
        layout.addWidget(self.autoLevelBox, 0,1)
        layout.addWidget(minLabel, 1, 0)
        layout.addWidget(self.minValSB, 1, 1)
        layout.addWidget(maxLabel, 2, 0)
        layout.addWidget(self.maxValSB, 2, 1)
        layout.addWidget(self.applyButton, 3, 1)

        self.setLayout(layout)
        self.applyButton.clicked.connect(self.check_and_emit)
        self.autoLevelBox.stateChanged.connect(self.autoLevelChange)

        self.updateLevels(self.minVal, self.maxVal)

    def isAutoLevel(self):
        return self.auto

    def autoLevelChange(self, value):
        if( value is 2):
            self.auto = True
            self.autoLevels.emit(1)
        else:
            self.auto = False
            self.autoLevels.emit(0)
            self.check_and_emit()
        self.levelsChanged.emit()

    def check_and_emit(self):
        # check if the minimum value is actually smaller than the maximum
        self.minVal = self.minValSB.value()
        self.maxVal = self.maxValSB.value()
        if (self.maxVal - self.minVal) <= 0:
            if(self.minVal >= 1.):
                self.minVal = self.maxVal - 1.
            else:
                self.maxVal = self.minVal + 1
            
        self.minValSB.setValue(self.minVal)
        self.maxValSB.setValue(self.maxVal)
        
        self.changeMinLevel.emit(self.minVal)
        self.changeMaxLevel.emit(self.maxVal)
        self.levelsChanged.emit()

    def updateLevels(self, lowlim, uplim):
        self.minValSB.setValue(lowlim)
        self.maxValSB.setValue(uplim)


class statistics_widget(QtGui.QGroupBox):

    """
    Display some general image statistics.
    """

    def __init__(self, parent=None):
        super(statistics_widget, self).__init__(parent)

        self.setTitle("Image statistics")
        layout = QtGui.QGridLayout()

        self.scaling = "sqrt"

        scalingLabel = QtGui.QLabel("Scaling:")
        self.scaleLabel = QtGui.QLabel(self.scaling)

        maxlabel = QtGui.QLabel("maximum: ")
        meanlabel = QtGui.QLabel("mean: ")
        variancelabel = QtGui.QLabel("variance: ")

        self.maxVal = QtGui.QLineEdit("Not set")
        self.meanVal = QtGui.QLineEdit("Not set")
        self.varVal = QtGui.QLineEdit("Not set")
        layout.addWidget(scalingLabel, 0, 0)
        layout.addWidget(self.scaleLabel, 0, 1)

        layout.addWidget(maxlabel, 1, 0)
        layout.addWidget(self.maxVal, 1, 1)
        layout.addWidget(meanlabel, 2, 0)
        layout.addWidget(self.meanVal, 2, 1)
        layout.addWidget(variancelabel, 3, 0)
        layout.addWidget(self.varVal, 3, 1)

        self.setLayout(layout)

    def update_stats(self, meanVal, maxVal, varVal, scaling):
        if self.scaling is not scaling:
            self.scaling = scaling
        self.scaleLabel.setText(self.scaling)
        self.maxVal.setText(maxVal)
        self.meanVal.setText(meanVal)
        self.varVal.setText(varVal)


class imagetransformations_widget(QtGui.QGroupBox):
    # still pending implemntation -> needs scipy, probably
    """
    Select how an image should be transformed.
    """
    changeFlip = QtCore.pyqtSignal(int)
    changeMirror = QtCore.pyqtSignal(int)
    changeRotate = QtCore.pyqtSignal(int)


    def __init__(self, parent=None):
        super(imagetransformations_widget, self).__init__(parent)

        self.setTitle("Image transformations")
        
        layout = QtGui.QHBoxLayout()
        self.cb = QtGui.QComboBox()        
        self.cb.addItem("None")
        self.cb.addItem("flip")
        self.cb.addItem("mirror")
        self.cb.addItem("rotate")
        #~ layout.addStretch(1)
        layout.addWidget(self.cb)
        self.setLayout(layout)
        
        #~ horizontallayout.addWidget(self.flip)
        #~ horizontallayout.addWidget(self.mirror)
        #~ horizontallayout.addWidget(self.rotate90)
        #~ 
        #~ self.setLayout(horizontallayout)
        #~ 
        #~ # signals:
        #~ self.flip.stateChanged.connect(self.changeFlip.emit)
        #~ self.mirror.stateChanged.connect(self.changeMirror.emit)
        #~ self.rotate90.stateChanged.connect(self.changeRotate.emit)
#~ 

class gradientChooser_widget(QtGui.QGroupBox):
    # still pending implemntation -> needs scipy, probably
    """
    Select how an image should be transformed.
    """
    
    chosenGradient = QtCore.pyqtSignal(QtCore.QString)

    def __init__(self, parent=None):
        super(gradientChooser_widget, self).__init__(parent)

        self.setTitle("Gradient choice")
        
        layout = QtGui.QHBoxLayout()
        self.cb = QtGui.QComboBox()        
        self.cb.addItem("inverted")
        self.cb.addItem("highContrast")
        self.cb.addItem("thermal")
        self.cb.addItem("flame")
        self.cb.addItem("bipolar")
        self.cb.addItem("spectrum")
        self.cb.addItem("greyclip")
        self.cb.addItem("grey")
        layout.addWidget(self.cb)
        self.setLayout(layout)
        self.cb.activated.connect(self.emitText)
        
    def emitText(self, index):
        self.chosenGradient.emit(self.cb.itemText(index))


class image_widget(QtGui.QWidget):

    """
    The part of the GUI that incorporates the image view.
    """

     #~ = QtCore.pyqtSignal(bool)
    #~ initialLevels = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        super(image_widget, self).__init__(parent)

        self.nparray = None
        self.imageItem = None

        self.img_widget = ImageDisplay(parent=self)

        verticallayout = QtGui.QVBoxLayout()

        filenamelayout = QtGui.QHBoxLayout()

        filelabel = QtGui.QLabel("Image/File name: ")
        filenamelayout.addWidget(filelabel)
        self.filenamedisplay = QtGui.QLineEdit()
        filenamelayout.addWidget(self.filenamedisplay)

        verticallayout.addLayout(filenamelayout)
        verticallayout.addWidget(self.img_widget)

        pixelvaluelayout = QtGui.QHBoxLayout()
        pixellabel = QtGui.QLabel("Pixel position and intensity: ")
        pixelvaluelayout.addWidget(pixellabel)

        self.infodisplay = QtGui.QLineEdit()
        pixelvaluelayout.addWidget(self.infodisplay)
        verticallayout.addLayout(pixelvaluelayout)
        
        self.setLayout(verticallayout)
        self.img_widget.currentMousePosition.connect(self.infodisplay.setText)

    def plot(self, array, name=None):
        if array is None:
            return
        if name is not None:
            self.filenamedisplay.setText(name)

        self.img_widget.updateImage(array)

    def setAutoLevels(self, autoLvls):
        self.img_widget.setAutoLevels(autoLvls)

    def setMinLevel(self, level = None):
        self.img_widget.setDisplayMinLevel(level)

    def setMaxLevel(self, level = None):
        self.img_widget.setDisplayMaxLevel(level)

    def changeGradient(self, name):
        self.img_widget.updateGradient(name)

class ImageDisplay(pg.GraphicsLayoutWidget):
    
    currentMousePosition = QtCore.pyqtSignal(QtCore.QString)

    def __init__(self, parent = None):
        super(ImageDisplay, self).__init__(parent)
        self.layout = self.ci
        self.crosshair_locked = False
        self.data = None
        self.autoDisplayLevels = True
        self.displayLevels = [None, None]

        self.viewbox = self.layout.addViewBox(row=0, col=1)

        self.image = pg.ImageItem()
        self.viewbox.addItem(self.image)
        
        leftAxis = pg.AxisItem('left')
        leftAxis.linkToView(self.viewbox)
        self.layout.addItem(leftAxis, row=0, col=0)
        
        bottomAxis = pg.AxisItem('bottom')
        bottomAxis.linkToView(self.viewbox)
        self.layout.addItem(bottomAxis, row=1, col =1)
        
        self.graditem = GI.GradientItem()
        self.graditem.setImageItem(self.image)
        
        self.layout.addItem(self.graditem, row = 0, col=2)
        
        self.layout.scene().sigMouseMoved.connect(self.mouse_position)
        self.layout.scene().sigMouseClicked.connect(self.mouse_click)
        
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=(255, 0, 0))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=(255, 0, 0))
        self.viewbox.addItem(self.vLine, ignoreBounds=True)
        self.viewbox.addItem(self.hLine, ignoreBounds=True)

    def addItem(self, item):
        self.image.additem(item)

    def updateImage(self, img=None):
        if(self.autoDisplayLevels):
            self.image.setImage(img, autoLevels = True)
        else:
            self.image.setImage(img, autoLevels = False, levels=self.displayLevels)
        self.data = img
    
    def updateGradient(self, name):
        self.graditem.setGradientByName(name)
    
    def mouse_position(self, event):
        try:
            mousePoint = self.image.mapFromScene(event)
            xdata = math.floor(mousePoint.x())
            ydata = math.floor(mousePoint.y())

            if not self.crosshair_locked:
                self.vLine.setPos(xdata)
                self.hLine.setPos(ydata)

            intensity = self.data[math.floor(xdata), math.floor(ydata)]
            self.currentMousePosition.emit("x=%.2f, y=%.2f, intensity=%.4f" % (xdata, ydata, intensity))
        
        except:
            pass

    def mouse_click(self, event):

        mousePoint = self.image.mapFromScene(event.scenePos())

        xdata = mousePoint.x()
        ydata = mousePoint.y()

        # if double click: fix mouse crosshair
        # another double click releases the crosshair again
        #~ if event.double():
            #~ self.crosshair_locked = not self.crosshair_locked
            #~ if not self.crosshair_locked:
                #~ self.vLine.setPos(xdata)
                #~ self.hLine.setPos(ydata)
    
    def setAutoLevels(self, autoLvls):
        if(autoLvls):
            self.autoDisplayLevels = True
        else:
            self.autoDisplayLevels = False

    def setDisplayMinLevel(self, level = None ):
        if ( level is not None):
            self.displayLevels[0] = level
    
    def setDisplayMaxLevel(self, level = None ):
        if ( level is not None):
            self.displayLevels[1] = level
    
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    dialog = HidraLiveViewer()
    from PyQt4 import QtTest

    i = 1
    dialog.show()
    while True:
        rand_arr = 10 * np.random.rand(100, 200) + 1
        dialog.plot2(img=rand_arr, name=("random number test nr. " + str(i)))
        i += 1
        QtTest.QTest.qWait(2000)
