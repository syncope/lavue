# Copyright (C) 2017  DESY, Christoph Rosemann, Notkestr. 85, D-22607 Hamburg
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
#     Christoph Rosemann <christoph.rosemann@desy.de>
#     Jan Kotanski <jan.kotanski@desy.de>
#


""" live viewer image display base it on a qt dialog """

from __future__ import print_function
from __future__ import unicode_literals

import time
import json
import re
import numpy as np
import os
import zmq

from PyQt4 import QtCore, QtGui

from . import imageSource as hcs
from . import messageBox

from . import gradientChoiceWidget
from . import hidraWidget
from . import imageWidget
from . import intensityScalingWidget
from . import levelsWidget
from . import statisticsWidget
from . import preparationBoxWidget
from . import imageFileHandler
from . import configWidget
from . import sardanaUtils
from . import dataFetchThread

try:
    from .hidraServerList import HidraServerList
except:
    print("Cannot read the list of HiDRA servers.")
    print("Alternate method not yet implemented.")


class HidraLiveViewer(QtGui.QDialog):

    '''The master class for the dialog, contains all other
    widget and handles communication.'''
    update_state = QtCore.pyqtSignal(int)

    def __init__(self, umode=None, parent=None):
        QtGui.QDialog.__init__(self, parent)
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.sourcetypes = []
        if hcs.HIDRA:
            self.sourcetypes.append(
                {"name": "Hidra",
                 "datasource": "HiDRASource",
                 "slot": "updateHidraButton",
                 "hidden": ["attrLabel", "attrLineEdit"]}
            )
        if hcs.PYTANGO:
            self.sourcetypes.append(
                {"name": "Tango",
                 "datasource": "TangoAttrSource",
                 "slot": "updateAttrButton",
                 "hidden": ["hostlabel", "currenthost",
                            "serverLabel", "serverlistBox"]})

        self.sourcetypes.append(
            {"name": "Test",
             "datasource": "GeneralSource",
             "slot": "updateButton",
             "hidden": ["hostlabel", "currenthost",
                        "serverLabel", "serverlistBox",
                        "attrLabel", "attrLineEdit"]},
        )

        self.doorname = ""
        self.addrois = True
        self.secstream = False
        self.secautoport = True
        self.secsockopt = ""
        self.secport = "5657"
        if umode and umode.lower() in ["expert"]:
            self.umode = "expert"
        else:
            self.umode = "user"
        self.showhisto = True
        self.updatehisto = False
        self.interruptonerror = True

        self.seccontext = zmq.Context()
        self.secsocket = self.seccontext.socket(zmq.PUB)
        self.apppid = os.getpid()

        # instantiate the data source
        # here: hardcoded the hidra cbf source!
        # future possibility: use abstract interface and factory for concrete
        # instantiation

        # note: host and target are defined in another place
        self.data_source = hcs.GeneralSource()

        # WIDGET DEFINITIONS
        # instantiate the widgets and declare the parent
        self.hidraW = hidraWidget.HidraWidget(
            parent=self, serverdict=HidraServerList)
        self.prepBoxW = preparationBoxWidget.PreparationBoxWidget(parent=self)
        self.scalingW = intensityScalingWidget.IntensityScalingWidget(
            parent=self)
        self.levelsW = levelsWidget.LevelsWidget(parent=self)
        self.gradientW = gradientChoiceWidget.GradientChoiceWidget(parent=self)
        self.statsW = statisticsWidget.StatisticsWidget(parent=self)
        self.imageW = imageWidget.ImageWidget(parent=self)
        self.levelsW.histogram.setImageItem(self.imageW.img_widget.image)
        self.levelsW.histogram.item.imageChanged(autoLevel=True)

        # self.maskW = self.prepBoxW.maskW
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
        self.levelsW.changeview(self.showhisto)

        self.imageW.cnfButton.clicked.connect(self.configuration)
        if self.umode in ["user"]:
            self.imageW.cnfButton.hide()
        self.imageW.applyROIButton.clicked.connect(self.onapplyrois)
        self.imageW.fetchROIButton.clicked.connect(self.onfetchrois)
