#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='pynliner',
      version='0.5.1.1.post1',
      description='Python CSS-to-inline-styles conversion tool for HTML using'
                  ' BeautifulSoup and cssutils',
      author='Tanner Netterville',
      author_email='tannern@gmail.com',
      packages=['pynliner'],
      install_requires=[
          'BeautifulSoup >=3.2.1,<4.0',
          'cssutils >=0.9.7',
          'mock'
      ],
      provides=['pynliner'])
