#!/usr/bin/env python

from setuptools import setup

setup(name='target-intercom',
      version='0.0.1',
      description='Singer.io target for pushing data to Intercom',
      author='Brian Sloane',
      url='https://singer.io',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      py_modules=['target_intercom'],
      install_requires=[
          'jsonschema==2.6.0',
          'singer-python==2.1.4',
          'python-intercom==3.1.0'
      ],
      entry_points='''
          [console_scripts]
          target-intercom=target_intercom:main
      ''',
)
