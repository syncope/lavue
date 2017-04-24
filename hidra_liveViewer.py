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
import mystery


class gui_definition(QtGui.QDialog):

    def __init__(self, parent=None, signal_host=None, target=None):
        super(gui_definition, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # instantiate the data source
        # here: hardcoded the hidra cbf source
        # note: host and target are defined here and in another place
        self.data_source = hcs.HiDRA_cbf_source(
            mystery.signal_host, mystery.target)
        # time in [ms] between calls to hidra
        self.waittime = 500

        # keep a reference to the "raw" image and the current filename
        self.raw_image = None
        self.image_name = None
        self.display_image = None

        # define left hand side layout: vertical
        vlayout = QtGui.QVBoxLayout()

        # instantiate the widgets and declare the parent
        self.isw = intensityscaling_widget(parent=self)
        self.itw = imagetransformations_widget(parent=self)
        self.lsw = levels_widget(parent=self)
        self.stats = statistics_widget(parent=self)
        self.img_w = image_widget(parent=self)
        self.hw = hidra_widget(parent=self)
        # set the right names for the hidra display at initialization
        self.hw.setNames(self.data_source.getTargetSignalHost())

        # the dialog layout is side by side
        globallayout = QtGui.QHBoxLayout()

        # place widgets on the layouts
        # first the vertical layout on the left side
        vlayout.addWidget(self.hw)
        vlayout.addWidget(self.itw)
        vlayout.addWidget(self.isw)
        vlayout.addWidget(self.stats)
        vlayout.addWidget(self.lsw)

        # then the vertical layout on the --global-- horizontal one
        globallayout.addLayout(vlayout)
        globallayout.addWidget(self.img_w)

        self.setLayout(globallayout)
        self.setWindowTitle("Live Image Viewer")

        # connect signals::
        # signal from intensity scaling widget:
        self.isw.changeScaling.connect(self.plot)

        # signal from limit setting widget
        self.lsw.levelsChanged.connect(self.img_w.setLevels)
        # signal from image widget
        self.img_w.initialLevels.connect(self._setInitialLevels)

        # connecting signals from hidra widget:
        self.hw.hidra_connect.connect(self.connect_hidra)
        self.hw.hidra_connect.connect(self.startPlotting)

        self.hw.hidra_disconnect.connect(self.stopPlotting)
        self.hw.hidra_disconnect.connect(self.disconnect_hidra)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.waittime)
        self.timer.timeout.connect(
            lambda: self._assignNewData(self.data_source.getData()))
        self.timer.timeout.connect(lambda: self.plot())

    def _setInitialLevels(self, lowlim, uplim):
        self.lsw._setLevels(lowlim, uplim)

    def plot(self, img=None, name=None):
        """ The main command of the live viewer class: draw a numpy array with the given name."""
        if img is None:
            return

        if img is not None and name is not None:
            self.image_name = name
            self.display_image = self.itw.transform(img)

        # calls internally the plot function of the plot widget
        self.img_w.plot(
            self.display_image, self.isw.getCurrentScaling(), self.image_name)
        self.stats.update_stats(self.display_image, self.isw.getCurrentScaling())

        # mode changer: start plotting mode
    def startPlotting(self):
        # only start plotting if the connection is really established
        if not self.hw.isConnected():
            return

        self.timer.start()

    def _assignNewData(self, nameDataTuple):
        # get the data from the source and keep it internally
        self.raw_image, self.image_name = nameDataTuple
        # the internal data object is copied to allow for internal conversions
        self.display_image = self.raw_image

        # mode changer: stop plotting mode
    def stopPlotting(self):
        self.timer.stop()

        # call the connect function of the hidra interface
    def connect_hidra(self):
        if not self.data_source.connect():
            self.hw.connectFailure()
            print(
                "<WARNING> The HiDRA connection could not be established. Check the settings.")
        else:
            self.hw.connectSuccess()

        # call the disconnect function of the hidra interface
    def disconnect_hidra(self):
        self.data_source.disconnect()


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

        self.serverLabel = QtGui.QLabel(u"HiDRA server: ")
        self.serverName = QtGui.QLabel(u"SomeName")
        self.hostlabel = QtGui.QLabel("Current host: ")
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


