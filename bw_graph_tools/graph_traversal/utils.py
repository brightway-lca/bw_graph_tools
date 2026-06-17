import numpy as np
from bw2calc import PYPARDISO, LCA, factorized, spsolve
from scipy.sparse import spmatrix

from bw_graph_tools.graph_traversal.graph_objects import Node


class CachingSolver:
    """Class which caches expensive linear algebra solutions.

    Two caches are maintained:

    * ``_cache`` stores full supply vectors keyed by product index, used by the legacy
      ``calculate``/``__call__`` interface.
    * ``_score_cache`` stores per-unit *cumulative LCA scores* (scalars) keyed by product index,
      used by the batched ``scores`` interface.

    The graph traversal only needs cumulative scores, not the full supply vectors. The batched
    ``scores`` method follows the same strategy as ``bw2calc.FastSupplyArraysMixin``:

    * With PARDISO (``pypardiso``), all requested products are solved in a single
      multi-right-hand-side ``spsolve`` call, which reuses the cached factorization and is much
      faster than solving one product at a time.
    * Otherwise (UMFPACK / SuperLU), a single multi-right-hand-side solve is *slower* than reusing
      a cached factorization, so the technosphere matrix is factorized once and each product is
      solved iteratively.
    """

    def __init__(self, lca: LCA):
        self.lca = lca
        self._cache = {}
        self._score_cache = {}
        # Cached LU factorization of the technosphere matrix, used by the iterative (non-PARDISO)
        # path. Built lazily on first use.
        self._factorized_solver = None
        # 1-D array of per-activity characterized scores (column sums of the characterized
        # biosphere matrix). Set by `set_score_row` before `scores` is called.
        self.score_row = None

    def in_cache(self, indices: set[int]) -> set[int]:
        """Return all `indices` values which are in the supply vector cache."""
        return indices & self._cache.keys()

    def add_to_cache(self, index: int, result: np.ndarray) -> None:
        """Store a pre-computed supply vector. Result must be for a demand amount of 1."""
        self._cache[index] = result

    def _calculate(self, index: int) -> np.ndarray:
        self.lca.demand_array[:] = 0
        self.lca.demand_array[index] = 1
        return self.lca.solve_linear_system()

    def calculate(self, index: int) -> np.ndarray:
        """Compute the supply vector for one unit of a given product."""
        if index not in self._cache:
            self._cache[index] = self._calculate(index)
        return self._cache[index]

    def __call__(self, index: int, amount: float) -> np.ndarray:
        return self.calculate(index) * amount

    def set_score_row(self, characterized_biosphere: spmatrix) -> None:
        """Pre-compute the per-activity score row used to reduce supply vectors to scores.

        ``characterized_biosphere`` is the characterization-times-biosphere matrix (biosphere
        flows by activities). Its column sums give, for each activity, the cumulative score per
        unit of supply, so that ``score_row @ supply`` equals
        ``(characterized_biosphere * supply).sum()``.
        """
        self.score_row = np.asarray(characterized_biosphere.sum(axis=0)).ravel()

    def scores(self, indices: list[int], amounts: list[float]) -> list[float]:
        """Compute cumulative LCA scores for several products in a single batched solve.

        Parameters
        ----------
        indices : list[int]
            Product (technosphere row) indices to demand, one unit each.
        amounts : list[float]
            Demanded amount for each product index, in the same order.

        Returns
        -------
        list[float]
            Cumulative LCA score for each `(index, amount)` pair, in input order.
        """
        missing = [index for index in indices if index not in self._score_cache]
        if missing:
            if PYPARDISO:
                unit_scores = self._unit_scores_pardiso(missing)
            else:
                unit_scores = self._unit_scores_iterative(missing)
            for index, score in zip(missing, unit_scores):
                self._score_cache[index] = float(score)
        return [
            self._score_cache[index] * amount for index, amount in zip(indices, amounts)
        ]

    def _unit_scores_pardiso(self, indices: list[int]) -> np.ndarray:
        """Solve all `indices` in a single multi-right-hand-side PARDISO solve."""
        matrix = self.lca.technosphere_matrix
        demand = np.zeros((matrix.shape[0], len(indices)))
        for column, index in enumerate(indices):
            demand[index, column] = 1
        supply = spsolve(matrix, demand)
        # `spsolve` may squeeze a single right-hand-side down to one dimension.
        if supply.ndim == 1:
            supply = supply.reshape(-1, 1)
        return np.asarray(self.score_row @ supply).ravel()

    def _unit_scores_iterative(self, indices: list[int]) -> np.ndarray:
        """Solve each of `indices` separately, reusing one cached LU factorization.

        A single multi-right-hand-side solve is slower than this under UMFPACK / SuperLU, so we
        mirror ``bw2calc.FastSupplyArraysMixin._calculate_umfpack``.
        """
        if self._factorized_solver is None:
            self._factorized_solver = factorized(self.lca.technosphere_matrix.tocsc())
        demand = np.zeros(self.lca.technosphere_matrix.shape[0])
        unit_scores = np.empty(len(indices))
        for position, index in enumerate(indices):
            demand[index] = 1
            unit_scores[position] = self.score_row @ self._factorized_solver(demand)
            demand[index] = 0
        return unit_scores


class Counter:
    """Custom counter to have easy access to current value"""

    def __init__(self):
        self.value = -1

    def __next__(self):
        self.value += 1
        return self.value

    def __gt__(self, other):
        return self.value > other


def get_demand_vector_for_activity(
    node: Node,
    skip_coproducts: bool,
    matrix: spmatrix,
) -> (list[int], list[float]):
    """
    Get input matrix indices and amounts for a given activity. Ignores the reference production
    exchanges and optionally other co-production exchanges.

    Parameters
    ----------
    node : `Node`
        Activity whose inputs we are iterating over
    skip_coproducts : bool
        Whether or not to ignore positive production exchanges other than the reference
        product, which is always ignored
    matrix : scipy.sparse.spmatrix
        Technosphere matrix

    Returns
    -------

    row indices : list
        Integer row indices for products consumed by `Node`
    amounts : list
        The amount of each product consumed, scaled to `Node.supply_amount`. Same order as row
        indices.

    """
    matrix = (-1 * node.supply_amount * matrix[:, node.activity_index]).tocoo()

    rows, vals = [], []
    for x, y in zip(matrix.row, matrix.data):
        if x == node.reference_product_index:
            continue
        elif y == 0:
            continue
        elif y < 0 and skip_coproducts:
            continue
        rows.append(x)
        vals.append(y)
    return rows, vals
