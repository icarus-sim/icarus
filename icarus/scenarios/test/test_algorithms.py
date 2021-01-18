import fnss

import networkx as nx

import icarus.scenarios as algorithms


class TestClustering(object):

    def test_algorithms(self):
        t = algorithms.IcnTopology(fnss.line_topology(6))
        t.graph['icr_candidates'] = set(t.nodes())
        fnss.set_delays_constant(t, 1, 'ms')
        fnss.set_delays_constant(t, 3, 'ms', [(1, 2), (3, 4)])
        clusters = algorithms.compute_clusters(t, 3)
        expected_clusters = [{0, 1}, {2, 3}, {4, 5}]
        assert expected_clusters == clusters

    def test_deploy_clusters(self):
        t = algorithms.IcnTopology(fnss.line_topology(6))
        t.graph['icr_candidates'] = set(t.nodes())
        clusters = [{0, 1}, {2, 3}, {4, 5}]
        cluster_map = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 2}
        algorithms.deploy_clusters(t, clusters)
        assert clusters == t.graph['clusters']
        for v, data in t.nodes(data=True):
            assert cluster_map[v] == data['cluster']

    def test_extract_cluster_level_topology(self):
        t = algorithms.IcnTopology(fnss.line_topology(6))
        t.graph['icr_candidates'] = set(t.nodes())
        clusters = [{0, 1}, {2, 3}, {4, 5}]
        algorithms.deploy_clusters(t, clusters)
        ct = algorithms.extract_cluster_level_topology(t)
        assert len(clusters) == len(ct)

    def test_extract_cluster_level_topology_1_cluster(self):
        t = algorithms.IcnTopology(fnss.line_topology(3))
        t.graph['icr_candidates'] = set(t.nodes())
        clusters = [t.graph['icr_candidates']]
        algorithms.deploy_clusters(t, clusters)
        ct = algorithms.extract_cluster_level_topology(t)
        assert 1 == len(clusters)
        assert 1 == ct.number_of_nodes()


class TestPMedian(object):

    def test_p_median(self):
        # Test topology:
        #
        # A ---- B ---- C ----[HIGH DIST] --- D --- E --- F
        #
        # Expected facilities: 1, 4
        t = fnss.Topology()
        nx.add_path(t, "ABCDEF")
        fnss.set_weights_constant(t, 1)
        fnss.set_weights_constant(t, 2, [("C", "D")])
        distances = dict(nx.all_pairs_dijkstra_path_length(t, weight='weight'))
        allocation, facilities, cost = algorithms.compute_p_median(distances, 2)
        assert allocation == {"A": "B", "B": "B", "C": "B", "D": "E", "E": "E", "F": "E", }
        assert facilities == set("BE")
        assert cost == 4

    def test_p_median_unsorted(self):
        # Test topology:
        #
        # A ---- C ---- B ----[HIGH DIST] --- E --- D --- F
        #
        # Expected facilities: 1, 4
        t = fnss.Topology()
        nx.add_path(t, "ACBEDF")
        fnss.set_weights_constant(t, 1)
        fnss.set_weights_constant(t, 2, [("B", "E")])
        distances = dict(nx.all_pairs_dijkstra_path_length(t, weight='weight'))
        allocation, facilities, cost = algorithms.compute_p_median(distances, 2)
        assert allocation == {"A": "C", "B": "C", "C": "C", "D": "D", "E": "D", "F": "D", }
        assert facilities == set("CD")
        assert cost == 4

    def test_p_median_3(self):
        # Test topology:
        #
        # A ---- C ---- B ----[HIGH DIST] --- E --- D --- F
        #
        # Expected facilities: 1, 4
        t = fnss.Topology()
        nx.add_path(t, "ACBEDF")
        fnss.set_weights_constant(t, 1)
        fnss.set_weights_constant(t, 2, [("B", "E")])
        distances = dict(nx.all_pairs_dijkstra_path_length(t, weight='weight'))
        allocation, facilities, cost = algorithms.compute_p_median(distances, 3)
        assert cost == 3

    def test_p_median_4(self):
        #
        # Test topology:
        #
        # A ---- C ---- B ----[HIGH DIST] --- E --- D --- F
        #
        # Expected facilities: 1, 4
        t = fnss.Topology()
        nx.add_path(t, "ACBEDF")
        fnss.set_weights_constant(t, 1)
        fnss.set_weights_constant(t, 2, [("B", "E")])
        distances = dict(nx.all_pairs_dijkstra_path_length(t, weight='weight'))
        allocation, facilities, cost = algorithms.compute_p_median(distances, 4)
        assert cost == 2

    def test_p_median_6(self):
        # Test topology:
        #
        # A ---- C ---- B ----[HIGH DIST] --- E --- D --- F
        #
        # Expected facilities: 1, 4
        t = fnss.Topology()
        nx.add_path(t, "ACBEDF")
        fnss.set_weights_constant(t, 1)
        fnss.set_weights_constant(t, 2, [("B", "E")])
        distances = dict(nx.all_pairs_dijkstra_path_length(t, weight='weight'))
        allocation, facilities, cost = algorithms.compute_p_median(distances, 6)
        assert allocation == {i: i for i in "ABCDEF"}
        assert facilities == set("ABCDEF")
        assert cost == 0
