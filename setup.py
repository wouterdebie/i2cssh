#! /usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
    from setuptools.command.test import test as TestCommand
except ImportError:
    from distutils.core import setup
    from distutils.cmd import Command as TestCommand

import sys


install_requires = [
    'iterm2==2.6',
    'click==8.1.3',
    'PyYAML==6.0',
    'click-option-group==0.5.3']

setup(
    name='i2cssh',
    version='0.0.3',
    author=u'Wouter de Bie',
    author_email='wouter@evenflow.nl',
    description='csshX like ssh tool for iTerm2',
    url='http://github.com/wouterdebie/i2cssh',
    scripts=['i2cssh'],
    license='MIT',
    keywords='ssh i2cssh csshX'.split(),
    classifiers=[
        'Topic :: Utilities',
        'Programming Language :: Python',
        'Operating System :: MacOS'
    ],

    install_requires=install_requires,
)
