"""Setup script"""
import sys
import os
from shutil import rmtree

from setuptools import find_packages, setup

# Packages required to run Icarus
requires = [
    'networkx (>=2.0)',
    'numpy (>=1.4)',
    'scipy (>=0.16)',
    'fnss (>=0.9.0)',
    'matplotlib (>=1.5.3)',
    'python-dateutil (>=2.5.3)',
    'click (>=6.6)'
]

# It imports release module this way because if it tried to import icarus package
# and some required dependencies were not installed, that would fail
# This is the only way to access the release module without needing all
# dependencies.
sys.path.insert(0, 'icarus')
import release
sys.path.pop(0)

# Clean tasks
if os.path.exists('MANIFEST'): os.remove('MANIFEST')
if os.path.exists('icarus.egg-info'): rmtree('icarus.egg-info')


# Main scripts
if __name__ == "__main__":
    setup(
        name='icarus',
        version=release.version,
        author=release.author,
        author_email=release.author_email,
        packages=find_packages(),
        url=release.url,
        download_url=release.download_url,
        license=release.license_long,
        classifiers=[
             'Development Status :: 5 - Production/Stable',
             'Intended Audience :: Developers',
             'Intended Audience :: Science/Research',
             'Intended Audience :: Telecommunications Industry',
             'License :: OSI Approved :: BSD License',
             'Natural Language :: English',
             'Operating System :: OS Independent',
             'Programming Language :: Python :: 2',
             'Programming Language :: Python :: 2.7',
             'Programming Language :: Python :: 3',
             'Programming Language :: Python :: 3.5',
             'Programming Language :: Python :: 3.6',
             'Programming Language :: Python :: 3.7',
             'Programming Language :: Python :: 3.8',
             'Topic :: Scientific/Engineering',
        ],
        entry_points={'console_scripts': {"{0} = {0}.main:main".format('icarus')}},
        description=release.description_short,
        long_description=release.description_long,
        python_requires='>=2.7.9, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
        install_requires=requires,
        keywords=[
            'caching',
            'simulation',
            'Information-Centric Networking',
            'Content Delivery Networks',
        ],
    )
