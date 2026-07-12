import bw_processing as bwp
import matrix_utils as mu
import numpy as np
import pytest

from bw_graph_tools.errors import UnclearProductionExchange
from bw_graph_tools.matrix_tools import gpe_zeroth_heuristic, guess_production_exchanges


def _pairs(row, col):
    """Return the set of (row, col) matrix-index pairs, order-independent."""
    return {(int(r), int(c)) for r, c in zip(row, col)}


def test_gpe_zeroth_heuristic_basic():
    dp = bwp.create_datapackage()
    indices = np.array([(0, 0), (1, 0), (0, 1), (1, 1)], dtype=bwp.INDICES_DTYPE)
    dp.add_persistent_vector(
        matrix="test",
        indices_array=indices,
        name="foo",
        data_array=np.array([1.0, 1.0, -1.0, -1.0]),
        reference_array=np.array([True, False, False, True], dtype=bool),
    )
    mm = mu.MappedMatrix(packages=[dp], matrix="test")
    row, col = gpe_zeroth_heuristic(mm)
    assert _pairs(row, col) == {(0, 0), (1, 1)}


def test_gpe_zeroth_heuristic_no_reference_array():
    dp = bwp.create_datapackage()
    indices = np.array([(0, 0), (1, 1)], dtype=bwp.INDICES_DTYPE)
    dp.add_persistent_vector(
        matrix="test",
        indices_array=indices,
        name="foo",
        data_array=np.array([1.0, 1.0]),
    )
    mm = mu.MappedMatrix(packages=[dp], matrix="test")
    row, col = gpe_zeroth_heuristic(mm)
    assert row.shape == (0,)
    assert col.shape == (0,)


def test_gpe_zeroth_heuristic_multiple_dp_one_without_reference():
    dp1 = bwp.create_datapackage()
    dp1.add_persistent_vector(
        matrix="test",
        indices_array=np.array([(0, 0), (1, 0)], dtype=bwp.INDICES_DTYPE),
        name="foo",
        data_array=np.array([1.0, -1.0]),
        reference_array=np.array([False, True], dtype=bool),
    )
    dp2 = bwp.create_datapackage()
    dp2.add_persistent_vector(
        matrix="test",
        indices_array=np.array([(0, 1), (1, 1)], dtype=bwp.INDICES_DTYPE),
        name="bar",
        data_array=np.array([1.0, 1.0]),
    )
    mm = mu.MappedMatrix(packages=[dp1, dp2], matrix="test")
    row, col = gpe_zeroth_heuristic(mm)
    # Only dp1 carries reference flags; the flagged entry is (1, 0).
    assert _pairs(row, col) == {(1, 0)}


def test_guess_production_exchanges_reference_overrides_first_heuristic():
    # Same product/activity id space, so the first (diagonal) heuristic would
    # normally claim column 0 at row 0. An explicit reference flag on (1, 0)
    # must win instead.
    dp = bwp.create_datapackage()
    indices = np.array([(0, 0), (1, 1), (1, 0)], dtype=bwp.INDICES_DTYPE)
    dp.add_persistent_vector(
        matrix="test",
        indices_array=indices,
        name="foo",
        data_array=np.array([1.0, 1.0, 1.0]),
        reference_array=np.array([False, False, True], dtype=bool),
    )
    mm = mu.MappedMatrix(packages=[dp], matrix="test")
    row, col = guess_production_exchanges(mm)
    # Column 0 -> row 1 (reference wins), column 1 -> row 1 (first heuristic).
    assert dict(zip(col.tolist(), row.tolist())) == {0: 1, 1: 1}


# The co-production loop that the structural heuristics cannot resolve:
# activity A (col 20) produces product Y (row 10) and waste Z (row 11);
# activity B (col 21) consumes Y and treats Z. Products and activities have
# disjoint id spaces, both of A's exchanges are positive, and both of B's are
# negative, so no sign/flip/uniqueness rule can pick the reference exchange.
_LOOP_INDICES = np.array(
    [(10, 20), (11, 20), (10, 21), (11, 21)], dtype=bwp.INDICES_DTYPE
)
_LOOP_DATA = np.array([1.0, 1.0, -1.0, -1.0])


def test_guess_production_exchanges_coproduction_raises_without_reference():
    dp = bwp.create_datapackage()
    dp.add_persistent_vector(
        matrix="test",
        indices_array=_LOOP_INDICES,
        name="foo",
        data_array=_LOOP_DATA,
    )
    mm = mu.MappedMatrix(packages=[dp], matrix="test")
    with pytest.raises(UnclearProductionExchange):
        guess_production_exchanges(mm)


def test_guess_production_exchanges_coproduction_resolved_with_reference():
    dp = bwp.create_datapackage()
    dp.add_persistent_vector(
        matrix="test",
        indices_array=_LOOP_INDICES,
        name="foo",
        data_array=_LOOP_DATA,
        # A's reference is Y (10, 20); B's reference is Z (11, 21).
        reference_array=np.array([True, False, False, True], dtype=bool),
    )
    mm = mu.MappedMatrix(packages=[dp], matrix="test")
    row, col = guess_production_exchanges(mm)
    # rows 10/11 map to matrix rows 0/1, cols 20/21 map to matrix cols 0/1.
    # Y (row 0) is A's (col 0) reference; Z (row 1) is B's (col 1) reference.
    assert dict(zip(col.tolist(), row.tolist())) == {0: 0, 1: 1}
