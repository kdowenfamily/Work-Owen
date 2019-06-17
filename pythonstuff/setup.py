#!/usr/bin/env python

#from setuptools import setup 		# this is for setting up develop mode
from distutils.core import setup	# this is for installing


# This setup is suitable for "python setup.py develop".

setup(name='mymath',
      version='0.1',
      description='A silly math package',
      author='Dan Owen',
      author_email='odan8816@gmail.com',
      url='http://www.f5.com/',
      packages=['mymath', 'mymath.adv'],
)