class imagesettings_widget(QtGui.QWidget):

    """
    Control the image settings.
    """

    def __init__(self, parent=None):
        super(imagesettings_widget, self).__init__(parent)

        # two columns layout:
        # | radiobuttons       | checkboxes |
        columnlayout = QtGui.QHBoxLayout()

        leftw = intensityscaling_widget()
        rightw = limitsetting_widget()

        columnlayout.addWidget(leftw)
        columnlayout.addWidget(rightw)

        self.setLayout(columnlayout)


class intensityscaling_widget(QtGui.QGroupBox):

    """
    Select how the image intensity is supposed to be scaled.
    """
    changeScaling = QtCore.pyqtSignal()

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
        self.changeScaling.emit()


class levels_widget(QtGui.QGroupBox):

    """
    Set minimum and maximum displayed values.
    """

    levelsChanged = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        super(levels_widget, self).__init__(parent)

        self.setTitle("Set display levels")
        layout = QtGui.QGridLayout()

        informLabel = QtGui.QLabel("Note: Linear scale!")
        minLabel = QtGui.QLabel("minimum value: ")
        maxLabel = QtGui.QLabel("maximum value: ")

        self.minVal = QtGui.QDoubleSpinBox()
        self.maxVal = QtGui.QDoubleSpinBox()

        self.applyButton = QtGui.QPushButton("Apply levels")

        layout.addWidget(informLabel, 0, 0)
        layout.addWidget(minLabel, 1, 0)
        layout.addWidget(self.minVal, 1, 1)
        layout.addWidget(maxLabel, 2, 0)
        layout.addWidget(self.maxVal, 2, 1)
        layout.addWidget(self.applyButton, 3, 1)

        self.setLayout(layout)
        self.applyButton.clicked.connect(
            lambda: self.levelsChanged.emit(self.minVal.value(), self.maxVal.value()))

    def _setLevels(self, lowlim, uplim):
        self.minVal.setValue(lowlim)
        self.maxVal.setValue(uplim)


class statistics_widget(QtGui.QGroupBox):

    """
    Display some general image statistics.
    """

    def __init__(self, parent=None):
        super(statistics_widget, self).__init__(parent)

        self.setTitle("Image statistics")
        layout = QtGui.QGridLayout()

        self.array = None
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

    def update_stats(self, array, scaling):
        self.array = array
        if array is None:
            return
        if self.scaling is not scaling:
            self.scaling = scaling

        if self.scaling == "sqrt":
            self.array = np.sqrt(self.array)
        elif self.scaling == "log":
            self.array = np.log10(self.array)

        self.maxVal.setText(str("%.4f" % np.amax(self.array)))
        self.meanVal.setText(str("%.4f" % np.mean(self.array)))
        self.varVal.setText(str("%.4f" % np.var(self.array)))

        self.show()


class imagetransformations_widget(QtGui.QGroupBox):

    """
    Select how an image should be transformed.
    """

    def __init__(self, parent=None):
        super(imagetransformations_widget, self).__init__(parent)

        self.setTitle("Image transformations")

        horizontallayout = QtGui.QHBoxLayout()

        self.flip = QtGui.QCheckBox(u"flip")
        self.mirror = QtGui.QCheckBox(u"mirror")
        self.rotate90 = QtGui.QCheckBox(u"rot90")

        horizontallayout.addWidget(self.flip)
        horizontallayout.addWidget(self.mirror)
        horizontallayout.addWidget(self.rotate90)

        self.setLayout(horizontallayout)

    def transform(self, display_img):
        '''Do the image transformation on the given numpy array.'''
        if display_img is None:
            return
        if self.flip.isChecked():
            display_img = np.flipud(display_img)
        if self.mirror.isChecked():
            display_img = np.fliplr(display_img)
        if self.rotate90.isChecked():
            display_img = np.transpose(display_img)
        return display_img


