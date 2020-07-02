import unittest

import icarus.scenarios as workload


class TestYCBS(unittest.TestCase):

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

    def test_a(self):
        n_items = 5
        event = list(workload.YCSBWorkload("A", n_items, 1, 2))
        self.assertEqual(len(event), 3)
        ev_1 = event[0]
        self.assertFalse(event[0]['log'])
        self.assertIn(ev_1['item'], range(1, n_items + 1))
        self.assertIn(ev_1['op'], ["READ", "UPDATE"])
        ev_2 = event[1]
        self.assertTrue(ev_2['log'])
        self.assertIn(ev_2['item'], range(1, n_items + 1))
        self.assertIn(ev_2['op'], ["READ", "UPDATE"])
        ev_3 = event[2]
        self.assertTrue(ev_3['log'])
        self.assertIn(ev_3['item'], range(1, n_items + 1))
        self.assertIn(ev_3['op'], ["READ", "UPDATE"])

    def test_b(self):
        n_items = 5
        event = list(workload.YCSBWorkload("B", n_items, 1, 2))
        self.assertEqual(len(event), 3)
        ev_1 = event[0]
        self.assertFalse(event[0]['log'])
        self.assertIn(ev_1['item'], range(1, n_items + 1))
        self.assertIn(ev_1['op'], ["READ", "UPDATE"])
        ev_2 = event[1]
        self.assertTrue(ev_2['log'])
        self.assertIn(ev_2['item'], range(1, n_items + 1))
        self.assertIn(ev_2['op'], ["READ", "UPDATE"])
        ev_3 = event[2]
        self.assertTrue(ev_3['log'])
        self.assertIn(ev_3['item'], range(1, n_items + 1))
        self.assertIn(ev_3['op'], ["READ", "UPDATE"])

    def test_c(self):
        n_items = 5
        event = list(workload.YCSBWorkload("C", n_items, 1, 2))
        self.assertEqual(len(event), 3)
        ev_1 = event[0]
        self.assertFalse(event[0]['log'])
        self.assertIn(ev_1['item'], range(1, n_items + 1))
        self.assertEqual(ev_1['op'], "READ")
        ev_2 = event[1]
        self.assertTrue(ev_2['log'])
        self.assertIn(ev_2['item'], range(1, n_items + 1))
        self.assertEqual(ev_2['op'], "READ")
        ev_3 = event[2]
        self.assertTrue(ev_3['log'])
        self.assertIn(ev_3['item'], range(1, n_items + 1))
        self.assertEqual(ev_3['op'], "READ")

    def test_iter(self):
        for event in workload.YCSBWorkload("C", 5, 1, 2):
            self.assertIn('op', event)
            self.assertIn('item', event)
            self.assertIn('log', event)
