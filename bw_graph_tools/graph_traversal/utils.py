from functools import lru_cache

import numpy as np
from bw2calc import LCA
from scipy.sparse import spmatrix

from bw_graph_tools.graph_traversal.graph_objects import Node


class CachingSolver:
    """Class which caches expensive linear algebra solution vectors."""

    def __init__(self, lca: LCA):
        self.lca = lca

    @lru_cache(maxsize=8096)
    def calculate(self, index: int) -> np.ndarray:
        """Compute cumulative LCA score for one unit of a given activity"""
        self.lca.demand_array[:] = 0
        self.lca.demand_array[index] = 1
        return self.lca.solve_linear_system()

    def __call__(self, index: int, amount: float) -> np.ndarray:
        return self.calculate(index) * amount


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
