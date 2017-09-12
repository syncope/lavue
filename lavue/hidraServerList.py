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

'''A list of possible hidra servers. Take your pick.'''

HidraServerList = { "p03" : ['haspp03pilatus.desy.de'],
                    "p08" : ['haspp08pil100.desy.de'], 
                    "p09" : ['haspp09pilatus.desy.de'],
                    "p10" : ['hasp10pilatus'],
                    "p11" : ['haspp11pilatus.desy.de'],
                    "pool" : ['haspilatus300k.desy.de', 'haspilatus1m.desy.de', 'haso233det.desy.de']
                   }
