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

import pyqtgraph as pg
import weakref
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.widgets.GraphicsView import GraphicsView
from pyqtgraph import HistogramLUTItem
from pyqtgraph.graphicsItems.GraphicsWidget import GraphicsWidget
from pyqtgraph.graphicsItems.ViewBox import ViewBox
from pyqtgraph.graphicsItems.GradientEditorItem import GradientEditorItem
from pyqtgraph.graphicsItems.LinearRegionItem import LinearRegionItem
from pyqtgraph.graphicsItems.PlotDataItem import PlotDataItem
from pyqtgraph.graphicsItems.AxisItem import AxisItem
from pyqtgraph.Point import Point
import pyqtgraph.functions as fn
import numpy as np

VMAJOR, VMINOR, VPATCH = pg.__version__.split(".")

pg.graphicsItems.GradientEditorItem.Gradients['reversegrey'] = {
    'ticks': [(0.0, (255, 255, 255, 255)),
              (1.0, (0, 0, 0, 255)), ], 'mode': 'rgb'}
pg.graphicsItems.GradientEditorItem.Gradients['highcontrast'] = {
    'ticks': [(0.0, (0, 0, 0, 255)),
              (1.0, (255, 255, 0, 255)), ], 'mode': 'rgb'}
pg.graphicsItems.GradientEditorItem.Gradients['spectrum'] = {
    'ticks': [(0.0, (255, 0, 255, 255)),
              (1.0, (255, 0, 0, 255))], 'mode': 'hsv'}
pg.graphicsItems.GradientEditorItem.Gradients['spectrumclip'] = {
    'ticks': [(0.0, (255, 0, 255, 255)),
              (.99, (255, 0, 0, 255)),
              (1.0, (255, 255, 255, 255))], 'mode': 'hsv'}
# define two new gradients of choice
pg.graphicsItems.GradientEditorItem.Gradients['inverted'] = {
    'ticks': [(0.0, (255, 255, 255, 255)),
              (1.0, (0, 0, 0, 255)), ], 'mode': 'rgb'}
# pg.graphicsItems.GradientEditorItem.Gradients['highcontrast'] = {
#    'ticks': [(0.0, (0, 0, 0, 255)),
#              (1.0, (255, 255, 0, 255)), ], 'mode': 'rgb'}

__all__ = ['HistogramHLUTWidget']


class HistogramHLUTWidget(GraphicsView):

    def __init__(self, parent=None,  *args, **kargs):
        background = kargs.get('background', 'default')
        GraphicsView.__init__(
            self, parent, useOpenGL=False, background=background)
        self.item = HistogramHLUTItem(*args, **kargs)
        self.setCentralItem(self.item)
        self.setSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        self.setMinimumWidth(95)

    def sizeHint(self):
        return QtCore.QSize(115, 200)

    def __getattr__(self, attr):
        return getattr(self.item, attr)


class GradientEditorItemWS(GradientEditorItem):

    sigNameChanged = QtCore.Signal(str)

    def __init__(self, *args, **kargs):
        GradientEditorItem.__init__(self, *args, **kargs)

    def loadPreset(self, name):
        """ loads a predefined gradient.
        """
        GradientEditorItem.loadPreset(self, name)
        self.sigNameChanged.emit(name)


class HistogramHLUTItem(HistogramLUTItem):

    def __init__(self, image=None, fillHistogram=True):
        GraphicsWidget.__init__(self)

        self.lut = None
        if VMAJOR == '0' and int(VMINOR) < 10:
            self.imageItem = None
        else:
            self.imageItem = lambda: None

        self.layout = QtGui.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)

        self.vb = ViewBox()
        # self.vb.setMaximumHeight(152)
        self.vb.setMinimumHeight(45)
        self.vb.setMouseEnabled(x=True, y=False)
        # self.vb.setMouseEnabled(x=False, y=True)

        self.gradient = GradientEditorItemWS()
        self.gradient.setOrientation('bottom')
        self.gradient.loadPreset('grey')

        self.region = LinearRegionItem([0, 1], LinearRegionItem.Vertical)
        self.region.setZValue(1000)
        self.vb.addItem(self.region)

        self.axis = AxisItem(
            'top', linkView=self.vb, maxTickLength=-10, showValues=False)

        self.layout.addItem(self.axis, 0, 0)
        self.layout.addItem(self.vb, 1, 0)
        self.layout.addItem(self.gradient, 2, 0)
        self.range = None

        self.gradient.setFlag(self.gradient.ItemStacksBehindParent)
        self.vb.setFlag(self.gradient.ItemStacksBehindParent)

        self.gradient.sigGradientChanged.connect(self.gradientChanged)
        self.region.sigRegionChanged.connect(self.regionChanging)
        self.region.sigRegionChangeFinished.connect(self.regionChanged)
        self.vb.sigRangeChanged.connect(self.viewRangeChanged)
        self.plot = PlotDataItem()
        # self.plot.dataBounds(1, 0.9)
        # self.plot.dataBounds(0, 0.9)

        self.fillHistogram(fillHistogram)

        self.vb.addItem(self.plot)
        self.autoHistogramRange()

        if image is not None:
            self.setImageItem(image)
        self.background = None

    def setGradientByName(self, name):
        try:
            self.gradient.loadPreset(str(name))
        except:
            self.gradient.loadPreset("highContrast")

    def paint(self, p, *args):
        pen = self.region.lines[0].pen
        rgn = self.getLevels()
        p1 = self.vb.mapFromViewToItem(
            self, Point(rgn[0], self.vb.viewRect().center().y()))
        p2 = self.vb.mapFromViewToItem(
            self, Point(rgn[1], self.vb.viewRect().center().y()))
        gradRect = self.gradient.mapRectToParent(
            self.gradient.gradRect.rect())
        for pen in [fn.mkPen('k', width=3), pen]:
            p.setPen(pen)
            p.drawLine(p1, gradRect.topLeft())
            p.drawLine(p2, gradRect.topRight())
            p.drawLine(gradRect.topLeft(), gradRect.bottomLeft())
            p.drawLine(gradRect.topRight(), gradRect.bottomRight())

    def setHistogramRange(self, mn, mx, padding=0.1):
        """Set the Y range on the histogram plot.
        This disables auto-scaling."""
        self.vb.enableAutoRange(self.vb.XAxis, False)
        self.vb.setYRange(mn, mx, padding)

    def imageChanged(self, autoLevel=False, autoRange=False):
        if isinstance(self.imageItem, weakref.ref):
            h = self.imageItem().getHistogram()
        else:
            h = self.imageItem.getHistogram()
        if h[0] is not None and self.background is not None:
            mn = min([abs(x - self.background) for x in h[0]])
            nid = np.where(h[0] == mn)
            if nid and len(nid) and len(nid[0]):
                h[1][[0][0]] = 0
        # print(h)
        if h[0] is None:
            return
        self.plot.setData(*h)
        if autoLevel:
            mn = h[0][0]
            mx = h[0][-1]
            self.region.setRegion([mn, mx])
