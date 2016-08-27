import unittest

import icarus.scenarios as topology


class TestTree(unittest.TestCase):

    def test_tree(self):
        t = topology.topology_tree(2, 3)
        self.assertEqual(6, len(t.graph['icr_candidates']))
        self.assertEqual(1, len(t.sources()))
        self.assertEqual(8, len(t.receivers()))


class TestPath(unittest.TestCase):

    def test_path(self):
        t = topology.topology_path(5)
        self.assertEqual(3, len(t.graph['icr_candidates']))
        self.assertEqual(1, len(t.sources()))
        self.assertEqual(1, len(t.receivers()))


class TestRing(unittest.TestCase):

    def test_ring(self):
        n = 5
        delay_int = 1
        delay_ext = 2
        t = topology.topology_ring(n, delay_int, delay_ext)
        self.assertEqual(n, len(t.graph['icr_candidates']))
        self.assertEqual(1, len(t.sources()))
        self.assertEqual(n, len(t.receivers()))
        self.assertEqual(2 * n + 1, t.number_of_nodes())
        self.assertEqual(2 * n + 1, t.number_of_edges())


class TestMesh(unittest.TestCase):

    def test_mesh(self):
        n = 5
        m = 3
        delay_int = 1
        delay_ext = 2
        t = topology.topology_mesh(n, m, delay_int, delay_ext)
        self.assertEqual(n, len(t.graph['icr_candidates']))
        self.assertEqual(m, len(t.sources()))
        self.assertEqual(n, len(t.receivers()))
        self.assertEqual(2 * n + m, t.number_of_nodes())
        self.assertEqual(m + n + n * (n - 1) / 2, t.number_of_edges())


class TestRocketFuel(unittest.TestCase):

    def test_rocketfuel(self):
        t = topology.topology_rocketfuel_latency(1221, 0.1, 20)
        self.assertEqual(len(t.receivers()), len(t.graph['icr_candidates']))
