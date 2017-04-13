#
# author: Ch. Rosemann, DESY
# email: christoph.rosemann@desy.de


# first try for a live viewer image display
# base it on a qt dialog
# this is just the formal definition of the graphical elements !

import pyqtgraph as pg
import math 

from PyQt4 import QtCore, QtGui
import sys


class gui_definition(QtGui.QDialog):

    def __init__(self, parent=None):
        super(gui_definition, self).__init__(parent)

        # make a grid layout
        # | hidra | image path | 
        # 
        vlayout = QtGui.QVBoxLayout()
        hw = hidra_widget()
        isw = intensityscaling_widget()

        globallayout = QtGui.QHBoxLayout()
        
        self.img_w = image_widget()
        #~ self.img_w = image_alt_widget()
        
        self.raw_image = None
        
        ## define grid elements
        vlayout.addWidget(hw)
        vlayout.addWidget(isw)
        
        globallayout.addLayout(vlayout)
        globallayout.addWidget(self.img_w)
        
        self.setLayout(globallayout)

        self.setWindowTitle("Live Image Viewer")
    
    
    def plot(self, nparr):
        self.raw_image = nparr
        self.img_w.plot(nparr)
        


class hidra_widget(QtGui.QWidget):
    """
    Connect and disconnect hidra service.
    """    
    
    def __init__(self, parent=None):
        super(hidra_widget, self).__init__(parent)
        
        self.connected = False
        # grid/table layout: 
        # | label:         | server name/details |
        # | connect button |  status display     |
        gridlayout = QtGui.QGridLayout()
        
        self.widget00 = QtGui.QLabel(u"HiDRA server")
        self.widget01 = QtGui.QLabel(u"SomeName")
        self.widget10 = QtGui.QPushButton("Connect")
        self.widget11 = QtGui.QLineEdit("Not connected")
        
        self.widget10.clicked.connect(self.toggleServerConnection)
        
        gridlayout.addWidget(self.widget00, 0, 0)
        gridlayout.addWidget(self.widget10, 1, 0)
        gridlayout.addWidget(self.widget01, 0, 1)
        gridlayout.addWidget(self.widget11, 1, 1)
        
        self.setLayout(gridlayout)
        
    def toggleServerConnection(self):
        if(not self.connected):
            try:
                magic_hidra_connect_command
            except:
                print("Big big connect error")
                return 

        self.connected = not self.connected
        
        if(self.connected):
            self.widget11.setText("Connected")
        else:
            self.widget11.setText("Not connected")


class imagesettings_widget(QtGui.QWidget):
    """
    Control the image settings.
    """    
    
    def __init__(self, parent=None):
        super(imagesettings_widget, self).__init__(parent)

        # two columns layout: 
        # | radiobuttons       | checkboxes |
        #columnlayout = QtGui.QHBoxLayout()
        
        #~ leftw = imagetransformations_widget()
        rightw = intensityscaling_widget()
        
        #~ columnlayout.addWidget(leftw)
        #~ columnlayout.addWidget(rightw)
        
        #~ self.setLayout(columnlayout)


class intensityscaling_widget(QtGui.QWidget):
    """
    Select how the image intensity is supposed to be scaled.
    """
    
    def __init__(self, parent=None):
        super(intensityscaling_widget, self).__init__(parent)
        
        self.current = "sqrt"
        verticallayout = QtGui.QVBoxLayout()
        
        self.linbutton = QtGui.QRadioButton(u"linear")
        self.logbutton = QtGui.QRadioButton(u"log")
        self.sqrtbutton = QtGui.QRadioButton(u"sqrt")
        
        self.linbutton.toggled.connect(self.setCurrentScaling)
        self.logbutton.toggled.connect(self.setCurrentScaling)
        self.sqrtbutton.toggled.connect(self.setCurrentScaling)
        self.sqrtbutton.setChecked(True)
        
        verticallayout.addWidget(self.linbutton)
        verticallayout.addWidget(self.logbutton)
        verticallayout.addWidget(self.sqrtbutton)

        self.setLayout(verticallayout)

    def getCurrentScaling(self):
        return self.current
    
    def setCurrentScaling(self, scaling):
        if self.linbutton.isChecked():
            self.current = "lin"
        elif self.logbutton.isChecked():
            self.current = "log"
        else:
            self.current = "sqrt"
        

