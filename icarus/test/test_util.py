import unittest

import networkx as nx
import fnss

import icarus.util as util


class TestUtil(unittest.TestCase):

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

    def test_timestr(self):
        self.assertEqual("1m 30s", util.timestr(90, True))
        self.assertEqual("1m", util.timestr(90, False))
        self.assertEqual("2m", util.timestr(120, True))
        self.assertEqual("21s", util.timestr(21, True))
        self.assertEqual("0m", util.timestr(21, False))
        self.assertEqual("1h", util.timestr(3600, True))
        self.assertEqual("1h", util.timestr(3600, False))
        self.assertEqual("1h 0m 4s", util.timestr(3604, True))
        self.assertEqual("1h", util.timestr(3604, False))
        self.assertEqual("1h 2m 4s", util.timestr(3724, True))
        self.assertEqual("1h 2m", util.timestr(3724, False))
        self.assertEqual("2d 1h 3m 9s", util.timestr(49 * 3600 + 189, True))
        self.assertEqual("0s", util.timestr(0, True))
        self.assertEqual("0m", util.timestr(0, False))

    def test_multicast_tree(self):
        topo = fnss.Topology()
        topo.add_path([2, 1, 3, 4])
        sp = nx.all_pairs_shortest_path(topo)
        tree = util.multicast_tree(sp, 1, [2, 3])
        self.assertSetEqual(set(tree), set([(1, 2), (1, 3)]))

    def test_apportionment(self):
        self.assertEqual(util.apportionment(10, [0.53, 0.47]), [5, 5])
        self.assertEqual(util.apportionment(100, [0.4, 0.21, 0.39]), [40, 21, 39])
        self.assertEqual(util.apportionment(99, [0.2, 0.7, 0.1]), [20, 69, 10])
