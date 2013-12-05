import sys
if sys.version_info[:2] >= (2, 7):
    import unittest
else:
    try:
        import unittest2 as unittest
    except ImportError:
        raise ImportError("The unittest2 package is needed to run the tests.") 
del sys

from icarus.tools import TruncatedZipfDist
import icarus.tools as cacheperf


class TestNumericCacheHitRatio(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass
        
    @classmethod
    def tearDownClass(cls):
        pass
    
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def test_lru_cache(self):
        pass

    def test_lfu_cache(self):
        pass


