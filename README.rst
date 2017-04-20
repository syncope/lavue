Lightweight Live Viewer: LaVue
==============================

This is a simple implementation of a live viewer front end.
It is supposed to show a live image view from xray-detectors at PETRA3.
It is work in progress.

Download
--------

Just clone the git repository to any convenient place.
    git clone https://github.com/syncope/lavue.git

Run Requirements
----------------

For the visuals pyqt4, pyqtgraph and numpy are needed.
An existing hidra installation is needed for the actual transfer of data.

Internals
---------

Data source is a HiDRA server, from which data is fetched by a query_next call.
The data is a tuple of a numpy array and a filename.

How to use
----------

The basic usage is to start the executable *laVueDirecte*, from which the pre-configured HiDRA server can be connected with the current host.

To view the basic functionality, a test can be run by invoking the hidra_liveViewer.py module directly from python:
    python3 hidra_liveViewer.py

The controls should be more or less self-explanatory.
Please note that the image statistics display is directly affected by the choice of intensity scaling.
Square root scaling of the intensity is the default.
The displayed image color code is scaled according to the chosen scale.


In contrast to this to settings are and displays are linear!

The cursor position display (move the mouse over the image display area), indicated by the red crosshair, is used to show the the intensity of the chosen pixel.
The value is displayed in the line below the image, using linear intensities.
The values in the "levels selection" box are also linear.

Known issues and Things to fix
------------------------------

Right now the image is displayed in a scaled way regarding its dimensions.
In the future a 100% view (or 1:1) is planned, where one detector pixel equals one pixel on the screen display.

The shown intensities currently are ranging between black (lowest) and white (highest).
It is foreseen to show the actual gradient and to choose between different gradient schemes.

Maybe an extension for the used detector will be used; this way the image would always be displayed in the correct orientation.
Maybe a "transpose" or "flip/mirror/rotate" option box will be created.
