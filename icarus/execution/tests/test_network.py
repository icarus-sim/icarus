from __future__ import division

import networkx as nx
import fnss

from icarus.scenarios import IcnTopology
from icarus.execution.collectors import DummyCollector

import icarus.execution.network as network


class TestSymmetrifyPaths(object):

    def test_symmetric_paths(self):
        path = {1: {
                    1: [1],
                    2: [1, 2],
                    3: [1, 3],
                    4: [1, 2, 4]
                },
                2: {
                     1: [2, 1],
                     2: [2],
                     3: [2, 1, 3],
                     4: [2, 4]
                },
                3: {
                     1: [3, 1],
                     2: [3, 4, 2],
                     3: [3],
                     4: [3, 4]
                },
                4: {
                     1: [4, 3, 1],
                     2: [4, 2],
                     3: [4, 3],
                     4: [4]}
                }
        network.symmetrify_paths(path)
        assert list(path[1][4]) == list(reversed(path[4][1]))
        assert list(path[2][3]) == list(reversed(path[3][2]))


class TestNetworkMVC(object):

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
        nx.add_path(topology, [0, 1, 2, 3, 4], a=1, b=1)
        nx.add_path(topology, [1, 5, 6, 7, 8, 3], b=2, c=2)
        source = 4
        receiver = 0
        caches = (1, 2, 3, 5, 6, 7, 8)
        contents = [1, 2, 3]
        fnss.add_stack(topology, source, 'source', {'contents': contents})
        fnss.add_stack(topology, receiver, 'receiver', {})
        for v in caches:
            fnss.add_stack(topology, v, 'router', {'cache_size': 1})
        return topology

    def setup_method(self):
        self.topology = self.build_topology()
        model = network.NetworkModel(self.topology, cache_policy={'name': 'FIFO'})
        self.view = network.NetworkView(model)
        self.controller = network.NetworkController(model)
        self.collector = DummyCollector(self.view)
        self.controller.attach_collector(self.collector)

    def test_remove_restore_link(self):
        assert [0, 1, 2, 3, 4] == self.view.shortest_path(0, 4)
        assert 1 == self.topology.adj[2][3]['a']
        self.controller.remove_link(2, 3, recompute_paths=True)
        assert [0, 1, 5, 6, 7, 8, 3, 4] == self.view.shortest_path(0, 4)
        self.controller.restore_link(2, 3, recompute_paths=True)
        assert [0, 1, 2, 3, 4] == self.view.shortest_path(0, 4)
        assert 1 == self.topology.adj[2][3]['a']

    def test_remove_restore_node(self):
        assert [0, 1, 2, 3, 4] == self.view.shortest_path(0, 4)
        assert 1 == self.view.cache_nodes(size=True)[2]
        self.controller.remove_node(2, recompute_paths=True)
        assert [0, 1, 5, 6, 7, 8, 3, 4] == self.view.shortest_path(0, 4)
        assert 2 not in self.view.cache_nodes()
        self.controller.restore_node(2, recompute_paths=True)
        assert [0, 1, 2, 3, 4] == self.view.shortest_path(0, 4)
        assert 1 == self.view.cache_nodes(size=True)[2]

    def test_joint_remove_restore_node_link(self):
        assert [0, 1, 2, 3, 4] == self.view.shortest_path(0, 4)
        self.controller.remove_link(2, 3, recompute_paths=True)
        assert [0, 1, 5, 6, 7, 8, 3, 4] == self.view.shortest_path(0, 4)
        assert 1 == self.view.cache_nodes(size=True)[2]
        self.controller.remove_node(2, recompute_paths=True)
        assert [0, 1, 5, 6, 7, 8, 3, 4] == self.view.shortest_path(0, 4)
        assert 2 not in self.view.cache_nodes()
        self.controller.restore_node(2, recompute_paths=True)
        assert 1 == self.view.cache_nodes(size=True)[2]
        assert [0, 1, 5, 6, 7, 8, 3, 4] == self.view.shortest_path(0, 4)
        self.controller.restore_link(2, 3, recompute_paths=True)
        assert [0, 1, 2, 3, 4] == self.view.shortest_path(0, 4)

    def test_rewire_link(self):
        assert [0, 1, 2, 3, 4] == self.view.shortest_path(0, 4)
        assert 1 == self.topology.adj[2][3]['a']
        self.controller.rewire_link(1, 5, 1, 3, recompute_paths=True)
        assert [0, 1, 3, 4] == self.view.shortest_path(0, 4)
        self.controller.rewire_link(1, 3, 1, 5, recompute_paths=True)
        assert [0, 1, 2, 3, 4] == self.view.shortest_path(0, 4)
        assert 1 == self.topology.adj[2][3]['a']
