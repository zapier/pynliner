#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='pynliner',
      version='0.5.1.1.post2',
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
