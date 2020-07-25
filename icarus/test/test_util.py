try:
    import cPickle as pickle
except ImportError:
    import pickle

import networkx as nx
import fnss

import icarus.util as util


class TestUtil(object):

    def test_timestr(self):
        assert "1m 30s" == util.timestr(90, True)
        assert "1m" == util.timestr(90, False)
        assert "2m" == util.timestr(120, True)
        assert "21s" == util.timestr(21, True)
        assert "0m" == util.timestr(21, False)
        assert "1h" == util.timestr(3600, True)
        assert "1h" == util.timestr(3600, False)
        assert "1h 0m 4s" == util.timestr(3604, True)
        assert "1h" == util.timestr(3604, False)
        assert "1h 2m 4s" == util.timestr(3724, True)
        assert "1h 2m" == util.timestr(3724, False)
        assert "2d 1h 3m 9s" == util.timestr(49 * 3600 + 189, True)
        assert "0s" == util.timestr(0, True)
        assert "0m" == util.timestr(0, False)

    def test_multicast_tree(self):
        topo = fnss.Topology()
        nx.add_path(topo, [2, 1, 3, 4])
        sp = dict(nx.all_pairs_shortest_path(topo))
        tree = util.multicast_tree(sp, 1, [2, 3])
        assert set(tree) == {(1, 2), (1, 3)}

    def test_apportionment(self):
        assert util.apportionment(10, [0.53, 0.47]) == [5, 5]
        assert util.apportionment(100, [0.4, 0.21, 0.39]) == [40, 21, 39]
        assert util.apportionment(99, [0.2, 0.7, 0.1]) == [20, 69, 10]


class TestSettings(object):

    def test_get_set(self):
        s = util.Settings()
        s["key_a"] = "val_a"
        assert "key_a" in s
        assert s["key_a"] == "val_a"
        assert len(s) == 1
        del s["key_a"]
        assert "key_a" not in s
        assert len(s) == 0

    def test_pickle_unpickle(self):
        s = util.Settings()
        s["key_a"] = "val_a"
        res = pickle.dumps(s)
        t = pickle.loads(res)
        assert s["key_a"] == t["key_a"]
