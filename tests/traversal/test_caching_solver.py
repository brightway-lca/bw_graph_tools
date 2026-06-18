import numpy as np
import pytest
import scipy.sparse as sp
from bw2calc import LCA, factorized, spsolve
from bw2data import Database, Method
from bw2data.tests import bw2test

from bw_graph_tools import GraphTraversalSettings, NewNodeEachVisitGraphTraversal
from bw_graph_tools.graph_traversal.utils import CachingSolver


class MatrixMockLCA:
    """LCA-like object exposing a real technosphere matrix for the batched `scores` path.

    Mirrors the relevant bits of ``bw2calc.LCA``: ``decompose_technosphere`` builds ``solver`` and
    ``solve_linear_system`` reuses it, as the iterative (non-PARDISO) path expects.
    """

    def __init__(self, technosphere):
        self.technosphere_matrix = technosphere
        self.demand_array = np.zeros(technosphere.shape[0])

    def decompose_technosphere(self):
        self.solver = factorized(self.technosphere_matrix.tocsc())

    def solve_linear_system(self, demand=None):
        if demand is None:
            demand = self.demand_array
        if hasattr(self, "solver"):
            return self.solver(demand)
        return spsolve(self.technosphere_matrix, demand)


def _score_solver():
    A = sp.csc_matrix(np.array([[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [1.0, 0.0, 4.0]]))
    solver = CachingSolver(MatrixMockLCA(A))
    solver.score_row = np.array([1.0, 1.0, 1.0])
    return solver


def test_in_cache_empty():
    assert _score_solver().in_cache({0, 1, 2}) == set()


def test_in_cache_after_scores():
    solver = _score_solver()
    solver.scores([2], [1.0])
    assert solver.in_cache({0, 1, 2}) == {2}
    assert solver.in_cache({0, 1}) == set()


def test_in_cache_after_add_to_cache():
    solver = _score_solver()
    solver.add_to_cache(7, 3.5)
    assert solver.in_cache({5, 6, 7}) == {7}
    assert solver.in_cache({5, 6}) == set()


def test_add_to_cache_prevents_recalculation():
    """A pre-populated score is used directly, without solving."""
    solver = _score_solver()
    solver.add_to_cache(0, 42.0)

    solver._unit_scores_iterative = lambda indices: pytest.fail(
        "should not solve a cached index"
    )
    solver._unit_scores_pardiso = solver._unit_scores_iterative

    assert solver.scores([0], [2.0]) == [84.0]


def test_iterative_path_decomposes_technosphere_once():
    """Without PARDISO, the LCA is decomposed once and `lca.solver` is reused for solves."""
    A = sp.csc_matrix(np.array([[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [1.0, 0.0, 4.0]]))
    lca = MatrixMockLCA(A)
    solver = CachingSolver(lca)
    solver.score_row = np.array([1.0, 1.0, 1.0])

    decompositions = []
    original = lca.decompose_technosphere
    lca.decompose_technosphere = lambda: decompositions.append(1) or original()

    assert not hasattr(lca, "solver")
    solver._unit_scores_iterative([0, 1])
    assert hasattr(lca, "solver"), "technosphere should be decomposed"
    solver._unit_scores_iterative([2])
    assert decompositions == [1], "should decompose only once and reuse `lca.solver`"


def test_set_score_row_from_characterized_biosphere():
    """`set_score_row` stores the column sums of the characterized biosphere matrix."""
    cb = sp.csr_matrix(np.array([[1.0, 2.0, 0.0], [0.0, 1.0, 3.0]]))
    solver = CachingSolver(MatrixMockLCA(sp.csc_matrix(np.eye(3))))
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
    # Independent reference: solve each demand vector directly and reduce with the full
    # characterized biosphere matrix.
    reference = []
    for index, amount in zip(indices, amounts):
        demand = np.zeros(lca.technosphere_matrix.shape[0])
        demand[index] = 1
        supply = spsolve(lca.technosphere_matrix, demand)
        reference.append(float((cb * supply).sum()) * amount)
    assert np.allclose(batched, reference)


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