class image_widget(QtGui.QWidget):

    """
    The part of the GUI that incorporates the image view.
    """

    levelsHaveChanged = QtCore.pyqtSignal()
    initialLevels = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        super(image_widget, self).__init__(parent)

        self.nparray = None
        self.crosshair_locked = False
        self.imageItem = None
        self.levels = [None, None]  # the min/max draw values in linear space
        self.levelsSet = False
        self._doOnlyOnce = True

        # the actual image is an item of the PlotWidget
        self.img_widget = pg.PlotWidget()
        self.img_widget.setAspectLocked(True)
        self.img_widget.scene().sigMouseMoved.connect(self.mouse_position)
        self.img_widget.scene().sigMouseClicked.connect(self.mouse_click)

        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=(255, 0, 0))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=(255, 0, 0))

        # self.gradient = pg.GradientWidget(orientation='right', allowAdd=False)
        #~ for t in self.gradient.listTicks():
            #~ removeTick(t)

        verticallayout = QtGui.QVBoxLayout()

        self.filenamedisplay = QtGui.QLineEdit()
        verticallayout.addWidget(self.filenamedisplay)

        verticallayout.addWidget(self.img_widget)
        #~ horizontallayout = QtGui.QHBoxLayout()
        #~ horizontallayout.addWidget(self.img_widget)
        #~ horizontallayout.addWidget(self.gradient)
        #~ verticallayout.addLayout(horizontallayout)

        self.infodisplay = QtGui.QLineEdit()
        verticallayout.addWidget(self.infodisplay)

        self.setLayout(verticallayout)

    def mouse_position(self, event):

        try:
            mousePoint = self.imageItem.mapFromScene(event)
            xdata = math.floor(mousePoint.x())
            ydata = math.floor(mousePoint.y())

            if not self.crosshair_locked:
                self.vLine.setPos(xdata)
                self.hLine.setPos(ydata)

            intensity = self.nparray[math.floor(xdata), math.floor(ydata)]
            self.infodisplay.setText("x=%.2f, y=%.2f, linear (!) intensity=%.4f"
                                     % (xdata, ydata, intensity))
        except:
            self.infodisplay.setText("error")

    def mouse_click(self, event):

        mousePoint = self.img_widget.mapFromScene(event.scenePos())

        xdata = mousePoint.x()
        ydata = mousePoint.y()

        # if double click: fix mouse crosshair
        # another double click releases the crosshair again
        #~ if event.double():
            #~ self.crosshair_locked = not self.crosshair_locked
            #~
            #~ if not self.crosshair_locked:
                #~ self.vLine.setPos(xdata)
                #~ self.hLine.setPos(ydata)

    def plot(self, nparr, style, name=None):
        if nparr is None:
            return
        if name is not None:
            self.filenamedisplay.setText(name)
        plotlevels = [None, None]
        self.nparray = np.float32(nparr)
        drawarray = self.nparray

        # check if drawing levels are set
        if not self.levelsSet:
            plotlevels[0] = np.amin(drawarray)
            plotlevels[1] = np.amax(drawarray)
            if self._doOnlyOnce:
                self.initialLevels.emit(plotlevels[0], plotlevels[1])
                self._doOnlyOnce = False
        else:
            plotlevels = self.levels

        if style == "sqrt":
            np.clip(drawarray, 0, np.inf)
            drawarray = np.sqrt(self.nparray)
            plotlevels = [math.sqrt(plotlevels[0]), math.sqrt(plotlevels[1])]
        elif style == "log":
            np.clip(drawarray, 10e-3, np.inf)
            drawarray = np.log10(self.nparray)
            if (plotlevels[0] < 10e-3):
                plotlevels[0] = 10e-3
            if (plotlevels[1] < 0.1):
                plotlevels[1] = 1.
            plotlevels = [math.log10(plotlevels[0]), math.log10(plotlevels[1])]
        elif style == "lin":
            plotlevels = [math.floor(plotlevels[0]), math.ceil(plotlevels[1])]
        else:
            print("Chosen display style '" + style + "' is not valid.")
            return

        if self.imageItem is None:
            self.imageItem = pg.ImageItem()
            self.img_widget.addItem(self.imageItem)
            self.img_widget.addItem(self.vLine, ignoreBounds=True)
            self.img_widget.addItem(self.hLine, ignoreBounds=True)

        self.imageItem.setImage(drawarray, autolevels=False, levels=plotlevels)
        #~ self.img_widget.setLimits(xMin=0, xMax=drawarray.shape[0], yMin=0, yMax=drawarray.shape[1])
        self.img_widget.setRange(xRange=[0, drawarray.shape[0]], yRange=[
                                 0, drawarray.shape[1]], padding=0, disableAutoRange=True)

    def setLevels(self, lowlim, uplim):
        if self.levels[0] != lowlim or self.levels[1] != uplim:
            self.levelsSet = True
            self.levels = [lowlim, uplim]
            self.levelsHaveChanged.emit()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    dialog = gui_definition()
    from PyQt4 import QtTest

    i = 1
    dialog.show()
    while True:
        rand_arr = 10 * np.random.rand(100, 200) + 1
        dialog.plot(rand_arr, "random number test nr. " + str(i))
        i += 1
        QtTest.QTest.qWait(2000)
