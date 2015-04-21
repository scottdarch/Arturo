#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from ano import __version__, __app_name__

install_requires = open("requirements.txt").read().split('\n')
readme_content = open("README.md").read()

def gen_data_files(package_dir, subdir):
    import os.path
    results = []
    for root, dirs, files in os.walk(os.path.join(package_dir, subdir)):  # @UnusedVariable
        results.extend([os.path.join(root, f)[len(package_dir)+1:] for f in files])
    return results

ano_package_data = gen_data_files('ano', 'make') + \
                   gen_data_files('ano', 'templates') + \
                   gen_data_files('ano', 'Arturo2/templates') + \
                   gen_data_files('ano', 'i18n')

setup(
    name=__app_name__,
    version=__version__,
    description='Command line toolkit for working with Arduino hardware',
    long_description=readme_content,
    author='Victor Nakoryakov, Amperka Team: Scott Dixon, Arturo Team',
    author_email='scottd.nerd+arturo@gmail.com',
    license='MIT',
    keywords="arduino build system",
    url='http://32bits.io/Arturo',
    packages=['ano', 'ano.commands', 'ano.Arturo2', 'ano.Arturo2.templates', 'ano.Arturo2.commands'],
    scripts=['bin/ano'],
    package_data={'ano': ano_package_data},
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Embedded Systems",
    ],
)
