import unittest

import networkx as nx
import fnss

import icarus.scenarios as algorithms


class TestClustering(unittest.TestCase):

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

    def test_algorithms(self):
        t = algorithms.IcnTopology(fnss.line_topology(6))
        t.graph['icr_candidates'] = set(t.nodes())
        fnss.set_delays_constant(t, 1, 'ms')
        fnss.set_delays_constant(t, 3, 'ms', [(1, 2), (3, 4)])
        clusters = algorithms.compute_clusters(t, 3)
        expected_clusters = [set([0, 1]), set([2, 3]), set([4, 5])]
        self.assertEqual(expected_clusters, clusters)

    def test_deploy_clusters(self):
        t = algorithms.IcnTopology(fnss.line_topology(6))
        t.graph['icr_candidates'] = set(t.nodes())
        clusters = [set([0, 1]), set([2, 3]), set([4, 5])]
        cluster_map = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 2}
        algorithms.deploy_clusters(t, clusters)
        self.assertEqual(clusters, t.graph['clusters'])
        for v, data in t.nodes(data=True):
            self.assertEqual(cluster_map[v], data['cluster'])

    def test_extract_cluster_level_topology(self):
        t = algorithms.IcnTopology(fnss.line_topology(6))
        t.graph['icr_candidates'] = set(t.nodes())
        clusters = [set([0, 1]), set([2, 3]), set([4, 5])]
        algorithms.deploy_clusters(t, clusters)
        ct = algorithms.extract_cluster_level_topology(t)
        self.assertEqual(len(clusters), len(ct))

    def test_extract_cluster_level_topology_1_cluster(self):
        t = algorithms.IcnTopology(fnss.line_topology(3))
        t.graph['icr_candidates'] = set(t.nodes())
        clusters = [t.graph['icr_candidates']]
        algorithms.deploy_clusters(t, clusters)
        ct = algorithms.extract_cluster_level_topology(t)
        self.assertEqual(1, len(clusters))
        self.assertEqual(1, ct.number_of_nodes())


class TestPMedian(unittest.TestCase):

    def test_p_median(self):
        """
        Test topology:

        A ---- B ---- C ----[HIGH DIST] --- D --- E --- F

        Expected facilities: 1, 4
        """
        t = fnss.Topology()
        nx.add_path(t, "ABCDEF")
        fnss.set_weights_constant(t, 1)
        fnss.set_weights_constant(t, 2, [("C", "D")])
        distances = dict(nx.all_pairs_dijkstra_path_length(t, weight='weight'))
        allocation, facilities, cost = algorithms.compute_p_median(distances, 2)
        self.assertDictEqual({"A": "B", "B": "B", "C": "B", "D": "E", "E": "E", "F": "E", }, allocation)
        self.assertSetEqual(set("BE"), facilities)
        self.assertEqual(4, cost)

    def test_p_median_unsorted(self):
        """

        Test topology:

        A ---- C ---- B ----[HIGH DIST] --- E --- D --- F

        Expected facilities: 1, 4
        """
        t = fnss.Topology()
        nx.add_path(t, "ACBEDF")
        fnss.set_weights_constant(t, 1)
        fnss.set_weights_constant(t, 2, [("B", "E")])
        distances = dict(nx.all_pairs_dijkstra_path_length(t, weight='weight'))
        allocation, facilities, cost = algorithms.compute_p_median(distances, 2)
        self.assertDictEqual({"A": "C", "B": "C", "C": "C", "D": "D", "E": "D", "F": "D", }, allocation)
        self.assertSetEqual(set("CD"), facilities)
        self.assertEqual(4, cost)

    def test_p_median_3(self):
        """
        Test topology:

        A ---- C ---- B ----[HIGH DIST] --- E --- D --- F

        Expected facilities: 1, 4
        """
        t = fnss.Topology()
        nx.add_path(t, "ACBEDF")
        fnss.set_weights_constant(t, 1)
        fnss.set_weights_constant(t, 2, [("B", "E")])
        distances = dict(nx.all_pairs_dijkstra_path_length(t, weight='weight'))
        allocation, facilities, cost = algorithms.compute_p_median(distances, 3)
        self.assertEqual(3, cost)

    def test_p_median_4(self):
        """
        Test topology:

        A ---- C ---- B ----[HIGH DIST] --- E --- D --- F

        Expected facilities: 1, 4
        """
        t = fnss.Topology()
        nx.add_path(t, "ACBEDF")
        fnss.set_weights_constant(t, 1)
        fnss.set_weights_constant(t, 2, [("B", "E")])
        distances = dict(nx.all_pairs_dijkstra_path_length(t, weight='weight'))
        allocation, facilities, cost = algorithms.compute_p_median(distances, 4)
        self.assertEqual(2, cost)


    def test_p_median_6(self):
        """
        Test topology:

        A ---- C ---- B ----[HIGH DIST] --- E --- D --- F

        Expected facilities: 1, 4
        """
        t = fnss.Topology()
        nx.add_path(t, "ACBEDF")
        fnss.set_weights_constant(t, 1)
        fnss.set_weights_constant(t, 2, [("B", "E")])
        distances = dict(nx.all_pairs_dijkstra_path_length(t, weight='weight'))
        allocation, facilities, cost = algorithms.compute_p_median(distances, 6)
        self.assertDictEqual({i: i for i in "ABCDEF"}, allocation)
        self.assertSetEqual(set("ABCDEF"), facilities)
        self.assertEqual(0, cost)
