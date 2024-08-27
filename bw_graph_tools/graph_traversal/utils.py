from bw2calc import LCA
import numpy as np
from functools import lru_cache


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
