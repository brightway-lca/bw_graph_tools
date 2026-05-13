import bw_processing as bwp
import matrix_utils as mu
import numpy as np
import pytest

from bw_graph_tools.errors import UnclearProductionExchange
from bw_graph_tools.matrix_tools import gpe_fifth_heuristic, guess_production_exchanges


def _make_mm(indices, data):
    dp = bwp.create_datapackage()
    dp.add_persistent_vector(
        matrix="test",
        indices_array=np.array(indices, dtype=bwp.INDICES_DTYPE),
        name="foo",
        data_array=np.array(data, dtype=float),
    )
    return mu.MappedMatrix(packages=[dp], matrix="test")


def test_fifth_heuristic_basic():
    # col 0 has rows [0, 1], col 1 has rows [1, 2].
    # row 0 → unique to col 0, row 2 → unique to col 1; row 1 shared (skipped).
    # Each column has exactly one uniquely-pointing row → both assigned.
    mm = _make_mm([(0, 0), (1, 0), (1, 1), (2, 1)], [1, 2, 3, 4])
    row, col = gpe_fifth_heuristic(mm=mm, row_existing=np.array([]), col_existing=np.array([]))
    assert set(zip(row.tolist(), col.tolist())) == {(0, 0), (2, 1)}


def test_fifth_heuristic_all_shared():
    # All rows appear in both columns → no unique row, nothing assigned.
    mm = _make_mm([(0, 0), (1, 0), (0, 1), (1, 1)], [1, 2, 3, 4])
    row, col = gpe_fifth_heuristic(mm=mm, row_existing=np.array([]), col_existing=np.array([]))
    assert row.size == 0
    assert col.size == 0


def test_fifth_heuristic_two_unique_rows_same_col():
    # col 0 has rows [0, 1], col 1 has rows [2, 3].
    # rows 0 and 1 are each unique to col 0; rows 2 and 3 unique to col 1.
    # Both cols have two uniquely-pointing rows → ambiguous → nothing assigned.
    mm = _make_mm([(0, 0), (1, 0), (2, 1), (3, 1)], [1, 2, 3, 4])
    row, col = gpe_fifth_heuristic(mm=mm, row_existing=np.array([]), col_existing=np.array([]))
    assert row.size == 0
    assert col.size == 0


def test_fifth_heuristic_one_resolved_one_ambiguous():
    # col 0 has row [0] only → unique, single → assigned.
    # col 1 has rows [1, 2], col 2 has rows [1, 3]: row 1 shared, row 2 unique to col 1,
    # row 3 unique to col 2 → col 1 and col 2 each have one uniquely-pointing row → assigned.
    mm = _make_mm([(0, 0), (1, 1), (2, 1), (1, 2), (3, 2)], [5, 1, 2, 3, 4])
    row, col = gpe_fifth_heuristic(mm=mm, row_existing=np.array([]), col_existing=np.array([]))
    assert set(zip(row.tolist(), col.tolist())) == {(0, 0), (2, 1), (3, 2)}


def test_fifth_heuristic_skips_already_found():
    # col 0 already in col_existing; col 1 has row 1 unique to it → only col 1 appended.
    mm = _make_mm([(0, 0), (1, 1)], [1, 2])
    row, col = gpe_fifth_heuristic(
        mm=mm, row_existing=np.array([0]), col_existing=np.array([0])
    )
    assert np.array_equal(row, [0, 1])
    assert np.array_equal(col, [0, 1])


def test_fifth_heuristic_no_missing_cols():
    # All columns already identified → returned unchanged immediately.
    mm = _make_mm([(0, 0), (1, 1)], [1, 2])
    row, col = gpe_fifth_heuristic(
        mm=mm, row_existing=np.array([0, 1]), col_existing=np.array([0, 1])
    )
    assert np.array_equal(row, [0, 1])
    assert np.array_equal(col, [0, 1])


def test_guess_production_exchanges_fifth_heuristic_fails():
    # 3×3 matrix where all four earlier heuristics fail and the fifth also cannot resolve.
    # Row IDs (100-102) and col IDs (200-202) are non-overlapping so the first heuristic
    # finds nothing.  Every column has two positive entries (bypasses third) and no negatives
    # (bypasses fourth).  The three columns form a cycle — every row appears in exactly two
    # columns — so no row is unique to any one column and the fifth heuristic also fails.
    mm = _make_mm(
        [(100, 200), (101, 200), (101, 201), (102, 201), (100, 202), (102, 202)],
        [1, 2, 3, 4, 5, 6],
    )
    with pytest.raises(UnclearProductionExchange):
        guess_production_exchanges(mm)


def test_guess_production_exchanges_fifth_heuristic_resolves_all():
    # 4×4 matrix where the fifth heuristic resolves the two columns left after the first.
    #
    # IDs 0–3 are used for both rows and columns.  Diagonal entries (0,0) and (1,1) let the
    # first heuristic identify cols 0 and 1.  Entry (3,0) exists only to make the four row
    # IDs distinct so the matrix is square.
    #
    # Remaining cols 2 and 3 each have two positive entries (bypasses third heuristic):
    #   col 2: rows [0, 1]  — row 0 shared with col 3; row 1 unique to col 2
    #   col 3: rows [0, 2]  — row 0 shared with col 2; row 2 unique to col 3
    #
    # The fifth heuristic assigns row 1 → col 2 and row 2 → col 3.
    mm = _make_mm(
        [(0, 0), (3, 0), (1, 1), (0, 2), (1, 2), (0, 3), (2, 3)],
        [1, 7, 2, 3, 4, 5, 6],
    )
    row, col = guess_production_exchanges(mm)
    # Matrix IDs map identically (0→0, 1→1, 2→2, 3→3) so we can use raw IDs directly.
    assert set(zip(row.tolist(), col.tolist())) == {(0, 0), (1, 1), (1, 2), (2, 3)}
