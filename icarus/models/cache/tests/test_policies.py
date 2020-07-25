from __future__ import division
import collections

import numpy as np
import pytest

import icarus.models as cache


class TestLinkedSet(object):

    def link_consistency(self, linked_set):
        """
        Checks that links of a linked set are consistent iterating from top
        or from bottom.

        This method depends on the internal implementation of the LinkedSet
        class
        """
        topdown = collections.deque()
        bottomup = collections.deque()
        cur = linked_set._top
        while cur:
            topdown.append(cur.val)
            cur = cur.down
        cur = linked_set._bottom
        while cur:
            bottomup.append(cur.val)
            cur = cur.up
        bottomup.reverse()
        if topdown != bottomup:
            return False
        return list(reversed(list(linked_set))) == list(reversed(linked_set))

    def test_append_top(self):
        c = cache.LinkedSet()
        c.append_top(1)
        assert len(c) == 1
        assert list(c) == [1]
        c.append_top(2)
        assert len(c) == 2
        assert list(c) == [2, 1]
        c.append_top(3)
        assert len(c) == 3
        assert list(c) == [3, 2, 1]
        assert self.link_consistency(c)
        with pytest.raises(KeyError):
            c.append_top(2)

    def test_append_bottom(self):
        c = cache.LinkedSet()
        c.append_bottom(1)
        assert len(c) == 1
        assert list(c) == [1]
        c.append_bottom(2)
        assert len(c) == 2
        assert list(c) == [1, 2]
        c.append_bottom(3)
        assert len(c) == 3
        assert list(c) == [1, 2, 3]
        assert self.link_consistency(c)
        with pytest.raises(KeyError):
            c.append_top(2)

    def test_move_to_top(self):
        c = cache.LinkedSet()
        c.append_top(1)
        c.move_to_top(1)
        assert list(c) == [1]
        c.append_bottom(2)
        c.move_to_top(1)
        assert list(c) == [1, 2]
        c.move_to_top(2)
        assert list(c) == [2, 1]
        c.append_bottom(3)
        c.move_to_top(1)
        assert list(c) == [1, 2, 3]
        assert self.link_consistency(c)

    def test_move_to_bottom(self):
        c = cache.LinkedSet()
        c.append_top(1)
        c.move_to_bottom(1)
        assert list(c) == [1]
        c.append_bottom(2)
        c.move_to_bottom(2)
        assert list(c) == [1, 2]
        c.move_to_bottom(1)
        assert list(c) == [2, 1]
        c.append_top(3)
        c.move_to_bottom(1)
        assert list(c) == [3, 2, 1]
        assert self.link_consistency(c)

    def test_move_up(self):
        c = cache.LinkedSet()
        c.append_bottom(1)
        c.move_up(1)
        assert list(c) == [1]
        c.append_bottom(2)
        c.move_up(1)
        assert list(c) == [1, 2]
        c.move_up(2)
        assert list(c) == [2, 1]
        c.append_bottom(3)
        c.move_up(3)
        assert list(c) == [2, 3, 1]
        c.move_up(3)
        assert list(c) == [3, 2, 1]
        assert self.link_consistency(c)
        with pytest.raises(KeyError):
            c.move_up(4)

    def test_move_down(self):
        c = cache.LinkedSet()
        c.append_top(1)
        c.move_down(1)
        assert list(c) == [1]
        c.append_top(2)
        c.move_down(1)
        assert list(c) == [2, 1]
        c.move_down(2)
        assert list(c) == [1, 2]
        c.move_down(2)
        assert list(c) == [1, 2]
        c.append_top(3)
        assert list(c) == [3, 1, 2]
        c.move_down(3)
        assert list(c) == [1, 3, 2]
        c.move_down(3)
        assert list(c) == [1, 2, 3]
        assert self.link_consistency(c)
        with pytest.raises(KeyError):
            c.move_down(4)

    def test_pop_top(self):
        c = cache.LinkedSet([1, 2, 3])
        evicted = c.pop_top()
        assert evicted == 1
        assert list(c) == [2, 3]
        assert self.link_consistency(c)
        evicted = c.pop_top()
        assert evicted == 2
        assert list(c) == [3]
        assert self.link_consistency(c)
        evicted = c.pop_top()
        assert evicted == 3
        assert list(c) == []
        evicted = c.pop_top()
        assert evicted == None
        assert list(c) == []

    def test_pop_bottom(self):
        c = cache.LinkedSet([1, 2, 3])
        evicted = c.pop_bottom()
        assert evicted == 3
        assert list(c) == [1, 2]
        assert self.link_consistency(c)
        evicted = c.pop_bottom()
        assert evicted == 2
        assert list(c) == [1]
        assert self.link_consistency(c)
        evicted = c.pop_bottom()
        assert evicted == 1
        assert list(c) == []
        evicted = c.pop_bottom()
        assert evicted == None
        assert list(c) == []

    def test_insert_above(self):
        c = cache.LinkedSet([3])
        c.insert_above(3, 2)
        assert list(c) == [2, 3]
        assert self.link_consistency(c)
        c.insert_above(2, 1)
        assert list(c) == [1, 2, 3]
        assert self.link_consistency(c)
        c.insert_above(1, 'a')
        assert list(c) == ['a', 1, 2, 3]
        assert self.link_consistency(c)
        c.insert_above(2, 'b')
        assert list(c) == ['a', 1, 'b', 2, 3]
        assert self.link_consistency(c)
        c.insert_above(3, 'c')
        assert list(c) == ['a', 1, 'b', 2, 'c', 3]
        assert self.link_consistency(c)

    def test_insert_below(self):
        c = cache.LinkedSet([1])
        c.insert_below(1, 2)
        assert list(c) == [1, 2]
        assert self.link_consistency(c)
        c.insert_below(2, 3)
        assert list(c) == [1, 2, 3]
        assert self.link_consistency(c)
        c.insert_below(1, 'a')
        assert list(c) == [1, 'a', 2, 3]
        assert self.link_consistency(c)
        c.insert_below(2, 'b')
        assert list(c) == [1, 'a', 2, 'b', 3]
        assert self.link_consistency(c)
        c.insert_below(3, 'c')
        assert list(c) == [1, 'a', 2, 'b', 3, 'c']
        assert self.link_consistency(c)

    def test_clear(self):
        c = cache.LinkedSet()
        c.append_top(1)
        c.append_top(2)
        assert len(c) == 2
        c.clear()
        assert len(c) == 0
        assert list(c) == []
        c.clear()

    def test_duplicated_elements(self):
        with pytest.raises(ValueError):
            cache.LinkedSet(iterable=[1, 1, 2])
            cache.LinkedSet(iterable=[1, None, None])
        assert cache.LinkedSet(iterable=[1, 0, None]) is not None


