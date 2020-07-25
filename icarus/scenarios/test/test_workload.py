import icarus.scenarios as workload


class TestYCBS(object):

    def test_a(self):
        n_items = 5
        event = list(workload.YCSBWorkload("A", n_items, 1, 2))
        assert len(event) == 3
        ev_1 = event[0]
        assert not event[0]['log']
        assert ev_1['item'] in range(1, n_items + 1)
        assert ev_1['op'] in ["READ", "UPDATE"]
        ev_2 = event[1]
        assert ev_2['log']
        assert ev_2['item'] in range(1, n_items + 1)
        assert ev_2['op'] in ["READ", "UPDATE"]
        ev_3 = event[2]
        assert ev_3['log']
        assert ev_3['item'] in range(1, n_items + 1)
        assert ev_3['op'] in ["READ", "UPDATE"]

    def test_b(self):
        n_items = 5
        event = list(workload.YCSBWorkload("B", n_items, 1, 2))
        assert len(event) == 3
        ev_1 = event[0]
        assert not event[0]['log']
        assert ev_1['item'] in range(1, n_items + 1)
        assert ev_1['op'] in ["READ", "UPDATE"]
        ev_2 = event[1]
        assert ev_2['log']
        assert ev_2['item'] in range(1, n_items + 1)
        assert ev_2['op'] in ["READ", "UPDATE"]
        ev_3 = event[2]
        assert ev_3['log']
        assert ev_3['item'] in range(1, n_items + 1)
        assert ev_3['op'] in ["READ", "UPDATE"]

    def test_c(self):
        n_items = 5
        event = list(workload.YCSBWorkload("C", n_items, 1, 2))
        assert len(event) == 3
        ev_1 = event[0]
        assert not event[0]['log']
        assert ev_1['item'] in range(1, n_items + 1)
        assert ev_1['op'] == "READ"
        ev_2 = event[1]
        assert ev_2['log']
        assert ev_2['item'] in range(1, n_items + 1)
        assert ev_2['op'] == "READ"
        ev_3 = event[2]
        assert ev_3['log']
        assert ev_3['item'] in range(1, n_items + 1)
        assert ev_3['op'] == "READ"

    def test_iter(self):
        for event in workload.YCSBWorkload("C", 5, 1, 2):
            assert 'op' in event
            assert 'item' in event
            assert 'log' in event
