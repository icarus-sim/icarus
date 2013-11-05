import sys
if sys.version_info[:2] < (2, 6):
    m = "Python version 2.6 or later is required for Icarus (%d.%d detected)."
    raise ImportError(m % sys.version_info[:2])
del sys


# Author information
__author__ = 'Lorenzo Saino, Ioannis Psaras'

# Version information
__version__ = '0.1-icn13'

# License information
___license___ = 'GNU GPLv2'