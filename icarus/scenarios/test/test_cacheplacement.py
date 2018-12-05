import unittest

import networkx as nx
import fnss

import icarus.scenarios as cacheplacement


class TestRadomCachePlacement(unittest.TestCase):

    def setUp(self):
        self.topo = fnss.line_topology(6)
        fnss.add_stack(self.topo, 0, 'receiver')
        self.topo.graph['icr_candidates'] = []
        for i in range(1, 5):
            self.topo.graph['icr_candidates'].append(i)
            fnss.add_stack(self.topo, i, 'router')
        fnss.add_stack(self.topo, 5, 'source')

    def verify_random_assignment(self, topo, cache_budget, cache_nodes):
        cacheplacement.random_cache_placement(topo, cache_budget, cache_nodes)
        actual_cache_budget = 0
        actual_cache_nodes = 0
        for v in topo.nodes():
            if 'cache_size' in topo.node[v]['stack'][1]:
                self.assertEqual(int(cache_budget / cache_nodes), topo.node[v]['stack'][1]['cache_size'])
                actual_cache_budget += topo.node[v]['stack'][1]['cache_size']
                actual_cache_nodes += 1
        self.assertGreater(cache_budget + cache_nodes, actual_cache_budget)
        self.assertLess(cache_budget - cache_nodes, actual_cache_budget)
        self.assertEqual(cache_nodes, actual_cache_nodes)

    def test_random_cache_placement_all_nodes(self):
        cacheplacement.random_cache_placement(self.topo, 100, 4)
        for i in range(1, 5):
            self.assertEqual(25, self.topo.node[i]['stack'][1]['cache_size'])

    def test_random_cache_placement_some_nodes_a(self):
        self.verify_random_assignment(self.topo, 100, 2)

    def test_random_cache_placement_some_nodes_b(self):
        self.verify_random_assignment(self.topo, 100, 3)

    def test_random_cache_placement_some_nodes_c(self):
        self.verify_random_assignment(self.topo, 100, 4)


class TestOptimalHashroutingCachePlacement(unittest.TestCase):

    def setUp(self):
        #
        #       -- s1 --
        #     /     |    \
        #   c1-----c2----c3
        #  /  \   / | \    \
        # r1  r2 r3 r4 r5  r6
        #
        topo = fnss.Topology()
        icr_candidates = ["c1", "c2", "c3"]
        nx.add_path(topo, icr_candidates)
        topo.add_edge("c1", "s1")
        topo.add_edge("c2", "s1")
        topo.add_edge("c3", "s1")
        topo.add_edge("c1", "r1")
        topo.add_edge("c1", "r2")
        topo.add_edge("c2", "r3")
        topo.add_edge("c2", "r4")
        topo.add_edge("c2", "r5")
        topo.add_edge("c3", "r6")
        topo.graph['icr_candidates'] = set(icr_candidates)
        for router in icr_candidates:
            fnss.add_stack(topo, router, 'router')
        for src in ['s1']:
            fnss.add_stack(topo, src, 'source')
        for rcv in ['r1', 'r2', 'r3', 'r4', 'r5', 'r6']:
            fnss.add_stack(topo, rcv, 'receiver')
        self.topo = cacheplacement.IcnTopology(topo)

    def test_optimal_hashrouting_cache_placement_a(self):
        cache_budget = 30
        cache_nodes = 1
        cacheplacement.optimal_hashrouting_cache_placement(self.topo, cache_budget,
                                                           cache_nodes, 0.5)
        if'cache_size' in self.topo.node["c1"]['stack'][1]:
            self.assertEqual(0, self.topo.node["c1"]['stack'][1]['cache_size'])
        self.assertEqual(30, self.topo.node["c2"]['stack'][1]['cache_size'])
        if'cache_size' in self.topo.node["c3"]['stack'][1]:
            self.assertEqual(0, self.topo.node["c3"]['stack'][1]['cache_size'])

    def test_optimal_hashrouting_cache_placement_b(self):
        cache_budget = 30
        cache_nodes = 2
        cacheplacement.optimal_hashrouting_cache_placement(self.topo, cache_budget,
                                                           cache_nodes, 0.5)
        self.assertEqual(15, self.topo.node["c1"]['stack'][1]['cache_size'])
        self.assertEqual(15, self.topo.node["c2"]['stack'][1]['cache_size'])
        if'cache_size' in self.topo.node["c3"]['stack'][1]:
            self.assertEqual(0, self.topo.node["c3"]['stack'][1]['cache_size'])

    def test_optimal_hashrouting_cache_placement_c(self):
        cache_budget = 30
        cache_nodes = 3
        cacheplacement.optimal_hashrouting_cache_placement(self.topo, cache_budget,
                                                           cache_nodes, 0.5)
        self.assertEqual(10, self.topo.node["c1"]['stack'][1]['cache_size'])
        self.assertEqual(10, self.topo.node["c2"]['stack'][1]['cache_size'])
        self.assertEqual(10, self.topo.node["c3"]['stack'][1]['cache_size'])