#        self.imageW.addROIButton.clicked.connect(self.onaddrois)
#        self.imageW.clearAllButton.clicked.connect(self.onclearrois)
        self.imageW.roiCoordsChanged.connect(self.calc_update_stats_sec)
        self.imageW.pixelComboBox.currentIndexChanged.connect(
            self.onPixelChanged)

        # connecting signals from hidra widget:
        self.hidraW.hidra_connect.connect(self.connect_hidra)
        self.hidraW.hidra_connect.connect(self.startPlotting)

        self.hidraW.hidra_disconnect.connect(self.stopPlotting)
        self.hidraW.hidra_disconnect.connect(self.disconnect_hidra)

        # gradient selector
        self.gradientW.chosenGradient.connect(
            self.levelsW.histogram.setGradientByName)
        # self.gradientW.chosenGradient.connect(self.imageW.changeGradient)
        # self.imageW.img_widget.graditem.gradient.sigNameChanged.connect(
        #    self.gradientW.changeGradient)
        self.levelsW.histogram.gradient.sigNameChanged.connect(
            self.gradientW.changeGradient)

        # simple mutable caching object for data exchange with thread
        # [blocked state | image name | image data]
        # during read+write access state is set to blocked to avoid conflict
        self.exchangelist = dataFetchThread.ExchangeList()

        self.dataFetcher = dataFetchThread.DataFetchThread(
            self.data_source, self.exchangelist)
        self.dataFetcher.newDataName.connect(self.getNewData)
        # ugly !!! sent current state to the data fetcher...
        self.update_state.connect(self.dataFetcher.changeStatus)
        self.hidraW.hidra_state.connect(self.updateSource)

        self.bkgSubW.bkgFileSelection.connect(self.prepareBKGSubtraction)
        self.bkgSubW.useCurrentImageAsBKG.connect(self.setCurrentImageAsBKG)
        self.bkgSubW.applyBkgSubtractBox.stateChanged.connect(
            self.checkBKGSubtraction)
        # self.maskW.maskFileSelection.connect(self.prepareMasking)
        # self.maskW.applyMaskBox.stateChanged.connect(self.checkMasking)

        # signals from transformation widget
        self.trafoW.activatedTransformation.connect(self.assessTransformation)

        # set the right target name for the hidra display at initialization
        self.hidraW.setTargetName(self.data_source.getTarget())
        # self.hidraW.hidra_servername.connect(self.data_source.setSignalHost)
        self.hidraW.hidra_servername.connect(self.setSignalHost)
        self.onPixelChanged()

        self.sardana = sardanaUtils.SardanaUtils()
        settings = QtCore.QSettings()
        self.restoreGeometry(
            settings.value("Layout/Geometry").toByteArray())
        qstval = str(settings.value("Configuration/AddROIs").toString())
        if qstval.lower() == "false":
            self.addrois = False
        qstval = str(settings.value("Configuration/SecAutoPort").toString())
        if qstval.lower() == "false":
            self.secautoport = False

        qstval = str(settings.value("Configuration/ShowHistogram").toString())
        if qstval.lower() == "false":
            self.showhisto = False
        qstval = str(settings.value("Configuration/SecPort").toString())
        try:
            int(qstval)
            self.secport = str(qstval)
        except:
            pass
        qstval = str(settings.value("Configuration/SecStream").toString())
        if qstval.lower() == "true":
            try:
                if self.secautoport:
                    self.secsockopt = "tcp://*:*"
                    self.secsocket.bind(self.secsockopt)
                    self.secport = self.secsocket.getsockopt(
                        zmq.LAST_ENDPOINT).split(":")[-1]
                else:
                    self.secsockopt = "tcp://*:%s" % self.secport
                    self.secsocket.bind(self.secsockopt)
                self.secstream = True
            except:
                self.secstream = False
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "lavue: Cannot connect to: %s" % self.secsockopt)
                messageBox.MessageBox.warning(
                    self, "lavue: Cannot connect to: %s" % self.secsockopt,
                    text, str(value))

        try:
            dataFetchThread.GLOBALREFRESHRATE = float(
                settings.value("Configuration/RefreshRate").toString())
        except:
            pass

        qstval = str(
            settings.value("Configuration/InterruptOnError").toString())
        if qstval.lower() == "false":
            self.interruptonerror = False
        elif qstval.lower() == "true":
            self.interruptonerror = True

        self.levelsW.changeview(self.showhisto)

    def onPixelChanged(self):
        imagew = self.imageW
        text = imagew.pixelComboBox.currentText()
        if text == "ROI":
            imagew.img_widget.vLine.hide()
            imagew.img_widget.hLine.hide()
            imagew.fetchROIButton.show()
            imagew.applyROIButton.show()
            imagew.roiSpinBox.show()
            imagew.labelROILineEdit.show()
            imagew.pixellabel.setText("[x1, y1, x2, y2]: ")
            imagew.roiLabel.show()
            for roi in imagew.img_widget.roi:
                roi.show()
            imagew.img_widget.roienable = True
            imagew.img_widget.roi[0].show()
            imagew.infodisplay.setText("")
            self.trafoName = "None"
            self.trafoW.cb.setCurrentIndex(0)
            self.trafoW.cb.setEnabled(False)
            imagew.roiChanged()
        else:
            imagew.pixellabel.setText("Pixel position and intensity: ")
            for roi in imagew.img_widget.roi:
                roi.hide()
            imagew.fetchROIButton.hide()
            imagew.labelROILineEdit.hide()
            imagew.applyROIButton.hide()
            imagew.roiSpinBox.hide()
            imagew.roiLabel.hide()
            imagew.img_widget.roienable = False
            imagew.img_widget.vLine.show()
            imagew.img_widget.hLine.show()
            imagew.infodisplay.setText("")
            self.trafoW.cb.setEnabled(True)
            imagew.roiCoordsChanged.emit()

    def onaddrois(self):
        if hcs.PYTANGO:
            roicoords = self.imageW.img_widget.roicoords
            if not self.doorname:
                self.doorname = self.sardana.getDeviceName("Door")
            # print("add rois %s " % roicoords)
            # print(self.sardana.getScanEnv(
            #    str(self.doorname), ["DetectorROIs"]))
            rois = json.loads(self.sardana.getScanEnv(
                str(self.doorname), ["DetectorROIs"]))
            rlabel = str(self.imageW.labelROILineEdit.text())
            if rlabel:
                if "DetectorROIs" not in rois or not isinstance(
                        rois["DetectorROIs"], dict):
                    rois["DetectorROIs"] = {}
                if rlabel not in rois["DetectorROIs"] or \
                   not isinstance(rois["DetectorROIs"][rlabel], list):
                    rois["DetectorROIs"][rlabel] = []
                rois["DetectorROIs"][rlabel].append(roicoords)
                # print("rois %s " % rois)
                self.sardana.setScanEnv(str(self.doorname), json.dumps(rois))
            if self.addrois:
                self.sardana.runMacro(
                    str(self.doorname), ["nxsadd", "%s" % rlabel])
        else:
            print("Connection error")

    def onapplyrois(self):
        if hcs.PYTANGO:
            roicoords = self.imageW.img_widget.roicoords
            roispin = self.imageW.roiSpinBox.value()
            if not self.doorname:
                self.doorname = self.sardana.getDeviceName("Door")

            # print("add rois %s " % roicoords)
            # print(self.sardana.getScanEnv(
            # str(self.doorname), ["DetectorROIs"]))
            rois = json.loads(self.sardana.getScanEnv(
                str(self.doorname), ["DetectorROIs"]))
            rlabel = str(self.imageW.labelROILineEdit.text())
            slabel = re.split(';|,| |\n', rlabel)
            slabel = [lb for lb in slabel if lb]
            rid = 0
            lastcrdlist = None
            toremove = []
            toadd = []
            if "DetectorROIs" not in rois or not isinstance(
                    rois["DetectorROIs"], dict):
                rois["DetectorROIs"] = {}
            lastalias = None
            for alias in slabel:
                if alias not in toadd:
                    rois["DetectorROIs"][alias] = []
                lastcrdlist = rois["DetectorROIs"][alias]
                if rid < len(roicoords):
                    lastcrdlist.append(roicoords[rid])
                    rid += 1
                    if alias not in toadd:
                        toadd.append(alias)
                if not lastcrdlist:
                    if alias in rois["DetectorROIs"].keys():
                        rois["DetectorROIs"].pop(alias)
                    if roispin >= 0:
                        toadd.append(alias)
                    else:
                        toremove.append(alias)
                lastalias = alias
            if rid > 0:
                while rid < len(roicoords):
                    lastcrdlist.append(roicoords[rid])
                    rid += 1
                if not lastcrdlist:
                    if lastalias in rois["DetectorROIs"].keys():
                        rois["DetectorROIs"].pop(lastalias)
                    if roispin >= 0:
                        toadd.append(lastalias)
                    else:
                        toremove.append(lastalias)

            # print("rois %s " % rois)
            # print("to remove %s" % toremove)
            # print("to add %s" % toadd)
            self.sardana.setScanEnv(str(self.doorname), json.dumps(rois))
            warns = []
            if self.addrois:
                try:
                    for alias in toadd:
                        _, warn = self.sardana.runMacro(
                            str(self.doorname), ["nxsadd", alias])
                        if warn:
                            warns.extend(list(warn))
                            print("Warning: %s" % warn)
                    for alias in toremove:
                        _, warn = self.sardana.runMacro(
                            str(self.doorname), ["nxsrm", alias])
                        if warn:
                            warns.extend(list(warn))
                            print("Warning: %s" % warn)
                    if warns:
                        msg = "\n".join(set(warns))
                        messageBox.MessageBox.warning(
                            self, "lavue: Errors in setting Measurement group",
                            msg, str(warns))

                except Exception:
                    import traceback
                    value = traceback.format_exc()
                    text = messageBox.MessageBox.getText(
                        "Problems in setting Measurement group")
                    messageBox.MessageBox.warning(
                        self, "lavue: Error in Setting Measurement group",
                        text, str(value))

        else:
            print("Connection error")

    def __storeSettings(self):
        """ Stores settings in QSettings object
        """
        settings = QtCore.QSettings()
        settings.setValue(
            "Configuration/AddROIs",
            QtCore.QVariant(self.addrois))
        settings.setValue(
            "Configuration/ShowHistogram",
            QtCore.QVariant(self.showhisto))
        settings.setValue(
            "Configuration/RefreshRate",
            QtCore.QVariant(dataFetchThread.GLOBALREFRESHRATE))
        settings.setValue(
            "Configuration/SecPort",
            QtCore.QVariant(self.secport))
        settings.setValue(
            "Configuration/SecAutoPort",
            QtCore.QVariant(self.secautoport))
        settings.setValue(
            "Configuration/SecStream",
            QtCore.QVariant(self.secstream))
        # settings.setValue(
        #    "Configuration/Door",
        #    QtCore.QVariant(self.doorname))
        settings.setValue(
            "Layout/Geometry",
            QtCore.QVariant(self.saveGeometry()))
        settings.setValue(
            "Configuration/InterruptOnError",
            QtCore.QVariant(self.interruptonerror))

    def closeEvent(self, _):
        """ stores the setting before finishing the application
        """
        self.__storeSettings()
        try:
            self.dataFetcher.newDataName.disconnect(self.getNewData)
        except Exception as e:
            print(str(e))
        if self.hidraW.connected:
            self.hidraW.toggleServerConnection()
        time.sleep(min(dataFetchThread.GLOBALREFRESHRATE * 5, 2))
        self.disconnect_hidra()
        self.dataFetcher.stop()
        try:
            self.seccontext.destroy()
            # print("disconnect")
        except:
            pass

    def onfetchrois(self):
        if hcs.PYTANGO:
            if not self.doorname:
                self.doorname = self.sardana.getDeviceName("Door")
            rois = json.loads(self.sardana.getScanEnv(
                str(self.doorname), ["DetectorROIs"]))
            # print("rois %s" % rois)
            rlabel = str(self.imageW.labelROILineEdit.text())
            slabel = re.split(';|,| |\n', rlabel)
            slabel = [lb for lb in set(slabel) if lb]
            detrois = {}
            if "DetectorROIs" in rois and isinstance(
                    rois["DetectorROIs"], dict):
                detrois = rois["DetectorROIs"]
                if slabel:
                    detrois = dict(
                        (k, v) for k, v in detrois.items() if k in slabel)
            # print("detrois %s " % detrois)
            coords = []
            aliases = []
            for k, v in detrois.items():
                if isinstance(v, list):
                    for cr in v:
                        if isinstance(cr, list):
                            coords.append(cr)
                            aliases.append(k)
            slabel = []
            for i, al in enumerate(aliases):
                if len(set(aliases[i:])) == 1:
                    slabel.append(al)
                    break
                else:
                    slabel.append(al)
            self.imageW.labelROILineEdit.setText(" ".join(slabel))
            self.imageW.updateROIButton()
            self.imageW.roiNrChanged(len(coords), coords)
        else:
            print("Connection error")

    def onclearrois(self):
        if hcs.PYTANGO:
            if not self.doorname:
                self.doorname = self.sardana.getDeviceName("Door")
            # print(self.sardana.getScanEnv(
            #     str(self.doorname)), ["DetectorROIs"])
            rois = json.loads(self.sardana.getScanEnv(
                str(self.doorname), ["DetectorROIs"]))
            rlabel = str(self.imageW.labelROILineEdit.text())
            if rlabel:
                if "DetectorROIs" not in rois or not isinstance(
                        rois["DetectorROIs"], dict):
                    rois["DetectorROIs"] = {}
                if rlabel in rois["DetectorROIs"]:
                    rois["DetectorROIs"].pop(rlabel)
                # print("rois %s " % rois)
                self.sardana.setScanEnv(str(self.doorname), json.dumps(rois))
            if self.addrois:
                self.sardana.runMacro(
                    str(self.doorname), ["nxsrm", "%s" % rlabel])

        else:
            print("Connection error")

    def configuration(self):
        cnfdlg = configWidget.ConfigWidget(self)
        if not self.doorname:
            self.doorname = self.sardana.getDeviceName("Door")
        cnfdlg.door = self.doorname
        cnfdlg.addrois = self.addrois
        cnfdlg.showhisto = self.showhisto
        cnfdlg.secautoport = self.secautoport
        cnfdlg.secport = self.secport
        cnfdlg.secstream = self.secstream
        cnfdlg.refreshrate = dataFetchThread.GLOBALREFRESHRATE
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__updateConfig(cnfdlg)

    def __updateConfig(self, dialog):
        self.doorname = dialog.door
        self.addrois = dialog.addrois

        if self.showhisto != dialog.showhisto:
            self.levelsW.changeview(dialog.showhisto)
            self.showhisto = dialog.showhisto
        dataFetchThread.GLOBALREFRESHRATE = dialog.refreshrate
        if self.secstream != dialog.secstream or (
                self.secautoport != dialog.secautoport and dialog.secautoport):
            if self.secstream:
                self.secsocket.unbind(self.secsockopt)
                if self.hidraW.connected:
                    self.hidraW.connectSuccess(None)
            if dialog.secstream:
                if dialog.secautoport:
                    self.secsockopt = "tcp://*:*"
                    self.secsocket.bind(self.secsockopt)
                    dialog.secport = self.secsocket.getsockopt(
                        zmq.LAST_ENDPOINT).split(":")[-1]
                else:
                    self.secsockopt = "tcp://*:%s" % dialog.secport
                    self.secsocket.bind(self.secsockopt)
                if self.hidraW.connected:
                    self.hidraW.connectSuccess(dialog.secport)
        self.secautoport = dialog.secautoport
        self.secport = dialog.secport
        self.secstream = dialog.secstream

    def setSignalHost(self, signalhost):
        self._signalhost = signalhost

    def updateSource(self, status):
        if status:
            self.data_source = getattr(
                hcs, self.sourcetypes[status - 1]["datasource"])()
            self.dataFetcher.data_source = self.data_source
            if self._signalhost:
                self.data_source.setSignalHost(self._signalhost)
        self.update_state.emit(status)

    def plot(self):
        """ The main command of the live viewer class:
        draw a numpy array with the given name."""
        # prepare or preprocess the raw image if present:
        self.prepareImage()

        # perform transformation
        self.transform()

        # use the internal raw image to create a display image with chosen
        # scaling
        self.scale(self.scalingW.getCurrentScaling())

        # calculate and update the stats for this
        self.calc_update_stats()

        # calls internally the plot function of the plot widget
        self.imageW.plot(self.display_image, self.image_name)
        if self.updatehisto:
            self.levelsW.histogram.imageChanged(autoLevel=True)
            self.updatehisto = False

    def calc_update_stats_sec(self):
        self.calc_update_stats(secstream=False)

    def calc_update_stats(self, secstream=True):
        # calculate the stats for this
        maxVal, meanVal, varVal, minVal, maxRawVal = self.calcStats()
        calctime = time.time()
        currentscaling = self.scalingW.getCurrentScaling()
        # update the statistics display
        roiVal, currentroi = self.calcROIsum()
        roilabel = ""
        if currentroi >= 0:
            roilabel = "roi_%s sum: " % (currentroi + 1)
            slabel = []
            rlabel = str(self.imageW.labelROILineEdit.text())
            if rlabel:
                slabel = re.split(';|,| |\n', rlabel)
                slabel = [lb for lb in slabel if lb]
            if slabel:
                roilabel = "%s\n[%s]" % (
                    roilabel,
                    slabel[currentroi]
                    if currentroi < len(slabel) else slabel[-1])
        if secstream and self.secstream and self.display_image is not None:
            messagedata = {
                'command': 'alive', 'calctime': calctime, 'maxval': maxVal,
                'maxrawval': maxRawVal,
                'minval': minVal, 'meanval': meanVal, 'pid': self.apppid,
                'scaling': currentscaling}
            topic = 10001
            self.secsocket.send_string("%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii")))

        self.statsW.update_stats(
            meanVal, maxVal, varVal, currentscaling, roiVal, roilabel)

        # if needed, update the levels display
        if self.levelsW.isAutoLevel():
            self.levelsW.updateLevels(float(minVal), float(maxVal))

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
            print("No data source is defined, this will result in trouble.")
        if not self.data_source.connect():
            self.hidraW.connectFailure()
            print(
                "<WARNING> The HiDRA connection could not be established. "
                "Check the settings.")
        else:
            self.hidraW.connectSuccess(
                self.secport if self.secstream else None)
        if self.secstream:
            calctime = time.time()
            messagedata = {
                'command': 'start', 'calctime': calctime, 'pid': self.apppid}
            topic = 10001
            # print(str(messagedata))
            self.secsocket.send_string("%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii")))
        self.updatehisto = True

    # call the disconnect function of the hidra interface
    def disconnect_hidra(self):
        self.data_source.disconnect()
        if self.secstream:
            calctime = time.time()
            messagedata = {
                'command': 'stop', 'calctime': calctime, 'pid': self.apppid}
            # print(str(messagedata))
            topic = 10001
            self.secsocket.send_string("%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii")))
        # self.data_source = None

    def getNewData(self, name):
        # check if data is there at all
        if name == "__ERROR__":
            if self.interruptonerror:
                if self.hidraW.connected:
                    self.hidraW.toggleServerConnection()
                _, errortext = self.exchangelist.readData()
                messageBox.MessageBox.warning(
                    self, "lavue: Error in reading data",
                    "Viewing will be interrupted", str(errortext))
            return
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
        if self.raw_image is None:
            return
        self.display_image = self.raw_image

        if self.doBkgSubtraction and self.background_image is not None:
            # simple subtraction
            try:
                self.display_image = self.raw_image - self.background_image
            except:
                self.checkBKGSubtraction(False)
                self.background_image = None
                self.doBkgSubtraction = False
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "lavue: Background image does not match "
                    "to the current image")
                messageBox.MessageBox.warning(
                    self, "lavue: Background image does not match "
                    "to the current image",
                    text, str(value))

        # if self.applyImageMask and self.maskIndices is not None:
        # set all masked (non-zero values) to zero by index
        #     self.display_image[self.maskIndices] = 0

    def scale(self, scalingType):
        self.imageW.img_widget.scaling = scalingType
        if self.display_image is None:
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
        elif self.trafoName == "flip (ud)":
            self.display_image = np.fliplr(self.display_image)
        elif self.trafoName == "flip (lr)":
            self.display_image = np.flipud(self.display_image)
        elif self.trafoName == "transpose":
            self.display_image = np.transpose(self.display_image)
        elif self.trafoName == "rot90 (cw)":
            # self.display_image = np.rot90(self.display_image, 3)
            self.display_image = np.transpose(
                np.flipud(self.display_image))
        elif self.trafoName == "rot180":
            self.display_image = np.flipud(
                np.fliplr(self.display_image))
        elif self.trafoName == "rot270 (cw)":
            # self.display_image = np.rot90(self.display_image, 1)
            self.display_image = np.transpose(
                np.fliplr(self.display_image))
        elif self.trafoName == "rot180 + transpose":
            self.display_image = np.transpose(
                np.fliplr(np.flipud(self.display_image)))

    def calcROIsum(self):
        rid = self.imageW.img_widget.currentroi
        if self.display_image is not None:
            if self.imageW.img_widget.roienable:
                if rid >= 0:
                    image = self.display_image
                    roicoords = self.imageW.img_widget.roicoords
                    rcrds = list(roicoords[rid])
                    for i in [0, 2]:
                        if rcrds[i] > image.shape[0]:
                            rcrds[i] = image.shape[0]
                        elif rcrds[i] < -i / 2:
                            rcrds[i] = -i / 2
                    for i in [1, 3]:
                        if rcrds[i] > image.shape[1]:
                            rcrds[i] = image.shape[1]
                        elif rcrds[i] < - (i - 1) / 2:
                            rcrds[i] = - (i - 1) / 2
                    roival = np.sum(image[
                        int(rcrds[0]):(int(rcrds[2]) + 1),
                        int(rcrds[1]):(int(rcrds[3]) + 1)
                    ])
                else:
                    roival = 0.
            else:
                roival = 0.
            return str("%.4f" % roival), rid
        else:
            return "0.", rid

    def calcStats(self):
        if self.display_image is not None:
            maxval = np.amax(self.display_image)
            maxrawval = np.amax(self.raw_image)
            meanval = np.mean(self.display_image)
            varval = np.var(self.display_image)
            # automatic maximum clipping to hardcoded value
            checkval = meanval + 10 * np.sqrt(varval)
            if maxval > checkval:
                maxval = checkval
            return (str("%.4f" % maxval),
                    str("%.4f" % meanval),
                    str("%.4f" % varval),
                    str("%.3f" % np.amin(self.display_image)),
                    str("%.4f" % maxrawval))
        else:
            return "0.", "0.", "0.", "0.", "0."

    def getInitialLevels(self):
        if self.display_image is not None:
            return np.amin(self.display_image), np.amax(self.display_image)

    # def checkMasking(self, state):
    #   self.applyImageMask = state
    #   if self.applyImageMask and self.mask_image is None:
    #       self.maskW.noImage()

    # def prepareMasking(self, imagename):
    #     '''Get the mask image, select non-zero elements
    #        and store the indices.'''
    #     self.mask_image = imageFileHandler.ImageFileHandler(
    #         str(imagename)).getImage()
    #     self.maskIndices = np.nonzero(self.mask_image !=0)

    def checkBKGSubtraction(self, state):
        self.doBkgSubtraction = state
        if self.doBkgSubtraction and self.background_image is None:
            self.bkgSubW.setDisplayedName("")
        elif not state and self.bkgSubW.applyBkgSubtractBox.isChecked():
            self.bkgSubW.applyBkgSubtractBox.setChecked(False)
            self.bkgSubW.setDisplayedName("")
        self.imageW.img_widget.doBkgSubtraction = state

    def prepareBKGSubtraction(self, imagename):
        self.background_image = imageFileHandler.ImageFileHandler(
            str(imagename)).getImage()

    def setCurrentImageAsBKG(self):
        if self.raw_image is not None:
            self.background_image = self.raw_image
            self.bkgSubW.setDisplayedName(str(self.image_name))
        else:
            self.bkgSubW.setDisplayedName("")
        #  self.updatehisto = True

    def assessTransformation(self, trafoName):
        self.trafoName = trafoName
        self.plot()