class TestCache(object):

    def test_do(self):
        c = cache.FifoCache(2)
        assert len(c) == 0
        c.do('PUT', 1)
        assert len(c) == 1
        c.do('UPDATE', 1)
        assert len(c) == 1
        assert c.do('GET', 1)
        c.do('PUT', 2)
        assert c.do('GET', 2)
        assert len(c) == 2
        assert c.dump() == [2, 1]
        c.do('PUT', 3)
        assert len(c) == 2
        assert c.dump() == [3, 2]
        assert c.do('GET', 2)
        assert c.do('GET', 3)
        assert not c.do('GET', 1)
        c.do('DELETE', 3)
        assert not c.do('GET', 3)
        assert c.dump() == [2]
        c.do('DELETE', 2)
        assert not c.do('GET', 2)
        assert c.dump() == []


class TestMinCache(object):

    def test_get_put(self):
        trace = [1, 2, 3, 4, 4, 2, 1]
        c = cache.BeladyMinCache(2, trace)
        assert not c.get(1)
        assert c.put(1) is None
        assert {1} == set(c.dump())
        assert not c.get(2)
        assert c.put(2) is None
        assert {1, 2} == set(c.dump())
        assert not c.get(3)
        assert c.put(3) is None
        assert {1, 2} == set(c.dump())
        assert not c.get(4)
        assert c.put(4) == 1
        assert {4, 2} == set(c.dump())
        assert c.get(4)
        assert {4, 2} == set(c.dump())
        assert c.get(2)
        assert {4, 2} == set(c.dump())
        assert not c.get(1)
        assert c.put(1) is None
        assert {4, 2} == set(c.dump())

    def test_get_put_no_hits(self):
        trace = range(10)
        size = 3
        c = cache.BeladyMinCache(3, trace)
        for i in trace:
            assert not c.get(i)
            assert c.put(i) is None
            assert set(range(min(i + 1, size))) == set(c.dump())


