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

""" setup.py for setting Lavue"""

from setuptools import setup
# from setuptools import find_packages

import codecs
import os

with codecs.open(os.path.join('.', 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# from sphinx.setup_command import BuildDoc

#: (:obj:`str`) package name
name = 'lavuelib'
lavuepackage = __import__(name)
#: (:obj:`str`) full release version
release = lavuepackage.__version__
#: (:obj:`str`) package version
version = ".".join(release.split(".")[:2])

#: (:obj:`dict` <:obj:`str`, :obj:`list` <:obj:`str`> > ) package data
package_data = {
    'lavuelib': ['ui/*.ui', 'qrc/*.rcc']
}

#: (:obj:`str`) .ui file directory
uidir = os.path.join(name, "ui")

#: (:obj:`dict` <:obj:`str`, `any`>) metadata for distutils
SETUPDATA = dict(
    name='lavue',
    version=release,
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
    packages=[name, uidir],
    package_data=package_data,
     # package_dir={'lauvelib': 'lavuelib'},
    include_package_data=True,
    scripts=['lavue', 'lavuemonitor', 'lavuezmqstreamfromtango'],
    zip_safe=False,
    # cmdclass={'build_sphinx': BuildDoc,},
    # command_options={
    #     'build_sphinx': {
    #         'project': ('setup.py', name),
    #         'version': ('setup.py', version),
    #         'release': ('setup.py', release)}},
)

## the main function
def main():
    setup(**SETUPDATA)

if __name__ == '__main__':
    main()
