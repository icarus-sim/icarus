from __future__ import division
import unittest

import icarus.models as cache


class TestPathCache(unittest.TestCase):

    def test_put_get(self):
        c = cache.PathCache([cache.LruCache(2) for _ in range(3)])
        self.assertEqual(len(c), 3)
        self.assertEqual(c.dump(serialized=False), [[], [], []])
        c.put(1)
        self.assertEqual(c.dump(serialized=False), [[1], [1], [1]])
        c.put(2)
        self.assertEqual(c.dump(serialized=False), [[2, 1], [2, 1], [2, 1]])
        c.put(3)
        self.assertEqual(len(c), 3)
        self.assertEqual(c.dump(serialized=False), [[3, 2], [3, 2], [3, 2]])
        self.assertTrue(c.get(2))
        self.assertEqual(len(c), 3)
        self.assertEqual(c.dump(serialized=False), [[2, 3], [3, 2], [3, 2]])
        self.assertTrue(c.get(2))
        self.assertEqual(len(c), 3)
        self.assertEqual(c.dump(serialized=False), [[2, 3], [3, 2], [3, 2]])
        c.put(4)
        self.assertEqual(len(c), 3)
        self.assertEqual(c.dump(serialized=False), [[4, 2], [4, 3], [4, 3]])
        self.assertTrue(c.get(3))
        self.assertFalse(c.get(1))
        self.assertEqual(c.dump(serialized=False), [[3, 4], [3, 4], [4, 3]])

    def test_has(self):
        c = cache.PathCache([cache.LruCache(2) for _ in range(3)])
        c.put(2)
        self.assertEqual(c.dump(serialized=False), [[2], [2], [2]])
        self.assertTrue(c.has(2))
        c.put(1)
        self.assertEqual(c.dump(serialized=False), [[1, 2], [1, 2], [1, 2]])
        self.assertTrue(c.has(1))
        self.assertTrue(c.has(2))
        c.get(2)
        self.assertEqual(c.dump(serialized=False), [[2, 1], [1, 2], [1, 2]])
        self.assertTrue(c.has(1))
        self.assertTrue(c.has(2))
        c.put(3)
        self.assertEqual(c.dump(serialized=False), [[3, 2], [3, 1], [3, 1]])
        self.assertTrue(c.has(1))
        self.assertTrue(c.has(2))
        self.assertTrue(c.has(3))
        c.get(2)
        self.assertEqual(c.dump(serialized=False), [[2, 3], [3, 1], [3, 1]])
        self.assertTrue(c.has(1))
        self.assertTrue(c.has(2))
        self.assertTrue(c.has(3))
        c.get(1)
        self.assertEqual(c.dump(serialized=False), [[1, 2], [1, 3], [3, 1]])
        self.assertTrue(c.has(1))
        self.assertTrue(c.has(2))
        self.assertTrue(c.has(3))
        c.get(3)
        self.assertEqual(c.dump(serialized=False), [[3, 1], [3, 1], [3, 1]])
        self.assertTrue(c.has(1))
        self.assertFalse(c.has(2))
        self.assertTrue(c.has(3))


class TestTreeCache(unittest.TestCase):

    def test_put_get(self):
        c = cache.TreeCache([cache.LruCache(2) for _ in range(2)],
                            cache.LruCache(2))
        self.assertFalse(c.get(1))
        c.put(1)
        leaf_0, leaf_1, root = [(1 in i) for i in c.dump(serialized=False)]
        self.assertTrue(root)
        # Assert that item is in leaf 0 XOR leaf 1
        self.assertTrue((leaf_0 and not leaf_1) or (not leaf_0 and leaf_1))
        self.assertTrue(c.get(1))

    def test_no_read_through(self):
        c = cache.TreeCache([cache.LruCache(2) for _ in range(2)],
                            cache.LruCache(2))
        self.assertRaises(ValueError, c.put, 1)


