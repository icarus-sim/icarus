import unittest

import numpy as np

import icarus.tools.cacheperf as cacheperf
import icarus.models as cache
import icarus.tools.stats as stats


class TestNumericCacheHitRatio(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.n = 500
        cls.pdf = np.ones(cls.n) / cls.n

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_lru_cache(self):
        r = 0.1
        h = cacheperf.numeric_cache_hit_ratio(self.pdf, cache.LruCache(r * self.n))
        self.assertLess(np.abs(h - r), 0.01)

    def test_in_cache_lfu_cache(self):
        r = 0.1
        h = cacheperf.numeric_cache_hit_ratio(self.pdf, cache.InCacheLfuCache(r * self.n))
        self.assertLess(np.abs(h - r), 0.01)

    def test_fifo_cache(self):
        r = 0.1
        h = cacheperf.numeric_cache_hit_ratio(self.pdf, cache.FifoCache(r * self.n))
        self.assertLess(np.abs(h - r), 0.01)

    def test_rand_cache(self):
        r = 0.1
        h = cacheperf.numeric_cache_hit_ratio(self.pdf, cache.RandEvictionCache(r * self.n))
        self.assertLess(np.abs(h - r), 0.01)


class TestLaoutarisPerContentCacheHitRatio(unittest.TestCase):

    def test_3rd_order_positive_disc(self):
        H = cacheperf.laoutaris_per_content_cache_hit_ratio(0.8, 1000, 100, 3)
        for h in H:
            self.assertGreaterEqual(h, 0)
            self.assertLessEqual(h, 1)

    def test_3rd_order_negative_disc(self):
        H = cacheperf.laoutaris_per_content_cache_hit_ratio(0.7, 1000, 100, 3)
        for h in H:
            self.assertGreaterEqual(h, 0)
            self.assertLessEqual(h, 1)

class TestCheApproximation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.pdf = stats.TruncatedZipfDist(alpha=0.8, n=100).pdf
        cls.cache_size = 40

    def test_che_characteristic_time(self):
        T = cacheperf.che_characteristic_time(self.pdf, self.cache_size)
        for t in T:
            self.assertGreaterEqual(t, self.cache_size)

    def test_che_characteristic_time_simplified(self):
        t = cacheperf.che_characteristic_time_simplified(self.pdf, self.cache_size)
        self.assertGreaterEqual(t, self.cache_size)

    def test_che_cache_hit_ratio(self):
        h = cacheperf.che_cache_hit_ratio(self.pdf, self.cache_size)
        self.assertGreaterEqual(h, 0)
        self.assertLessEqual(h, 1)

    def test_che_cache_hit_ratio_simplified(self):
        h = cacheperf.che_cache_hit_ratio_simplified(self.pdf, self.cache_size)
        self.assertGreaterEqual(h, 0)
        self.assertLessEqual(h, 1)

    def test_che_per_content_cache_hit_ratio(self):
        H = cacheperf.che_per_content_cache_hit_ratio(self.pdf, self.cache_size)
        for h in H:
            self.assertGreaterEqual(h, 0)
            self.assertLessEqual(h, 1)

    def test_che_per_content_cache_hit_ratio_simplified(self):
        H = cacheperf.che_per_content_cache_hit_ratio_simplified(self.pdf, self.cache_size)
        for h in H:
            self.assertGreaterEqual(h, 0)
            self.assertLessEqual(h, 1)


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
