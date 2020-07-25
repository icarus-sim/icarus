from __future__ import division

import pytest
import icarus.models as cache


class TestPathCache(object):

    def test_put_get(self):
        c = cache.PathCache([cache.LruCache(2) for _ in range(3)])
        assert len(c) == 3
        assert c.dump(serialized=False) == [[], [], []]
        c.put(1)
        assert c.dump(serialized=False) == [[1], [1], [1]]
        c.put(2)
        assert c.dump(serialized=False) == [[2, 1], [2, 1], [2, 1]]
        c.put(3)
        assert len(c) == 3
        assert c.dump(serialized=False) == [[3, 2], [3, 2], [3, 2]]
        assert c.get(2)
        assert len(c) == 3
        assert c.dump(serialized=False) == [[2, 3], [3, 2], [3, 2]]
        assert c.get(2)
        assert len(c) == 3
        assert c.dump(serialized=False) == [[2, 3], [3, 2], [3, 2]]
        c.put(4)
        assert len(c) == 3
        assert c.dump(serialized=False) == [[4, 2], [4, 3], [4, 3]]
        assert c.get(3)
        assert not c.get(1)
        assert c.dump(serialized=False) == [[3, 4], [3, 4], [4, 3]]

    def test_has(self):
        c = cache.PathCache([cache.LruCache(2) for _ in range(3)])
        c.put(2)
        assert c.dump(serialized=False) == [[2], [2], [2]]
        assert c.has(2)
        c.put(1)
        assert c.dump(serialized=False) == [[1, 2], [1, 2], [1, 2]]
        assert c.has(1)
        assert c.has(2)
        c.get(2)
        assert c.dump(serialized=False) == [[2, 1], [1, 2], [1, 2]]
        assert c.has(1)
        assert c.has(2)
        c.put(3)
        assert c.dump(serialized=False) == [[3, 2], [3, 1], [3, 1]]
        assert c.has(1)
        assert c.has(2)
        assert c.has(3)
        c.get(2)
        assert c.dump(serialized=False) == [[2, 3], [3, 1], [3, 1]]
        assert c.has(1)
        assert c.has(2)
        assert c.has(3)
        c.get(1)
        assert c.dump(serialized=False) == [[1, 2], [1, 3], [3, 1]]
        assert c.has(1)
        assert c.has(2)
        assert c.has(3)
        c.get(3)
        assert c.dump(serialized=False) == [[3, 1], [3, 1], [3, 1]]
        assert c.has(1)
        assert not c.has(2)
        assert c.has(3)


class TestTreeCache(object):

    def test_put_get(self):
        c = cache.TreeCache([cache.LruCache(2) for _ in range(2)],
                            cache.LruCache(2))
        assert not c.get(1)
        c.put(1)
        leaf_0, leaf_1, root = [(1 in i) for i in c.dump(serialized=False)]
        assert root
        # Assert that item is in leaf 0 XOR leaf 1
        assert (leaf_0 and not leaf_1) or (not leaf_0 and leaf_1)
        assert c.get(1)

    def test_no_read_through(self):
        c = cache.TreeCache([cache.LruCache(2) for _ in range(2)],
                            cache.LruCache(2))
        with pytest.raises(ValueError):
            c.put(1)


class TestArrayCache(object):

    def test_put_get(self):
        c = cache.ArrayCache([cache.LruCache(2) for _ in range(2)])
        assert not c.get(1)
        c.put(1)
        c_0, c_1 = [(1 in i) for i in c.dump(serialized=False)]
        # Assert that item is in leaf 0 XOR leaf 1
        assert (c_0 and not c_1) or (not c_0 and c_1)
        if not c.get(1):
            c.put(1)
            assert c.dump(serialized=False) == [[1], [1]]

    def test_no_read_through(self):
        c = cache.ArrayCache([cache.LruCache(2) for _ in range(2)])
        with pytest.raises(ValueError):
            c.put(1)

    def test_incorrect_weights(self):
        # Weight not summing up to 1
        array = [cache.LruCache(2) for _ in range(2)]
        with pytest.raises(ValueError):
            cache.ArrayCache(array, weights=[0.8, 0.1])
            cache.ArrayCache(array, weights=[0.8, 0.3])
            # Number of weights not matching with number of nodes
            cache.ArrayCache(array, weights=[1.0])
            cache.ArrayCache(array, weights=[0.8, 0.1, 0.1])


class TestShardedCache(object):

    def test_put_get_has(self):
        c = cache.ShardedCache(6, 'LRU', 3, f_map=lambda x: x % 3)
        c.put(4)
        assert c.dump(serialized=False) == [[], [4], []]
        assert c.has(4)
        assert c.get(4)
        c.put(1)
        assert c.dump(serialized=False) == [[], [1, 4], []]
        assert c.has(1)
        assert c.get(1)
        assert c.has(4)
        c.put(7)
        assert c.dump(serialized=False) == [[], [7, 1], []]
        assert c.has(7)
        assert c.get(7)
        assert c.has(1)
        assert c.get(1)
        assert not c.has(4)
        assert not c.get(4)

    def test_put_get_scan(self):
        c = cache.ShardedCache(6, 'LRU', 3, f_map=lambda x: x % 3)
        assert c.put(0) == None
        assert c.dump(serialized=False) == [[0], [], []]
        assert c.put(1) == None
        assert c.dump(serialized=False) == [[0], [1], []]
        assert c.put(2) == None
        assert c.dump(serialized=False) == [[0], [1], [2]]
        c.put(3)
        assert c.dump(serialized=False) == [[3, 0], [1], [2]]
        c.put(4)
        assert c.dump(serialized=False) == [[3, 0], [4, 1], [2]]
        c.put(5)
        assert c.dump(serialized=False) == [[3, 0], [4, 1], [5, 2]]
        assert c.put(6) == 0
        assert c.dump(serialized=False) == [[6, 3], [4, 1], [5, 2]]
        assert c.put(7) == 1
        assert c.dump(serialized=False) == [[6, 3], [7, 4], [5, 2]]
        assert c.put(8) == 2
        assert c.dump(serialized=False) == [[6, 3], [7, 4], [8, 5]]

    def test_remove(self):
        c = cache.ShardedCache(6, 'LRU', 3, f_map=lambda x: x % 3)
        assert c.dump(serialized=False) == [[], [], []]
        c.put(0)
        assert c.dump(serialized=False) == [[0], [], []]
        c.remove(0)
        assert c.dump(serialized=False) == [[], [], []]