class TestLruCache(object):

    def test_lru(self):
        c = cache.LruCache(4)
        c.put(0)
        assert len(c) == 1
        c.put(2)
        assert len(c) == 2
        c.put(3)
        assert len(c) == 3
        c.put(4)
        assert len(c) == 4
        assert c.dump() == [4, 3, 2, 0]
        assert c.put(5) == 0
        assert c.put(5) == None
        assert len(c) == 4
        assert c.dump() == [5, 4, 3, 2]
        c.get(2)
        assert c.dump() == [2, 5, 4, 3]
        c.get(4)
        assert c.dump() == [4, 2, 5, 3]
        c.clear()
        assert len(c) == 0
        assert c.dump() == []

    def test_remove(self):
        c = cache.LruCache(4)
        c.put(1)
        c.put(2)
        c.put(3)
        c.remove(2)
        assert len(c) == 2
        assert c.dump() == [3, 1]
        c.put(4)
        c.put(5)
        assert c.dump() == [5, 4, 3, 1]
        c.remove(5)
        assert len(c) == 3
        assert c.dump() == [4, 3, 1]
        c.remove(1)
        assert len(c) == 2
        assert c.dump() == [4, 3]

    def test_position(self):
        c = cache.LruCache(4)
        c.put(4)
        c.put(3)
        c.put(2)
        c.put(1)
        assert c.dump() == [1, 2, 3, 4]
        assert c.position(1) == 0
        assert c.position(2) == 1
        assert c.position(3) == 2
        assert c.position(4) == 3


