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

from distutils.core import setup
# from setuptools import setup
# from setuptools import find_packages

from codecs import open
from os import path

with open(path.join('.', 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# from sphinx.setup_command import BuildDoc

name = 'lavue'
version = '0'
release = '0.6.0'

setup(
    name='lavue',
    version='0.6.0',

    description='Live image viewer application for photon science detectors.',
    long_description=long_description,

    url='https://github.com/syncope/lavue',

    author='Ch.Rosemann, J.Kotanski, A.Rothkirch',
    author_email='christoph.rosemann@desy.de, '
    'jan.kotanski@desy.de, '
    'andre.rothkirch@desy.de ',

    license='GPLv2',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
    ],

    keywords='live viewer photon science detector',

    packages=['lavue', ],

    package_dir={'lauve': 'lavue', },

    #    include_package_data=True,

    scripts=['laVue'],

    # cmdclass={'build_sphinx': BuildDoc,},
    # command_options={
    #     'build_sphinx': {
    #         'project': ('setup.py', name),
    #         'version': ('setup.py', version),
    #         'release': ('setup.py', release)}},
)
