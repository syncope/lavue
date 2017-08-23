from setuptools import setup, find_packages

from codecs import open
from os import path

with open(path.join('.', 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

from sphinx.setup_command import BuildDoc

name='lavue'
version='0'
release='0.1.0'

setup(
    name='lavue',
    version='0.1.0.dev',

    description='Live image viewer application for photon science detectors.', 
    long_description=long_description,

    url='https://github.com/syncope/lavue',

    author='Ch.Rosemann',
    author_email='christoph.rosemann@desy.de',
    
    license='GPLv2',
    
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 2.7',
        #~ 'Programming Language :: Python :: 3',
        #~ 'Programming Language :: Python :: 3.4',
        #~ 'Programming Language :: Python :: 3.5',
    ],

    keywords='live viewer photon science detector',
    
    packages=['lavue',],
    
    package_dir = { 'lauve':'lavue',},
    
    include_package_data=True,
    
    scripts=['bin/laVue',],
    
    #~ cmdclass={'build_sphinx': BuildDoc,},
    #~ command_options={
        #~ 'build_sphinx': {
            #~ 'project': ('setup.py', name),
            #~ 'version': ('setup.py', version),
            #~ 'release': ('setup.py', release)}},
)