class TestSlruCache(object):

    def test_alloc(self):
        c = cache.SegmentedLruCache(100, 3, [0.4, 0.21, 0.39])
        assert list(c._segment_maxlen) == [40, 21, 39]
        assert sum(c._segment_maxlen) == c.maxlen

    def test_alloc_rounding(self):
        c = cache.SegmentedLruCache(100, 3, [0.402, 0.201, 0.397])
        assert list(c._segment_maxlen) == [40, 20, 40]
        assert sum(c._segment_maxlen) == c.maxlen

    def test_put_get(self):
        c = cache.SegmentedLruCache(9, 3)
        assert c.maxlen == 9
        c.put(1)
        assert c.dump(serialized=False) == [[], [], [1]]
        c.put(2)
        assert c.dump(serialized=False) == [[], [], [2, 1]]
        c.put(3)
        assert len(c) == 3
        assert c.dump(serialized=False) == [[], [], [3, 2, 1]]
        c.get(2)
        assert len(c) == 3
        assert c.dump(serialized=False) == [[], [2], [3, 1]]
        c.get(2)
        assert len(c) == 3
        assert c.dump(serialized=False) == [[2], [], [3, 1]]
        c.put(4)
        assert len(c) == 4
        assert c.dump(serialized=False) == [[2], [], [4, 3, 1]]
        evicted = c.put(5)
        assert evicted == 1
        assert len(c) == 4
        assert c.dump(serialized=False) == [[2], [], [5, 4, 3]]
        c.get(5)
        assert len(c) == 4
        assert c.dump(serialized=False) == [[2], [5], [4, 3]]
        c.put(6)
        assert len(c) == 5
        assert c.dump(serialized=False) == [[2], [5], [6, 4, 3]]
        c.get(6)
        assert len(c) == 5
        assert c.dump(serialized=False) == [[2], [6, 5], [4, 3]]
        c.get(3)
        assert len(c) == 5
        assert c.dump(serialized=False) == [[2], [3, 6, 5], [4]]
        c.get(4)
        assert len(c) == 5
        assert c.dump(serialized=False) == [[2], [4, 3, 6], [5]]
        c.get(4)
        assert len(c) == 5
        assert c.dump(serialized=False) == [[4, 2], [3, 6], [5]]
        c.get(2)
        assert len(c) == 5
        assert c.dump(serialized=False) == [[2, 4], [3, 6], [5]]
        c.get(3)
        assert len(c) == 5
        assert c.dump(serialized=False) == [[3, 2, 4], [6], [5]]
        c.get(3)
        assert len(c) == 5
        assert c.dump(serialized=False) == [[3, 2, 4], [6], [5]]
        c.get(2)
        assert len(c) == 5
        assert c.dump(serialized=False) == [[2, 3, 4], [6], [5]]
        c.get(6)
        assert len(c) == 5
        assert c.dump(serialized=False) == [[6, 2, 3], [4], [5]]

    def test_remove(self):
        c = cache.SegmentedLruCache(4, 2)
        c.put(2)
        c.put(2)
        c.put(1)
        c.put(1)
        c.put(4)
        c.put(3)
        assert c.dump(serialized=False) == [[1, 2], [3, 4]]
        c.remove(2)
        assert len(c) == 3
        assert c.dump(serialized=False) == [[1], [3, 4]]
        c.remove(1)
        assert len(c) == 2
        assert c.dump(serialized=False) == [[], [3, 4]]
        c.remove(4)
        assert len(c) == 1
        assert c.dump(serialized=False) == [[], [3]]
        c.remove(3)
        assert len(c) == 0
        assert c.dump(serialized=False) == [[], []]

    def test_position(self):
        c = cache.SegmentedLruCache(4, 2)
        c.put(2)
        c.put(2)
        c.put(1)
        c.put(1)
        c.put(4)
        c.put(3)
        assert c.dump(serialized=False) == [[1, 2], [3, 4]]
        assert c.position(1) == 0
        assert c.position(2) == 1
        assert c.position(3) == 2
        assert c.position(4) == 3

    def test_has(self):
        c = cache.SegmentedLruCache(4, 2)
        c.put(2)
        c.put(2)
        c.put(1)
        c.put(1)
        c.put(4)
        c.put(3)
        assert c.dump(serialized=False) == [[1, 2], [3, 4]]
        assert c.has(1)
        assert c.has(2)
        assert c.has(3)
        assert c.has(4)
        assert not c.has(5)

    def test_dump(self):
        c = cache.SegmentedLruCache(4, 2)
        c.put(2)
        c.put(2)
        c.put(1)
        c.put(1)
        c.put(4)
        c.put(3)
        assert c.dump(serialized=False) == [[1, 2], [3, 4]]
        assert c.dump(serialized=True) == [1, 2, 3, 4]
        assert c.dump() == [1, 2, 3, 4]


class TestFifoCache(object):

    def test_fifo(self):
        c = cache.FifoCache(4)
        assert len(c) == 0
        c.put(1)
        assert len(c) == 1
        c.put(2)
        assert len(c) == 2
        c.put(3)
        assert len(c) == 3
        c.put(4)
        assert len(c) == 4
        assert c.dump() == [4, 3, 2, 1]
        c.put(5)
        assert len(c) == 4
        assert c.dump() == [5, 4, 3, 2]
        c.get(2)
        assert c.dump() == [5, 4, 3, 2]
        c.get(4)
        assert c.dump() == [5, 4, 3, 2]
        c.put(6)
        assert c.dump() == [6, 5, 4, 3]
        c.clear()
        assert len(c) == 0
        assert c.dump() == []

    def test_remove(self):
        c = cache.FifoCache(4)
        c.put(1)
        c.put(2)
        c.put(3)
        c.remove(2)
        assert len(c) == 2
        assert c.dump() == [3, 1]
        c.put(4)
        c.put(5)
        assert c.dump() == [5, 4, 3, 1]
        c.remove(5)
        assert len(c) == 3
        assert c.dump() == [4, 3, 1]


