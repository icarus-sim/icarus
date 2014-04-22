import sys
if sys.version_info[:2] >= (2, 7):
    import unittest
else:
    try:
        import unittest2 as unittest
    except ImportError:
        raise ImportError("The unittest2 package is needed to run the tests.") 
del sys

import icarus.models as cache

class TestLruCache(unittest.TestCase):

    def test_lru(self):
        c = cache.LruCache(4)
        c.put(1)
        self.assertEquals(len(c), 1)
        c.put(2)
        self.assertEquals(len(c), 2)
        c.put(3)
        self.assertEquals(len(c), 3)
        c.put(4)
        self.assertEquals(len(c), 4)
        self.assertEquals(c.dump(), [4, 3, 2, 1])
        c.put(5)
        self.assertEquals(len(c), 4)
        self.assertEquals(c.dump(), [5, 4, 3, 2])
        c.get(2)
        self.assertEquals(c.dump(), [2, 5, 4, 3])
        c.get(4)
        self.assertEquals(c.dump(), [4, 2, 5, 3])
        c.clear()
        self.assertEquals(len(c), 0)
        self.assertEquals(c.dump(), [])
    

class TestFifoCache(unittest.TestCase):

    def test_fifo(self):
        c = cache.FifoCache(4)
        self.assertEquals(len(c), 0)
        c.put(1)
        self.assertEquals(len(c), 1)
        c.put(2)
        self.assertEquals(len(c), 2)
        c.put(3)
        self.assertEquals(len(c), 3)
        c.put(4)
        self.assertEquals(len(c), 4)
        self.assertEquals(c.dump(), [4, 3, 2, 1])
        c.put(5)
        self.assertEquals(len(c), 4)
        self.assertEquals(c.dump(), [5, 4, 3, 2])
        c.get(2)
        self.assertEquals(c.dump(), [5, 4, 3, 2])
        c.get(4)
        self.assertEquals(c.dump(), [5, 4, 3, 2])
        c.put(6)
        self.assertEquals(c.dump(), [6, 5, 4, 3])
        c.clear()
        self.assertEquals(len(c), 0)
        self.assertEquals(c.dump(), [])
    

class TestRandCache(unittest.TestCase):
    
    def test_rand(self):
        c = cache.RandCache(4)
        self.assertEquals(len(c), 0)
        c.put(1)
        self.assertEquals(len(c), 1)
        c.put(2)
        self.assertEquals(len(c), 2)
        c.put(3)
        self.assertEquals(len(c), 3)
        c.put(4)
        self.assertEquals(len(c), 4)
        self.assertEquals(len(c.dump()), 4)
        for v in (1, 2, 3, 4):
            self.assertTrue(c.has(v))
        c.get(3)
        for v in (1, 2, 3, 4):
            self.assertTrue(c.has(v))
        c.put(5)
        self.assertEquals(len(c), 4)
        self.assertTrue(c.has(5))
        c.clear()
        self.assertEquals(len(c), 0)
        self.assertEquals(c.dump(), [])


class TestLfuCache(unittest.TestCase):

    def test_lfu(self):
        c = cache.LfuCache(4)
        self.assertEquals(len(c), 0)
        c.put(1)
        self.assertEquals(len(c), 1)
        c.put(2)
        self.assertEquals(len(c), 2)
        c.put(3)
        self.assertEquals(len(c), 3)
        c.put(4)
        self.assertEquals(len(c), 4)
        self.assertEquals(len(c.dump()), 4)
        for v in (1, 2, 3, 4):
            self.assertTrue(c.has(v))
        c.get(1)
        c.get(1)
        c.get(1)
        c.get(2)
        c.get(2)
        c.get(3)
        c.put(5)
        self.assertEquals(c.dump(), [1, 2, 3, 5])
        self.assertEquals(len(c), 4)
        self.assertTrue(c.has(5))
        c.clear()
        self.assertEquals(len(c), 0)
        self.assertEquals(c.dump(), [])
        
        
class TestRandInsert(unittest.TestCase):
    
    def test_rand_insert(self):
        n = 100000
        p1 = 0.01
        p2 = 0.1
        rc1 = cache.rand_insert_cache(cache.LruCache(n), p1)
        rc2 = cache.rand_insert_cache(cache.LruCache(n), p2)
        for i in range(n):
            rc1.put(i)
            rc2.put(i)
        self.assertLess(len(rc1) - n*p1, 200)
        self.assertLess(len(rc2) - n*p2, 200)
        self.assertEqual(rc1.put.__name__, 'put')
        self.assertGreater(len(rc1.put.__doc__), 0)


class TestKetValCache(unittest.TestCase):
    
    def test_key_val_cache(self):
        c = cache.keyval_cache(cache.FifoCache(3))
        c.put(1,11)
        self.assertEqual(c.get(1), 11)
        c.put(1, 12)
        self.assertEqual(c.get(1), 12)
        self.assertEqual(c.dump(), [(1, 12)])
        c.put(2, 21)
        self.assertTrue(c.has(1))
        self.assertTrue(c.has(2))
        c.put(3, 31)
        k, v = c.put(4, 41)
        self.assertEqual((k, v), (1, 12))
        c.clear()
        self.assertEqual(len(c), 0)
        self.assertEqual(c.get.__name__, 'get')
        self.assertEqual(c.put.__name__, 'put')
        self.assertEqual(c.dump.__name__, 'dump')
        self.assertEqual(c.clear.__name__, 'clear')