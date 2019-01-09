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

""" Live Viewer widgets """

from .release import __version__
import os

if "GNOME_DESKTOP_SESSION_ID" not in os.environ:
    os.environ["GNOME_DESKTOP_SESSION_ID"] = "qtconfig"
if os.path.isdir("/usr/lib/kde4/plugins/") and \
   "QT_PLUGIN_PATH" not in os.environ:
    os.environ["QT_PLUGIN_PATH"] = "/usr/lib/kde4/plugins/"


__all__ = ["__version__"]