class TestClimbCache(object):

    def test_climb(self):
        c = cache.ClimbCache(4)
        c.put(1)
        assert len(c) == 1
        c.put(2)
        assert len(c) == 2
        c.put(3)
        assert len(c) == 3
        c.put(5)
        assert len(c) == 4
        assert c.dump() == [1, 2, 3, 5]
        assert c.put(4) == 5
        assert c.dump() == [1, 2, 3, 4]
        assert c.put(4) == None
        assert c.dump() == [1, 2, 4, 3]
        assert c.put(4) == None
        assert c.dump() == [1, 4, 2, 3]
        assert c.put(4) == None
        assert c.dump() == [4, 1, 2, 3]
        assert c.put(4) == None
        assert c.dump() == [4, 1, 2, 3]
        assert c.put(5) == 3
        assert c.dump() == [4, 1, 2, 5]

    def test_remove(self):
        c = cache.ClimbCache(4)
        c.put(1)
        c.put(2)
        c.put(3)
        c.remove(2)
        assert len(c) == 2
        assert c.dump() == [1, 3]
        c.put(4)
        c.put(5)
        assert c.dump() == [1, 3, 4, 5]
        c.remove(5)
        assert len(c) == 3
        assert c.dump() == [1, 3, 4]
        c.remove(1)
        assert len(c) == 2
        assert c.dump() == [3, 4]

    def test_position(self):
        c = cache.ClimbCache(4)
        c.put(1)
        c.put(2)
        c.put(3)
        c.put(4)
        assert c.dump() == [1, 2, 3, 4]
        assert c.position(1) == 0
        assert c.position(2) == 1
        assert c.position(3) == 2
        assert c.position(4) == 3


class TestRandCache(object):

    def test_rand(self):
        c = cache.RandEvictionCache(4)
        assert len(c) == 0
        c.put(1)
        assert len(c) == 1
        c.put(2)
        assert len(c) == 2
        c.put(3)
        assert len(c) == 3
        c.put(4)
        assert len(c) == 4
        assert len(c.dump()) == 4
        for v in (1, 2, 3, 4):
            assert c.has(v)
        c.get(3)
        for v in (1, 2, 3, 4):
            assert c.has(v)
        c.put(5)
        assert len(c) == 4
        assert c.has(5)
        c.clear()
        assert len(c) == 0
        assert c.dump() == []

    def test_remove(self):
        c = cache.RandEvictionCache(4)
        c.put(1)
        c.put(2)
        c.put(3)
        c.remove(2)
        assert len(c) == 2
        for v in (3, 1):
            assert c.has(v)
        c.put(4)
        c.put(5)
        for v in (5, 4, 3, 1):
            assert c.has(v)
        c.remove(5)
        assert len(c) == 3
        for v in (4, 3, 1):
            assert c.has(v)


class TestInCacheLfuCache(object):

    def test_lfu(self):
        c = cache.InCacheLfuCache(4)
        assert len(c) == 0
        c.put(1)
        assert len(c) == 1
        c.put(2)
        assert len(c) == 2
        c.put(3)
        assert len(c) == 3
        c.put(4)
        assert len(c) == 4
        assert len(c.dump()) == 4
        for v in (1, 2, 3, 4):
            assert c.has(v)
        c.get(1)
        c.get(1)
        c.get(1)
        c.get(2)
        c.get(2)
        c.get(3)
        c.put(5)
        assert c.dump() == [1, 2, 3, 5]
        assert len(c) == 4
        assert c.has(5)
        c.clear()
        assert len(c) == 0
        assert c.dump() == []


class TestPerfectLfuCache(object):

    def test_lfu(self):
        c = cache.PerfectLfuCache(3)
        assert len(c) == 0
        c.put(1)
        assert len(c) == 1
        c.put(2)
        assert len(c) == 2
        c.put(3)
        assert len(c) == 3
        assert len(c.dump()) == 3
        for v in (1, 2, 3):
            assert c.has(v)
        c.get(1)
        c.get(1)
        c.get(1)
        c.get(1)
        c.get(1)
        c.get(2)
        c.get(2)
        c.get(2)
        c.get(2)
        c.get(3)
        c.get(3)
        c.get(3)
        c.get(5)
        c.put(5)  # This does not removes 3
        assert c.dump() == [1, 2, 3]
        c.get(5)
        c.get(5)
        c.get(5)
        c.get(5)
        c.get(5)
        # Now 5 has been requested frequently enough to be included in cache
        # and replace 3
        c.put(5)
        assert c.dump() == [5, 1, 2]
        # Now 5 has been requested 2 times, but 3 was requested 3 times. If I
        # reinsert 3, 3 is kept and 5 discarded
        c.get(3)
        c.get(3)
        c.get(3)
        c.get(3)
        c.get(3)
        # Now 3 has been requested enough times to be inserted and evict 2
        c.put(3)
        assert c.dump() == [3, 5, 1]
        c.clear()
        assert len(c) == 0
        assert c.dump() == []


