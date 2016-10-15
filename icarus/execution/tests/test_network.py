from __future__ import division
import unittest

import networkx as nx
import fnss

from icarus.scenarios import IcnTopology
from icarus.execution.collectors import DummyCollector

import icarus.execution.network as network


class TestSymmetrifyPaths(unittest.TestCase):

    def test_symmetric_paths(self):
        topology = fnss.Topology()
        topology.add_path([1, 2, 4, 5, 3, 6, 1])
        path = nx.all_pairs_shortest_path(topology)
        self.assertNotEqual(list(path[1][5]), list(reversed(path[5][1])))
        network.symmetrify_paths(path)
        self.assertEqual(list(path[1][5]), list(reversed(path[5][1])))

class TestNetworkMvc(unittest.TestCase):

    @classmethod
    def build_topology(cls):
        # Topology sketch
        #
        # 0 ---- 1 ---- 2 ---- 3 ---- 4
        #        |             |
        #        |             |
        #        5 -- 6 - 7 -- 8
        #
        topology = IcnTopology()
        topology.add_path([0, 1, 2, 3, 4], a=1, b=1)
        topology.add_path([1, 5, 6, 7, 8, 3], b=2, c=2)
        source = 4
        receiver = 0
        caches = (1, 2, 3, 5, 6, 7, 8)
        contents = [1, 2, 3]
        fnss.add_stack(topology, source, 'source', {'contents': contents})
        fnss.add_stack(topology, receiver, 'receiver', {})
        for v in caches:
            fnss.add_stack(topology, v, 'router', {'cache_size': 1})
        return topology

    def setUp(self):
        self.topology = self.build_topology()
        model = network.NetworkModel(self.topology, cache_policy={'name': 'FIFO'})
        self.view = network.NetworkView(model)
        self.controller = network.NetworkController(model)
        self.collector = DummyCollector(self.view)
        self.controller.attach_collector(self.collector)

    def test_remove_restore_link(self):
        self.assertEqual([0, 1, 2, 3, 4], self.view.shortest_path(0, 4))
        self.assertEqual(1, self.topology.edge[2][3]['a'])
        self.controller.remove_link(2, 3, recompute_paths=True)
        self.assertEqual([0, 1, 5, 6, 7, 8, 3, 4], self.view.shortest_path(0, 4))
        self.controller.restore_link(2, 3, recompute_paths=True)
        self.assertEqual([0, 1, 2, 3, 4], self.view.shortest_path(0, 4))
        self.assertEqual(1, self.topology.edge[2][3]['a'])

    def test_remove_restore_node(self):
        self.assertEqual([0, 1, 2, 3, 4], self.view.shortest_path(0, 4))
        self.assertEqual(1, self.view.cache_nodes(size=True)[2])
        self.controller.remove_node(2, recompute_paths=True)
        self.assertEqual([0, 1, 5, 6, 7, 8, 3, 4], self.view.shortest_path(0, 4))
        self.assertNotIn(2, self.view.cache_nodes())
        self.controller.restore_node(2, recompute_paths=True)
        self.assertEqual([0, 1, 2, 3, 4], self.view.shortest_path(0, 4))
        self.assertEqual(1, self.view.cache_nodes(size=True)[2])

    def test_joint_remove_restore_node_link(self):
        self.assertEqual([0, 1, 2, 3, 4], self.view.shortest_path(0, 4))
        self.controller.remove_link(2, 3, recompute_paths=True)
        self.assertEqual([0, 1, 5, 6, 7, 8, 3, 4], self.view.shortest_path(0, 4))
        self.assertEqual(1, self.view.cache_nodes(size=True)[2])
        self.controller.remove_node(2, recompute_paths=True)
        self.assertEqual([0, 1, 5, 6, 7, 8, 3, 4], self.view.shortest_path(0, 4))
        self.assertNotIn(2, self.view.cache_nodes())
        self.controller.restore_node(2, recompute_paths=True)
        self.assertEqual(1, self.view.cache_nodes(size=True)[2])
        self.assertEqual([0, 1, 5, 6, 7, 8, 3, 4], self.view.shortest_path(0, 4))
        self.controller.restore_link(2, 3, recompute_paths=True)
        self.assertEqual([0, 1, 2, 3, 4], self.view.shortest_path(0, 4))

    def test_rewire_link(self):
        self.assertEqual([0, 1, 2, 3, 4], self.view.shortest_path(0, 4))
        self.assertEqual(1, self.topology.edge[2][3]['a'])
        self.controller.rewire_link(1, 5, 1, 8, recompute_paths=True)
        self.assertEqual([0, 1, 8, 3, 4], self.view.shortest_path(0, 4))
        self.controller.rewire_link(1, 8, 1, 5, recompute_paths=True)
        self.assertEqual([0, 1, 2, 3, 4], self.view.shortest_path(0, 4))
        self.assertEqual(1, self.topology.edge[2][3]['a'])
