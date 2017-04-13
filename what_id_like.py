try:
    import numpy as np
    data = np.random.normal(size=(100,100))

    import pyqtgraph as pg
    pg.mkQApp()
    w = pg.GraphicsLayoutWidget()
    w.show()
    v = w.addViewBox(row=0, col=0)
    p1 = w.addPlot(row=0, col=1)
    p2 = w.addPlot(row=1, col=0)

    # restrict size of plot areas
    w.ci.layout.setColumnMaximumWidth(1, 100)
    w.ci.layout.setRowMaximumHeight(1, 100)

    # force central viewbox and side plots to have matching coordinate systems
    p1.setYLink(v)  
    p2.setXLink(v)

    # Show image data and plot image mean axross x/y axes
    img = pg.ImageItem(data)
    v.addItem(img)
    p1.plot(x=data.mean(axis=0), y=np.arange(0, data.shape[1]))
    p2.plot(x=np.arange(0, data.shape[1]), y=data.mean(axis=1))
    i = input()
except:
    pass