class TestInsertAfterKHits(object):

    def test_put_get_no_memory(self):
        c = cache.LruCache(2)
        c = cache.insert_after_k_hits_cache(c, k=3, memory=None)
        assert not c.get(1)
        c.put(1)
        assert not c.get(1)
        c.put(1)
        assert not c.get(1)
        c.put(1)
        assert c.get(1)

    def test_put_get_force_insert(self):
        c = cache.LruCache(2)
        c = cache.insert_after_k_hits_cache(c, k=3, memory=None)
        assert not c.get(1)
        c.put(1, force_insert=True)
        assert c.get(1)
        c.put(2)
        assert not c.get(2)
        c.put(2)
        assert not c.get(2)
        c.put(2)
        assert c.get(2)

    def test_put_get_force_insert_eviction(self):
        c = cache.LruCache(2)
        c = cache.insert_after_k_hits_cache(c, k=3, memory=None)
        assert not c.get(1)
        c.put(1, force_insert=True)
        assert c.get(1)
        c.put(2, force_insert=True)
        assert c.get(2)
        assert c.put(3, force_insert=True) == 1

    def test_put_get_mixed_no_memory(self):
        c = cache.LruCache(2)
        c = cache.insert_after_k_hits_cache(c, k=3, memory=None)
        assert not c.get(1)
        c.put(1)
        assert not c.get(2)
        c.put(2)
        assert not c.get(1)
        c.put(1)
        assert not c.get(2)
        c.put(2)
        assert not c.get(2)
        c.put(2)
        assert c.get(2)
        assert not c.get(1)
        c.put(1)
        assert c.get(1)
        assert c.get(2)

    def test_put_get_mixed_memory(self):
        c = cache.LruCache(2)
        c = cache.insert_after_k_hits_cache(c, k=2, memory=2)
        assert 0 == len(c._metacache_queue)
        assert 0 == len(c._metacache_hits)
        assert not c.get(1)
        c.put(1)
        assert 1 == len(c._metacache_queue)
        assert 1 == len(c._metacache_hits)
        assert not c.get(2)
        c.put(2)
        assert 2 == len(c._metacache_queue)
        assert 2 == len(c._metacache_hits)
        assert not c.get(3)
        c.put(3)
        assert 2 == len(c._metacache_queue)
        assert 2 == len(c._metacache_hits)
        assert not c.get(1)
        c.put(1)
        assert 2 == len(c._metacache_queue)
        assert 2 == len(c._metacache_hits)
        # This fails because memory wiped out record for 1
        assert not c.get(1)
        assert not c.get(3)
        c.put(3)
        assert 1 == len(c._metacache_queue)
        assert 1 == len(c._metacache_hits)
        assert c.get(3)
        assert not c.get(1)
        c.put(1)
        assert c.get(1)
        assert 0 == len(c._metacache_queue)
        assert 0 == len(c._metacache_hits)

    def test_deepcopy(self):
        c = cache.LruCache(10)
        rc = cache.insert_after_k_hits_cache(c, k=3)
        rc.put(1)
        assert not c.has(1)
        c.put(3)
        assert not rc.has(3)

    def test_naming(self):
        c = cache.insert_after_k_hits_cache(cache.FifoCache(3), k=3)
        assert c.get.__name__ == 'get'
        assert c.put.__name__ == 'put'
        assert c.dump.__name__ == 'dump'
        assert c.clear.__name__ == 'clear'
        assert len(c.get.__doc__) > 0
        assert len(c.put.__doc__) > 0
        assert len(c.dump.__doc__) > 0
        assert len(c.clear.__doc__) > 0


