from icarus.results import ResultSet


class TestResultSet:
    @classmethod
    def setup_class(cls):
        cls.rs = ResultSet()
        cls.cond_a = {"alpha": 1, "beta": 2, "gamma": 3}
        cls.cond_b = {"alpha": -1, "beta": 2, "gamma": 3}
        cls.cond_c = {"alpha": 1, "beta": -2, "gamma": 3}
        cls.metric = {"m1": 1, "m2": 2, "m3": 3}
        cls.rs.add(cls.cond_a, cls.metric)
        cls.rs.add(cls.cond_b, cls.metric)
        cls.rs.add(cls.cond_c, cls.metric)

    def test_len(self):
        assert 3 == len(self.rs)

    def test_getitem(self):
        cond, metric = self.rs[0]
        assert self.cond_a == cond
        assert self.metric == metric

    def test_filter_match(self):
        filtered_rs = self.rs.filter({"gamma": 3})
        assert 3 == len(filtered_rs)
        filtered_rs = self.rs.filter({"beta": 2})
        assert 2 == len(filtered_rs)
        filtered_rs = self.rs.filter({"beta": -2})
        assert 1 == len(filtered_rs)
        filtered_rs = self.rs.filter({"alpha": 1, "beta": 2})
        assert 1 == len(filtered_rs)
        filtered_rs = self.rs.filter({"gamma": 1})
        assert 0 == len(filtered_rs)
        filtered_rs = self.rs.filter({"alpha": -1, "beta": -2})
        assert 0 == len(filtered_rs)

    def test_json(self):
        a = {"d": [1, 2, "v"], "p": 1}
        b = {"a": "b"}
        rs = ResultSet()
        rs.add(a, b)
        rs.add(b, a)
        assert [[a, b], [b, a]] == eval(rs.json())
