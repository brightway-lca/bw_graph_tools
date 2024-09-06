import bw_processing as bwp
import matrix_utils as mu
import numpy as np

from bw_graph_tools.matrix_tools import gpe_second_heuristic


def test_second_heuristic_empty_existing():
    dp1 = bwp.create_datapackage()
    data = np.array([1, 2, 3, 4])
    indices = np.array(
        [
            (1, 1),
            (0, 1),
            (0, 0),
            (1, 0),
        ],
        dtype=bwp.INDICES_DTYPE,
    )
    flip = np.array([False, True, True, True], dtype=bool)
    dp1.add_persistent_vector(
        matrix="test",
        indices_array=indices,
        name="foo",
        data_array=data,
        flip_array=flip,
    )
    mm = mu.MappedMatrix(
        packages=[dp1],
        matrix="test",
    )
    row, col = gpe_second_heuristic(
        mm=mm, row_existing=np.array([]), col_existing=np.array([])
    )
    assert np.array_equal(np.array([1]), row)
    assert np.array_equal(np.array([1]), col)


def test_second_heuristic_off_diagonal():
    dp1 = bwp.create_datapackage()
    data = np.array([1, 2, 3, 4])
    indices = np.array(
        [
            (1, 1),
            (0, 1),
            (0, 0),
            (1, 0),
        ],
        dtype=bwp.INDICES_DTYPE,
    )
    flip = np.array([True, False, True, False], dtype=bool)
    dp1.add_persistent_vector(
        matrix="test",
        indices_array=indices,
        name="foo",
        data_array=data,
        flip_array=flip,
    )
    mm = mu.MappedMatrix(
        packages=[dp1],
        matrix="test",
    )
    row, col = gpe_second_heuristic(
        mm=mm, row_existing=np.array([]), col_existing=np.array([])
    )
    assert np.array_equal(np.array([0, 1]), row)
    assert np.array_equal(np.array([1, 0]), col)


def test_second_heuristic_exclude_multiple_flips():
    dp1 = bwp.create_datapackage()
    data = np.array([1, 2, 3, 4])
    indices = np.array(
        [
            (1, 1),
            (0, 1),
            (0, 0),
            (1, 0),
        ],
        dtype=bwp.INDICES_DTYPE,
    )
    flip = np.array([False, True, False, False], dtype=bool)
    dp1.add_persistent_vector(
        matrix="test",
        indices_array=indices,
        name="foo",
        data_array=data,
        flip_array=flip,
    )
    mm = mu.MappedMatrix(
        packages=[dp1],
        matrix="test",
    )
    row, col = gpe_second_heuristic(
        mm=mm, row_existing=np.array([]), col_existing=np.array([])
    )
    assert np.array_equal(np.array([1]), row)
    assert np.array_equal(np.array([1]), col)


def test_second_heuristic_overlap_existing():
    dp1 = bwp.create_datapackage()
    data = np.array([1, 2, 3, 4])
    indices = np.array(
        [
            (1, 1),
            (0, 1),
            (0, 0),
            (1, 0),
        ],
        dtype=bwp.INDICES_DTYPE,
    )
    flip = np.array([False, True, False, True], dtype=bool)
    dp1.add_persistent_vector(
        matrix="test",
        indices_array=indices,
        name="foo",
        data_array=data,
        flip_array=flip,
    )
    mm = mu.MappedMatrix(
        packages=[dp1],
        matrix="test",
    )
    row, col = gpe_second_heuristic(
        mm=mm, row_existing=np.array([0]), col_existing=np.array([0])
    )
    assert np.array_equal(np.array([0, 1]), row)
    assert np.array_equal(np.array([0, 1]), col)


def test_second_heuristic_complement_existing():
    dp1 = bwp.create_datapackage()
    data = np.array([1, 2, 3, 4])
    indices = np.array(
        [
            (1, 1),
            (0, 1),
            (0, 0),
            (1, 0),
        ],
        dtype=bwp.INDICES_DTYPE,
    )
    flip = np.array([False, True, False, True], dtype=bool)
    dp1.add_persistent_vector(
        matrix="test",
        indices_array=indices,
        name="foo",
        data_array=data,
        flip_array=flip,
    )
    mm = mu.MappedMatrix(
        packages=[dp1],
        matrix="test",
    )
    row, col = gpe_second_heuristic(
        mm=mm, row_existing=np.array([10]), col_existing=np.array([10])
    )
    assert np.array_equal(np.array([10, 1, 0]), row)
    assert np.array_equal(np.array([10, 1, 0]), col)


def test_second_heuristic_no_flip():
    dp1 = bwp.create_datapackage()
    data = np.array([1, 2, 3, 4])
    indices = np.array(
        [
            (1, 1),
            (0, 1),
            (0, 0),
            (1, 0),
        ],
        dtype=bwp.INDICES_DTYPE,
    )
    dp1.add_persistent_vector(
        matrix="test",
        indices_array=indices,
        name="foo",
        data_array=data,
    )
    mm = mu.MappedMatrix(
        packages=[dp1],
        matrix="test",
    )
    row, col = gpe_second_heuristic(
        mm=mm, row_existing=np.array([0]), col_existing=np.array([0])
    )
    assert np.array_equal(np.array([0]), row)
    assert np.array_equal(np.array([0]), col)
