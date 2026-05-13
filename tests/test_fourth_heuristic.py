import bw_processing as bwp
import matrix_utils as mu
import numpy as np

from bw_graph_tools.matrix_tools import gpe_fourth_heuristic, guess_production_exchanges


def _make_mm(indices, data):
    dp = bwp.create_datapackage()
    dp.add_persistent_vector(
        matrix="test",
        indices_array=np.array(indices, dtype=bwp.INDICES_DTYPE),
        name="foo",
        data_array=np.array(data, dtype=float),
    )
    return mu.MappedMatrix(packages=[dp], matrix="test")


def test_fourth_heuristic_single_negative():
    # col 1 has one negative entry → waste treatment production exchange
    # Matrix:  col0  col1
    #   row0 [  3    2  ]
    #   row1 [  4   -1  ]
    mm = _make_mm([(1, 1), (0, 1), (0, 0), (1, 0)], [-1, 2, 3, 4])
    row, col = gpe_fourth_heuristic(mm=mm, row_existing=np.array([]), col_existing=np.array([]))
    assert np.array_equal(row, [1])
    assert np.array_equal(col, [1])


def test_fourth_heuristic_off_diagonal():
    # col 0 has one negative entry at an off-diagonal position
    # Matrix:  col0  col1
    #   row0 [  0   -1  ]   ← col1 single negative
    #   row1 [ -1    3  ]   ← col0 single negative
    mm = _make_mm([(0, 1), (1, 0), (1, 1)], [-1, -1, 3])
    row, col = gpe_fourth_heuristic(mm=mm, row_existing=np.array([]), col_existing=np.array([]))
    # Both columns have a single negative entry
    assert set(zip(row.tolist(), col.tolist())) == {(0, 1), (1, 0)}


def test_fourth_heuristic_multiple_negatives_per_column():
    # col 1 has two negative entries → ambiguous, should not be identified
    # Matrix:  col0  col1
    #   row0 [  3   -2  ]
    #   row1 [  4   -1  ]
    mm = _make_mm([(1, 1), (0, 1), (0, 0), (1, 0)], [-1, -2, 3, 4])
    row, col = gpe_fourth_heuristic(mm=mm, row_existing=np.array([]), col_existing=np.array([]))
    assert row.size == 0
    assert col.size == 0


def test_fourth_heuristic_overlap_existing():
    # col 1 has a single negative, but is already in col_existing → should be skipped
    mm = _make_mm([(1, 1), (0, 1), (0, 0), (1, 0)], [-1, 2, 3, 4])
    row, col = gpe_fourth_heuristic(
        mm=mm, row_existing=np.array([1]), col_existing=np.array([1])
    )
    # No new entries added
    assert np.array_equal(row, [1])
    assert np.array_equal(col, [1])


def test_fourth_heuristic_complement_existing():
    # col 0 already found; col 1 has single negative → appended to existing
    mm = _make_mm([(1, 1), (0, 1), (0, 0), (1, 0)], [-1, 2, 3, 4])
    row, col = gpe_fourth_heuristic(
        mm=mm, row_existing=np.array([0]), col_existing=np.array([0])
    )
    assert np.array_equal(row, [0, 1])
    assert np.array_equal(col, [0, 1])


def test_fourth_heuristic_no_negatives():
    # All entries positive → nothing found
    mm = _make_mm([(0, 0), (1, 1)], [1, 2])
    row, col = gpe_fourth_heuristic(mm=mm, row_existing=np.array([]), col_existing=np.array([]))
    assert row.size == 0
    assert col.size == 0


def test_guess_production_exchanges_waste_treatment():
    # col 0: normal process — produces row 0 (positive), generates waste row 1 (negative)
    # col 1: waste treatment — accepts waste row 1 only (single negative, no other entries)
    # Third heuristic finds col 0 (single positive); fourth heuristic finds col 1 (single negative).
    mm = _make_mm([(0, 0), (1, 0), (1, 1)], [1.0, -0.5, -1.0])
    row, col = guess_production_exchanges(mm)
    assert set(zip(row.tolist(), col.tolist())) == {(0, 0), (1, 1)}


def test_guess_production_exchanges_waste_prefers_earlier_heuristics():
    # col 0 has row==col (first heuristic), col 1 has single negative (fourth heuristic)
    # Ensures fourth heuristic does not override earlier results.
    mm = _make_mm([(0, 0), (1, 0), (1, 1)], [2.0, -1.0, -3.0])
    row, col = guess_production_exchanges(mm)
    assert set(zip(row.tolist(), col.tolist())) == {(0, 0), (1, 1)}