class TestArrayCache(unittest.TestCase):

    def test_put_get(self):
        c = cache.ArrayCache([cache.LruCache(2) for _ in range(2)])
        self.assertFalse(c.get(1))
        c.put(1)
        c_0, c_1 = [(1 in i) for i in c.dump(serialized=False)]
        # Assert that item is in leaf 0 XOR leaf 1
        self.assertTrue((c_0 and not c_1) or (not c_0 and c_1))
        if not c.get(1):
            c.put(1)
            self.assertEqual(c.dump(serialized=False), [[1], [1]])

    def test_no_read_through(self):
        c = cache.ArrayCache([cache.LruCache(2) for _ in range(2)])
        self.assertRaises(ValueError, c.put, 1)

    def test_incorrect_weights(self):
        # Weight not summing up to 1
        self.assertRaises(ValueError,
                          cache.ArrayCache,
                          [cache.LruCache(2) for _ in range(2)],
                          weights=[0.8, 0.1])
        self.assertRaises(ValueError,
                          cache.ArrayCache,
                          [cache.LruCache(2) for _ in range(2)],
                          weights=[0.8, 0.3])
        # Number of weights not matching with number of nodes
        self.assertRaises(ValueError,
                          cache.ArrayCache,
                          [cache.LruCache(2) for _ in range(2)],
                          weights=[1.0])
        self.assertRaises(ValueError,
                          cache.ArrayCache,
                          [cache.LruCache(2) for _ in range(2)],
                          weights=[0.8, 0.1, 0.1])


class TestShardedCache(unittest.TestCase):

    def test_put_get_has(self):
        c = cache.ShardedCache(6, 'LRU', 3, f_map=lambda x: x % 3)
        c.put(4)
        self.assertEqual(c.dump(serialized=False), [[], [4], []])
        self.assertTrue(c.has(4))
        self.assertTrue(c.get(4))
        c.put(1)
        self.assertEqual(c.dump(serialized=False), [[], [1, 4], []])
        self.assertTrue(c.has(1))
        self.assertTrue(c.get(1))
        self.assertTrue(c.has(4))
        c.put(7)
        self.assertEqual(c.dump(serialized=False), [[], [7, 1], []])
        self.assertTrue(c.has(7))
        self.assertTrue(c.get(7))
        self.assertTrue(c.has(1))
        self.assertTrue(c.get(1))
        self.assertFalse(c.has(4))
        self.assertFalse(c.get(4))

    def test_put_get_scan(self):
        c = cache.ShardedCache(6, 'LRU', 3, f_map=lambda x: x % 3)
        self.assertEqual(c.put(0), None)
        self.assertEqual(c.dump(serialized=False), [[0], [], []])
        self.assertEqual(c.put(1), None)
        self.assertEqual(c.dump(serialized=False), [[0], [1], []])
        self.assertEqual(c.put(2), None)
        self.assertEqual(c.dump(serialized=False), [[0], [1], [2]])
        c.put(3)
        self.assertEqual(c.dump(serialized=False), [[3, 0], [1], [2]])
        c.put(4)
        self.assertEqual(c.dump(serialized=False), [[3, 0], [4, 1], [2]])
        c.put(5)
        self.assertEqual(c.dump(serialized=False), [[3, 0], [4, 1], [5, 2]])
        self.assertEqual(c.put(6), 0)
        self.assertEqual(c.dump(serialized=False), [[6, 3], [4, 1], [5, 2]])
        self.assertEqual(c.put(7), 1)
        self.assertEqual(c.dump(serialized=False), [[6, 3], [7, 4], [5, 2]])
        self.assertEqual(c.put(8), 2)
        self.assertEqual(c.dump(serialized=False), [[6, 3], [7, 4], [8, 5]])

    def test_remove(self):
        c = cache.ShardedCache(6, 'LRU', 3, f_map=lambda x: x % 3)
        self.assertEqual(c.dump(serialized=False), [[], [], []])
        c.put(0)
        self.assertEqual(c.dump(serialized=False), [[0], [], []])
        c.remove(0)
        self.assertEqual(c.dump(serialized=False), [[], [], []])
