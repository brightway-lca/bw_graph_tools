import numpy as np
import pytest
from bw2calc import LCA
from bw2data import Database, Method
from bw2data.tests import bw2test

from bw_graph_tools import GraphTraversalSettings, NewNodeEachVisitGraphTraversal
from bw_graph_tools.graph_traversal.utils import CachingSolver


class MockLCA:
    """Minimal LCA-like object for unit-testing CachingSolver without a real database."""

    def __init__(self, size=5):
        self.demand_array = np.zeros(size)

    def solve_linear_system(self):
        return self.demand_array.copy()


def test_in_cache_empty():
    solver = CachingSolver(MockLCA())
    assert solver.in_cache({0, 1, 2}) == set()


def test_in_cache_after_calculate():
    solver = CachingSolver(MockLCA())
    solver.calculate(2)
    assert solver.in_cache({0, 1, 2}) == {2}
    assert solver.in_cache({0, 1}) == set()


def test_in_cache_after_add_to_cache():
    solver = CachingSolver(MockLCA())
    result = np.array([1.0, 2.0, 3.0])
    solver.add_to_cache(7, result)
    assert solver.in_cache({5, 6, 7}) == {7}
    assert solver.in_cache({5, 6}) == set()


def test_add_to_cache_is_returned_by_calculate():
    """Pre-populated cache values are used by calculate, bypassing _calculate."""
    solver = CachingSolver(MockLCA())
    sentinel = np.array([99.0, 98.0, 97.0])
    solver.add_to_cache(3, sentinel)
    result = solver.calculate(3)
    assert result is sentinel


def test_add_to_cache_prevents_recalculation():
    """calculate() should not call _calculate when the index is already cached."""
    solver = CachingSolver(MockLCA())
    sentinel = np.array([42.0])
    solver.add_to_cache(0, sentinel)

    called = []
    original = solver._calculate
    solver._calculate = lambda idx: called.append(idx) or original(idx)

    solver.calculate(0)
    assert called == [], "_calculate should not be called for a cached index"


@bw2test
def test_injected_caching_solver_is_used():
    """A CachingSolver passed via settings is used instead of a fresh one."""
    Database("bio").write(
        {
            ("bio", "a"): {"type": "emission", "name": "a", "exchanges": []},
        }
    )
    Database("t").write(
        {
            ("t", "1"): {
                "name": "1",
                "exchanges": [
                    {"input": ("bio", "a"), "amount": 1.0, "type": "biosphere"},
                    {"input": ("t", "1"), "amount": 1, "type": "production"},
                    {"input": ("t", "2"), "amount": 1, "type": "technosphere"},
                ],
            },
            ("t", "2"): {
                "name": "2",
                "exchanges": [
                    {"input": ("bio", "a"), "amount": 0.5, "type": "biosphere"},
                    {"input": ("t", "2"), "amount": 1, "type": "production"},
                ],
            },
        }
    )
    Method(("test",)).write([(("bio", "a"), 1)])

    lca = LCA({("t", "1"): 1}, ("test",))
    lca.lci()
    lca.lcia()

    # First traversal — build up a solver with a warm cache
    gt1 = NewNodeEachVisitGraphTraversal(lca, GraphTraversalSettings())
    gt1.traverse()
    solver = gt1._caching_solver
    cached_after_first = set(solver._cache.keys())
    assert len(cached_after_first) > 0, "First traversal should populate the cache"

    # Second traversal — inject the same solver
    gt2 = NewNodeEachVisitGraphTraversal(
        lca, GraphTraversalSettings(caching_solver=solver)
    )
    assert gt2._caching_solver is solver, "Injected solver should be used directly"
    # Cache should already contain the indices from the first traversal
    assert solver.in_cache(cached_after_first) == cached_after_first