class TestRandInsert(object):

    def test_rand_insert(self):
        n = 10000
        r = 10
        p1 = 0.01
        p2 = 0.1
        rc1 = cache.rand_insert_cache(cache.LruCache(n), p1)
        rc2 = cache.rand_insert_cache(cache.LruCache(n), p2)
        len_rc1 = 0
        len_rc2 = 0
        for _ in range(r):
            for i in range(n):
                rc1.put(i)
                rc2.put(i)
            len_rc1 += len(rc1)
            len_rc2 += len(rc2)
            rc1.clear()
            rc2.clear()
        assert abs(len_rc1 / r - n * p1) < 50
        assert abs(len_rc2 / r - n * p2) < 50

    def test_constant_seed(self):
        n = 10000
        p = 0.1
        rc1 = cache.rand_insert_cache(cache.LruCache(n), p, seed=0)
        for i in range(n):
            rc1.put(i)
        rc2 = cache.rand_insert_cache(cache.LruCache(n), p, seed=0)
        for i in range(n):
            rc2.put(i)
        assert rc1.dump() == rc2.dump()

    def test_different_seed(self):
        n = 10000
        p = 0.1
        rc1 = cache.rand_insert_cache(cache.LruCache(n), p, seed=1)
        for i in range(n):
            rc1.put(i)
        rc2 = cache.rand_insert_cache(cache.LruCache(n), p, seed=2)
        for i in range(n):
            rc2.put(i)
        assert rc1.dump() != rc2.dump()

    def test_deepcopy(self):
        c = cache.LruCache(10)
        rc = cache.rand_insert_cache(c, p=1.0)
        rc.put(1)
        assert not c.has(1)
        c.put(3)
        assert not rc.has(3)

    def test_naming(self):
        c = cache.rand_insert_cache(cache.FifoCache(3), 0.2)
        assert c.get.__name__ == 'get'
        assert c.put.__name__ == 'put'
        assert c.dump.__name__ == 'dump'
        assert c.clear.__name__ == 'clear'
        assert len(c.get.__doc__) > 0
        assert len(c.put.__doc__) > 0
        assert len(c.dump.__doc__) > 0
        assert len(c.clear.__doc__) > 0


class TestKeyValCache(object):

    def test_key_val_cache(self):
        c = cache.keyval_cache(cache.FifoCache(3))
        c.put(1, 11)
        assert c.get(1) == 11
        c.put(1, 12)
        assert c.get(1) == 12
        assert c.dump() == [(1, 12)]
        c.put(2, 21)
        assert c.has(1)
        assert c.has(2)
        c.put(3, 31)
        k, v = c.put(4, 41)
        assert c.remove(2) == 21
        assert len(c) == 2
        assert (k, v) == (1, 12)
        c.clear()
        assert len(c) == 0

    def test_naming(self):
        c = cache.keyval_cache(cache.FifoCache(3))
        assert c.get.__name__ == 'get'
        assert c.put.__name__ == 'put'
        assert c.dump.__name__ == 'dump'
        assert c.clear.__name__ == 'clear'
        assert len(c.get.__doc__) > 0
        assert len(c.put.__doc__) > 0
        assert len(c.dump.__doc__) > 0
        assert len(c.clear.__doc__) > 0

    def test_deepcopy(self):
        kc = cache.LruCache(10)
        kvc = cache.keyval_cache(kc)
        kvc.put(1, 2)
        assert not kc.has(1)
        kc.put(3)
        assert not kvc.has(3)

    def test_zero_val_lru(self):
        c = cache.keyval_cache(cache.LruCache(10))
        reqs = [(10, 0), (10, 1)]
        for k, v in reqs:
            c.put(k, v)


