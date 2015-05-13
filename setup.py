#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

from arturo import __version__, __app_name__, __lib_name__


install_requires = open("requirements.txt").read().split('\n')
readme_content = open("README.md").read()

def gen_data_files(package_dir, subdir):
    import os.path
    results = []
    for root, dirs, files in os.walk(os.path.join(package_dir, subdir)):  # @UnusedVariable
        results.extend([os.path.join(root, f)[len(package_dir)+1:] for f in files])
    return results

package_data =  gen_data_files(__lib_name__, 'commands') + \
                gen_data_files(__lib_name__, 'templates') + \
                gen_data_files(__lib_name__, 'i18n')

setup(
    name=__lib_name__,
    version=__version__,
    description='Command line toolkit for working with Arduino hardware',
    long_description=readme_content,
    author='Victor Nakoryakov, Amperka Team: Scott Dixon, Arturo Team',
    author_email='scottd.nerd+arturo@gmail.com',
    license='MIT',
    keywords="arduino build system",
    url='http://32bits.io/Arturo',
    packages=[__lib_name__, __lib_name__ + '.commands', __lib_name__ + '.templates', __lib_name__ + '.i18n'],
    scripts=['bin/' + __app_name__],
    package_data={__lib_name__: package_data},
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Embedded Systems",
    ],
)
