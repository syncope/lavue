LaVue - Live Image Viewer
=========================

Introduction
------------

This is a simple implementation of a live viewer front end.
It is supposed to show a live image view from xray-detectors at PETRA3 @ DESY,

  e.g. Pilatus, Lambda, Eiger, PerkinElmer, PCO, LimaCCD, and others.

![LaVue - Live Image Viewer GUI](https://raw.github.com/jkotan/lavue/develop/doc/_image/lavue2.png)

Download
--------

Just clone the git repository to any convenient place.
    git clone https://github.com/syncope/lavue.git

Run Requirements
----------------

For the visuals pyqt4, pyqtgraph and numpy are needed.
In order to load (and apply) either mask files or background images for subtraction, fabio must be installed.
An existing hidra installation is needed for the actual transfer of data.

Internals
---------

Data source is a HiDRA server, from which data is fetched by a query_next call.
The data is a tuple of a numpy array and a filename.

How to use
----------

The basic usage is to start the executable *laVue*, from which the pre-configured HiDRA server can be connected with the current host.

The controls should be more or less self-explanatory.

The screen is vertically divided into two parts, the control and the display part.

On the left part of the dialog the controls are presented.
The order from top to bottom is similar to the processing flow.
The topmost section is dedicated to the connection.
The current hostname is shown, along with the connection status.
In order to connect to a server, select it from the drop-down list and click "Connect".
The status of the connection is then indicated.
In case of a failed attempt, please look for more informationat the terminal from where the application was started.
The second section shows possible preparation steps before the image is displayed.
Background subtraction can be applied, once an image has been selected.
Either the current shown image can be used, or selected from a file.
In addition it is possible to mirror, rotate or flip the image upside down from the "Transformation" drop-down menu.
Please note that these choices regarding the preparation are only applied to the next new image.

The most important choice is the one regarding the intensity scaling of the image.
Default value is square root scaling, which suppresses any intensity value below zero.
The radio button selection can also be "linear" or logarithmic.
The lower limit for the logarithmic display is .01 in linear units, or -2 in logarithmic.
Please note that the choice of scaling affects ALL displayed intensity values -- in the limit setting, the statistics part and in the pixel detail display.

The limits on the displayed intensities can be set automatically (default).
But the levels can also be set manually in the spin boxes.
To apply the current choice, click the "apply levels" button.

For easier interpretation of the displayed intensities different gradients can be selected in the drop-down menu.
One can try different settings, which are immediately used.
Two choices include a specific choices for "clipping" intensities, that are the ones outside the manually selected limits.
"greyclip" uses a grey scale with red as the overflow colour; "spectrumclip" uses white as clipping colour.

The last section is for value display only.
It shows the (raw) image intensity value statistics: maximum, mean and variance.


On the right hand side, the image is displayed in the largest section of the screen.
Above that image display, the current image name is displayed.
Below the image display the x and y values, along with the (scaled!) intensity can be shown of the pixel that the mouse is currently positioned at.
To give a visual aid, a red crosshair is displayed at the current mouse position.
The crosshair is centered in the middle of a pixel.

The image display is composed of the axes of the currently visible image, as well as the chosen colour gradient.
It is possible to zoom in and out the image, using the mouse wheel.
To move the displayed image, keep the left mouse button pressed and move the mouse.
To reset to the full view, right-click with the mouse and select "View all".


Please note that the image statistics display is directly affected by the choice of intensity scaling.
Square root scaling of the intensity is the default.
The displayed image color code is scaled according to the chosen scale.

The cursor position display (move the mouse over the image display area), indicated by the red crosshair, is used to show the the intensity of the chosen pixel.
The value is displayed in the line below the image, using linear intensities.
The values in the "levels selection" box are also linear.