class TestTtlCache(object):

    def test_put_dump(self):
        curr_time = 1
        f_time = lambda: curr_time
        c = cache.ttl_cache(cache.FifoCache(4), f_time)
        c.put(1, ttl=2)
        c.put(2, ttl=5)
        c.put(3, ttl=3)
        assert c.dump() == [(3, 4), (2, 6), (1, 3)]
        assert c.has(1)
        assert c.has(2)
        assert c.has(3)
        curr_time = 4
        assert not c.has(1)
        assert c.has(2)
        assert c.has(3)
        assert c.dump() == [(3, 4), (2, 6)]
        c.put(3, ttl=6)
        assert c.dump() == [(3, 10), (2, 6)]
        curr_time = 11
        assert c.dump() == []

    def test_get(self):
        curr_time = 1
        f_time = lambda: curr_time
        c = cache.ttl_cache(cache.FifoCache(3), f_time)
        c.put(1, ttl=2)
        assert c.get(1)
        assert not c.get(2)
        assert c.get(1)
        c.put(2, ttl=7)
        assert c.get(1)
        assert c.get(2)
        curr_time = 4
        assert not c.get(1)
        assert c.get(2)
        curr_time = 15
        assert not c.get(1)
        assert not c.get(2)

    def test_eviction(self):
        curr_time = 0
        f_time = lambda: curr_time
        c = cache.ttl_cache(cache.FifoCache(3), f_time)
        assert c.put(1, ttl=4) is None
        assert c.put(2, ttl=6) is None
        assert c.put(3, ttl=8) is None
        assert c.put(4, ttl=10) == 1
        curr_time = 7
        assert c.put(5, ttl=12) is None

    def test_incorrect_params(self):
        with pytest.raises(TypeError):
            cache.ttl_cache('cache', lambda: 1)
        with pytest.raises(TypeError):
            cache.ttl_cache(cache.FifoCache(4), 'function')
        c = cache.ttl_cache(cache.FifoCache(10), lambda: 5)
        with pytest.raises(ValueError):
            c.put(1, ttl=2, expires=8)

    def test_put_stale_content(self):
        c = cache.ttl_cache(cache.FifoCache(2), lambda: 5)
        c.put(1, ttl=-2)
        assert not c.has(1)
        c.put(2, expires=3)
        assert not c.has(2)

    def test_inf_ttl(self):
        curr_time = 1
        f_time = lambda: curr_time
        c = cache.ttl_cache(cache.FifoCache(5), f_time)
        c.put(1)
        c.put(2)
        c.put(3)
        curr_time = 1000
        dump = c.dump()
        assert (1, np.infty) in dump
        assert (2, np.infty) in dump
        assert (3, np.infty) in dump
        c.put(1, ttl=100)
        curr_time = 2000
        dump = c.dump()
        assert len(dump) == 3
        assert (1, np.infty) in dump
        assert (2, np.infty) in dump
        assert (3, np.infty) in dump
        c.put(4, ttl=200)
        dump = c.dump()
        assert len(dump) == 4
        assert dump[0] == (4, 2200)
        assert (1, np.infty) in dump
        assert (2, np.infty) in dump
        assert (3, np.infty) in dump
        curr_time = 3000
        dump = c.dump()
        assert len(dump) == 3
        assert (1, np.infty) in dump
        assert (2, np.infty) in dump
        assert (3, np.infty) in dump

    def test_clear(self):
        curr_time = 1
        f_time = lambda: curr_time
        c = cache.ttl_cache(cache.FifoCache(3), f_time)
        c.put(1, ttl=4)
        c.put(2, ttl=5)
        c.put(1, ttl=8)
        c.put(3, ttl=3)
        c.put(4, ttl=1)
        c.clear()
        assert len(c) == 0
        assert c.dump() == []

    def test_naming(self):
        c = cache.ttl_cache(cache.FifoCache(4), lambda: 0)
        assert c.get.__name__ == 'get'
        assert c.put.__name__ == 'put'
        assert c.dump.__name__ == 'dump'
        assert c.clear.__name__ == 'clear'
        assert c.has.__name__ == 'has'

    def test_deepcopy(self):
        c = cache.LruCache(10)
        ttl_c = cache.ttl_cache(c, lambda: 0)
        ttl_c.put(1, 2)
        assert not c.has(1)
        c.put(3)
        assert not ttl_c.has(3)
