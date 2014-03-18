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


class TestLaoutarisCacheHitRatio(unittest.TestCase):
    
    def test_3rd_order_positive_disc(self):
        h = cacheperf.laoutaris_cache_hit_ratio(0.8, 1000, 100, 3)
        self.assertGreaterEqual(h, 0)
        
    def test_3rd_order_negative_disc(self):
        h = cacheperf.laoutaris_cache_hit_ratio(0.7, 1000, 100, 3)
        self.assertGreaterEqual(h, 0)
        

class TestOptimalCacheHitRatio(unittest.TestCase):
    
    def test_unsorted_pdf(self):
        h = cacheperf.optimal_cache_hit_ratio([0.1, 0.5, 0.4], 2)
        self.assertAlmostEqual(0.9, h)