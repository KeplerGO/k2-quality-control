#!/usr/bin/env python
import os
import sys
from setuptools import setup

if "publish" in sys.argv[-1]:
    os.system("python setup.py sdist upload -r pypi")
    sys.exit()
elif "testpublish" in sys.argv[-1]:
    os.system("python setup.py sdist upload -r pypitest")
    sys.exit()

# Load the __version__ variable without importing the package
exec(open('k2qc/version.py').read())

entry_points = {'console_scripts':
                ['k2qc = k2qc:k2qc_main',
                 'k2qc-flags = k2qc.flags:k2qc_flags_main']}

setup(name='k2qc',
      version=__version__,
      description='Automated quality control of Kepler/K2 '
                  'Target Pixel and Lightcurve Files.',
      author='Geert Barentsen',
      author_email='hello@geert.io',
      url='https://github.com/barentsen/k2qc',
      packages=['k2qc'],
      install_requires=['astropy>=1.0',
                        'numpy',
                        'tqdm',
                        'click'],
      entry_points=entry_points,
      classifiers=[
          "Development Status :: 4 - Beta",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Intended Audience :: Science/Research",
          "Topic :: Scientific/Engineering :: Astronomy",
          ],
      )
