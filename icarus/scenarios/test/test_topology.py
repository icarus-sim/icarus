import icarus.scenarios as topology

def test_tree():
    t = topology.topology_tree(2, 3)
    assert 6 == len(t.graph['icr_candidates'])
    assert 1 == len(t.sources())
    assert 8 == len(t.receivers())

def test_path():
    t = topology.topology_path(5)
    assert 3 == len(t.graph['icr_candidates'])
    assert 1 == len(t.sources())
    assert 1 == len(t.receivers())

def test_ring():
    n = 5
    delay_int = 1
    delay_ext = 2
    t = topology.topology_ring(n, delay_int, delay_ext)
    assert n == len(t.graph['icr_candidates'])
    assert 1 == len(t.sources())
    assert n == len(t.receivers())
    assert 2 * n + 1 == t.number_of_nodes()
    assert 2 * n + 1 == t.number_of_edges()

def test_mesh():
    n = 5
    m = 3
    delay_int = 1
    delay_ext = 2
    t = topology.topology_mesh(n, m, delay_int, delay_ext)
    assert n == len(t.graph['icr_candidates'])
    assert m == len(t.sources())
    assert n == len(t.receivers())
    assert 2 * n + m == t.number_of_nodes()
    assert m + n + n * (n - 1) / 2 == t.number_of_edges()

def test_rocketfuel():
    t = topology.topology_rocketfuel_latency(1221, 0.1, 20)
    assert len(t.receivers()) == len(t.graph['icr_candidates'])