class imagetransformations_widget(QtGui.QWidget):
    """
    Select how an image should be transformed.
    """
    
    def __init__(self, parent=None):
        super(imagetransformations_widget, self).__init__(parent)
        
        verticallayout = QtGui.QVBoxLayout()
        
        flip = QtGui.QCheckBox(u"flip")
        mirror = QtGui.QCheckBox(u"mirror")
        rotate90 = QtGui.QCheckBox(u"rotate90")
        
        verticallayout.addWidget(flip)
        verticallayout.addWidget(mirror)
        verticallayout.addWidget(rotate90)

        self.setLayout(verticallayout)


class image_widget(QtGui.QWidget):
    """
    The part of the GUI that incorporates the image view.
    """
    
    def __init__(self, parent=None):
        super(image_widget, self).__init__(parent)
        
        self.nparray = None
        self.crosshair_locked = False
        self.imageItem = None
        
        # the actual image is an item of the PlotWidget
        self.img_widget = pg.PlotWidget()
        self.img_widget.scene().sigMouseMoved.connect(self.mouse_position)
        self.img_widget.scene().sigMouseClicked.connect(self.mouse_click)

        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=(255, 0, 0))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=(255, 0, 0))

        gridlayout = QtGui.QGridLayout()
        gridlayout.addWidget(self.img_widget, 0,0)

        # the vertical projection on one side
        self.img_vproj_widget = pg.PlotWidget()
        gridlayout.addWidget(self.img_vproj_widget, 0,1)

        # the horizontal projection below
        self.img_hproj_widget = pg.PlotWidget()
        gridlayout.addWidget(self.img_hproj_widget, 1,0)

        self.infodisplay = QtGui.QLineEdit()
        gridlayout.addWidget(self.infodisplay, 1,1)

        self.setLayout(gridlayout)
        

    def mouse_position(self, event):
        
        try:
            mousePoint = self.imageItem.mapFromScene(event)
            xdata = math.floor(mousePoint.x())
            ydata = math.floor(mousePoint.y())

            if not self.crosshair_locked:
                self.vLine.setPos(xdata)
                self.hLine.setPos(ydata)

            intensity = self.nparray[math.floor(xdata), math.floor(ydata)]
            self.infodisplay.setText("x=%.2f, y=%.2f, intensity=%.2f"
                                           % (xdata, ydata, intensity))
        except:
            self.infodisplay.setText("error")

    def mouse_click(self, event):
        
        mousePoint = self.imageItem.mapFromScene(event.scenePos())

        xdata = mousePoint.x()
        ydata = mousePoint.y()

        if event.double():
            self.crosshair_locked = not self.crosshair_locked

            if not self.crosshair_locked:
                self.vLine.setPos(xdata)
                self.hLine.setPos(ydata)
             
    def plot(self, nparr):
        self.nparray = nparr
        
        if self.imageItem is None:
            self.imageItem = pg.ImageItem(self.nparray)
            self.img_widget.addItem(self.imageItem)
            self.img_widget.addItem(self.vLine, ignoreBounds=True)
            self.img_widget.addItem(self.hLine, ignoreBounds=True)
        else:
            self.imageItem.setImage(data)
            


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    
    dialog = gui_definition()
    #dialog = image_widget()
    
    # to take out: generate random image
    import numpy as np
    rand_arr = np.random.rand(550,550)
            
    dialog.plot(rand_arr)
    #~ dialog = hidra_widget()
    dialog.show()
    i = input()
