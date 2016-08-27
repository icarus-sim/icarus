import unittest

from icarus.results import ResultSet

class TestResultSet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rs = ResultSet()
        cls.cond_a = {'alpha': 1, 'beta': 2, 'gamma': 3}
        cls.cond_b = {'alpha':-1, 'beta': 2, 'gamma': 3}
        cls.cond_c = {'alpha': 1, 'beta':-2, 'gamma': 3}
        cls.metric = {'m1': 1, 'm2': 2, 'm3': 3}
        cls.rs.add(cls.cond_a, cls.metric)
        cls.rs.add(cls.cond_b, cls.metric)
        cls.rs.add(cls.cond_c, cls.metric)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_len(self):
        self.assertEquals(3, len(self.rs))

    def test_getitem(self):
        cond, metric = self.rs[0]
        self.assertEquals(self.cond_a, cond)
        self.assertEquals(self.metric, metric)

    def test_filter_match(self):
        filtered_rs = self.rs.filter({'gamma': 3})
        self.assertEquals(3, len(filtered_rs))
        filtered_rs = self.rs.filter({'beta': 2})
        self.assertEquals(2, len(filtered_rs))
        filtered_rs = self.rs.filter({'beta':-2})
        self.assertEquals(1, len(filtered_rs))
        filtered_rs = self.rs.filter({'alpha': 1, 'beta': 2})
        self.assertEquals(1, len(filtered_rs))
        filtered_rs = self.rs.filter({'gamma': 1})
        self.assertEquals(0, len(filtered_rs))
        filtered_rs = self.rs.filter({'alpha':-1, 'beta':-2})
        self.assertEquals(0, len(filtered_rs))

    def test_json(self):
        a = {"d": [1, 2, "v"], "p": 1}
        b = {"a": "b"}
        rs = ResultSet()
        rs.add(a, b)
        rs.add(b, a)
        self.assertEqual([[a, b], [b, a]], eval(rs.json()))
