#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from setuptools import setup

with open('pynliner/__init__.py') as stream:
    content = stream.read()
    version_match = re.search("__version__\s*=\s*'(.*?)'\s+", content)

setup(name='pynliner',
      version=version_match.group(1),
      description='Python CSS-to-inline-styles conversion tool for HTML using'
                  ' BeautifulSoup and cssutils',
      author='Tanner Netterville',
      author_email='tannern@gmail.com',
      packages=['pynliner'],
      install_requires=[
          'BeautifulSoup4 >= 4.4.1',
          'cssutils >=0.9.7',
          'mock',
          'six'
      ],
      provides=['pynliner'])