class TestOptimalMedianCachePlacement(unittest.TestCase):

    def setUp(self):
        #
        #   s1    s2
        #    |     |
        #   c1-----c2----c3
        #  /  \   / | \    \
        # r1  r2 r3 r4 r5  r6
        #
        topo = fnss.Topology()
        icr_candidates = ["c1", "c2", "c3"]
        nx.add_path(topo, icr_candidates)
        topo.add_edge("c2", "s1")
        topo.add_edge("c2", "s2")
        topo.add_edge("c1", "r1")
        topo.add_edge("c1", "r2")
        topo.add_edge("c2", "r3")
        topo.add_edge("c2", "r4")
        topo.add_edge("c2", "r5")
        topo.add_edge("c3", "r6")
        topo.graph['icr_candidates'] = set(icr_candidates)
        for router in icr_candidates:
            fnss.add_stack(topo, router, 'router')
        for src in ['s1']:
            fnss.add_stack(topo, src, 'source')
        for rcv in ['r1', 'r2', 'r3', 'r4', 'r5', 'r6']:
            fnss.add_stack(topo, rcv, 'receiver')
        self.topo = cacheplacement.IcnTopology(topo)

    def test_1(self):
        cache_budget = 30
        cache_nodes = 1
        cacheplacement.optimal_median_cache_placement(self.topo, cache_budget,
                                                      cache_nodes, 0.5)
        if'cache_size' in self.topo.node["c1"]['stack'][1]:
            self.assertEqual(0, self.topo.node["c1"]['stack'][1]['cache_size'])
        self.assertEqual(30, self.topo.node["c2"]['stack'][1]['cache_size'])
        if'cache_size' in self.topo.node["c3"]['stack'][1]:
            self.assertEqual(0, self.topo.node["c3"]['stack'][1]['cache_size'])
        self.assertDictEqual({'r1': 'c2', 'r2': 'c2', 'r3': 'c2', 'r4': 'c2', 'r5': 'c2', 'r6': 'c2'},
                             self.topo.graph['cache_assignment'])

    def test_2(self):
        cache_budget = 30
        cache_nodes = 2
        cacheplacement.optimal_median_cache_placement(self.topo, cache_budget,
                                                           cache_nodes, 0.5)
        self.assertEqual(15, self.topo.node["c1"]['stack'][1]['cache_size'])
        self.assertEqual(15, self.topo.node["c2"]['stack'][1]['cache_size'])
        if'cache_size' in self.topo.node["c3"]['stack'][1]:
            self.assertEqual(0, self.topo.node["c3"]['stack'][1]['cache_size'])
        self.assertDictEqual({'r1': 'c1', 'r2': 'c1', 'r3': 'c2', 'r4': 'c2', 'r5': 'c2', 'r6': 'c2'},
                             self.topo.graph['cache_assignment'])

    def test_3(self):
        cache_budget = 30
        cache_nodes = 3
        cacheplacement.optimal_median_cache_placement(self.topo, cache_budget,
                                                           cache_nodes, 0.5)
        self.assertEqual(10, self.topo.node["c1"]['stack'][1]['cache_size'])
        self.assertEqual(10, self.topo.node["c2"]['stack'][1]['cache_size'])
        self.assertEqual(10, self.topo.node["c3"]['stack'][1]['cache_size'])
        self.assertDictEqual({'r1': 'c1', 'r2': 'c1', 'r3': 'c2', 'r4': 'c2', 'r5': 'c2', 'r6': 'c3'},
                             self.topo.graph['cache_assignment'])


class TestClusteredHashroutingCachePlacement(unittest.TestCase):

    def setUp(self):
        topo = cacheplacement.IcnTopology(fnss.line_topology(7))
        receivers = [0]
        sources = [6]
        icr_candidates = [1, 2, 3, 4, 5]
        topo.graph['icr_candidates'] = set(icr_candidates)
        for router in icr_candidates:
            fnss.add_stack(topo, router, 'router')
        for src in sources:
            fnss.add_stack(topo, src, 'source')
        for rcv in receivers:
            fnss.add_stack(topo, rcv, 'receiver')
        fnss.set_delays_constant(topo, 2, 'ms')
        fnss.set_delays_constant(topo, 20, 'ms', [(2, 3)])
        self.topo = topo

    def test_cluster_const(self):
        n_clusters = 2
        cache_budget = 60
        cacheplacement.clustered_hashrouting_cache_placement(self.topo,
                            cache_budget, n_clusters, 'cluster_const')
        clusters = self.topo.graph['clusters']
        self.assertEqual(n_clusters, len(clusters))
        self.assertEqual(len(self.topo.graph['icr_candidates']), sum(len(c) for c in clusters))
        for c in clusters:
            if 0 in c:
                self.assertSetEqual(set([0, 1, 2]), c)
            elif 7 in c:
                self.assertSetEqual(set([3, 4, 5, 6]), c)
        self.assertDictEqual({1: 15, 2: 15, 3: 10, 4: 10, 5: 10},
                             self.topo.cache_nodes())

    def test_node_const(self):
        n_clusters = 2
        cache_budget = 50
        cacheplacement.clustered_hashrouting_cache_placement(self.topo,
                            cache_budget, n_clusters, 'node_const')
        clusters = self.topo.graph['clusters']
        self.assertEqual(n_clusters, len(clusters))
        self.assertEqual(len(self.topo.graph['icr_candidates']), sum(len(c) for c in clusters))
        for c in clusters:
            if 0 in c:
                self.assertSetEqual(set([0, 1, 2]), c)
            elif 7 in c:
                self.assertSetEqual(set([3, 4, 5, 6]), c)
        cache_size = cache_budget / len(self.topo.cache_nodes())
        self.assertDictEqual({i: cache_size for i in self.topo.cache_nodes()},
                             self.topo.cache_nodes())
