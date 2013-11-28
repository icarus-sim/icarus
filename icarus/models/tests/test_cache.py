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

    def test_rand(self):
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
        rc1 = cache.LruCache(n)
        rc2 = cache.LruCache(n)
        cache.set_rand_insert(rc1, p1)
        cache.set_rand_insert(rc2, p2)
        for i in range(n):
            rc1.put(i)
            rc2.put(i)
        self.assertTrue(len(rc1) - n*p1 < 100)
        self.assertTrue(len(rc2) - n*p2 < 100)
