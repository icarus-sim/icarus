from __future__ import division
import unittest

import networkx as nx
import fnss

from icarus.execution.network import symmetrify_paths


class TestSymmetrifyPaths(unittest.TestCase):

    def test_symmetric_paths(self):
        topology = fnss.Topology()
        topology.add_path([1, 2, 4, 5, 3, 6, 1])
        path = nx.all_pairs_shortest_path(topology)
        self.assertNotEqual(list(path[1][5]), list(reversed(path[5][1])))
        symmetrify_paths(path)
        self.assertEqual(list(path[1][5]), list(reversed(path[5][1])))
