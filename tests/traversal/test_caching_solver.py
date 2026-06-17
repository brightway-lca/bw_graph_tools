import numpy as np
import pytest
import scipy.sparse as sp
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


class MatrixMockLCA:
    """LCA-like object exposing a real technosphere matrix for the batched `scores` path."""

    def __init__(self, technosphere):
        self.technosphere_matrix = technosphere
        self.demand_array = np.zeros(technosphere.shape[0])


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


def test_set_score_row_from_characterized_biosphere():
    """`set_score_row` stores the column sums of the characterized biosphere matrix."""
    cb = sp.csr_matrix(np.array([[1.0, 2.0, 0.0], [0.0, 1.0, 3.0]]))
    solver = CachingSolver(MockLCA())
    solver.set_score_row(cb)
    assert np.allclose(solver.score_row, [1.0, 3.0, 3.0])


def test_scores_batched_values():
    """Batched scores equal `score_row @ A^-1 e_index`, scaled by amount."""
    A = sp.csc_matrix(np.array([[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [1.0, 0.0, 4.0]]))
    solver = CachingSolver(MatrixMockLCA(A))
    solver.score_row = np.array([1.0, 1.0, 1.0])

    result = solver.scores([0, 1], [2.0, 3.0])

    # Reference: solve each column independently and reduce with score_row.
    inverse = np.linalg.inv(A.toarray())
    expected = [
        float(solver.score_row @ inverse[:, 0]) * 2.0,
        float(solver.score_row @ inverse[:, 1]) * 3.0,
    ]
    assert np.allclose(result, expected)


def test_scores_caches_unit_scores():
    """Repeated requests reuse cached unit scores and only solve missing indices."""
    A = sp.csc_matrix(np.array([[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [1.0, 0.0, 4.0]]))
    solver = CachingSolver(MatrixMockLCA(A))
    solver.score_row = np.array([1.0, 1.0, 1.0])

    solver.scores([0], [1.0])
    assert set(solver._score_cache) == {0}

    # Amount scaling comes from the cached unit score, not a re-solve.
    assert np.allclose(solver.scores([0], [5.0]), [solver._score_cache[0] * 5.0])

    solver.scores([0, 1, 2], [1.0, 1.0, 1.0])
    assert set(solver._score_cache) == {0, 1, 2}


def test_scores_empty():
    solver = CachingSolver(MatrixMockLCA(sp.csc_matrix(np.eye(3))))
    solver.score_row = np.ones(3)
    assert solver.scores([], []) == []


@bw2test
def test_batched_scores_match_supply_vector_path():
    """The batched `scores` path agrees with reducing full supply vectors (legacy path)."""
    Database("bio").write(
        {("bio", "a"): {"type": "emission", "name": "a", "exchanges": []}}
    )
    Database("t").write(
        {
            ("t", "1"): {
                "name": "1",
                "exchanges": [
                    {"input": ("bio", "a"), "amount": 1.0, "type": "biosphere"},
                    {"input": ("t", "1"), "amount": 1, "type": "production"},
                    {"input": ("t", "2"), "amount": 0.4, "type": "technosphere"},
                ],
            },
            ("t", "2"): {
                "name": "2",
                "exchanges": [
                    {"input": ("bio", "a"), "amount": 0.5, "type": "biosphere"},
                    {"input": ("t", "2"), "amount": 1, "type": "production"},
                    {"input": ("t", "1"), "amount": 0.1, "type": "technosphere"},
                ],
            },
        }
    )
    Method(("test",)).write([(("bio", "a"), 1)])

    lca = LCA({("t", "1"): 1}, ("test",))
    lca.lci()
    lca.lcia()

    gt = NewNodeEachVisitGraphTraversal(lca, GraphTraversalSettings())
    solver = gt._caching_solver
    cb = gt.characterized_biosphere

    indices = list(range(lca.technosphere_matrix.shape[0]))
    amounts = [1.5] * len(indices)

    batched = solver.scores(indices, amounts)
    legacy = [
        float((cb * solver.calculate(index)).sum()) * amount
        for index, amount in zip(indices, amounts)
    ]
    assert np.allclose(batched, legacy)


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
    # Traversal scores products via the batched `scores` interface, which fills `_score_cache`.
    cached_after_first = set(solver._score_cache.keys())
    assert len(cached_after_first) > 0, "First traversal should populate the score cache"

    # Second traversal — inject the same solver
    gt2 = NewNodeEachVisitGraphTraversal(
        lca, GraphTraversalSettings(caching_solver=solver)
    )
    assert gt2._caching_solver is solver, "Injected solver should be used directly"
    # Score cache should already contain the indices from the first traversal
    assert set(solver._score_cache.keys()) >= cached_after_first
