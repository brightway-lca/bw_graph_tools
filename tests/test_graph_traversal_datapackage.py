import bw_processing as bwp
import matrix_utils as mu
import numpy as np

from bw_graph_tools import get_path_from_matrix


def test_simple_graph():
    A = 101
    B = 102
    C = 103
    edges = np.array(
        [
            (A, A),
            (B, B),
            (C, C),
            (B, A),
            (C, B),
        ],
        dtype=bwp.INDICES_DTYPE,
    )
    data = np.array([1, 1, 1, 1, 1])
    flip = np.array([0, 0, 0, 1, 1], dtype=bool)
    dp = bwp.create_datapackage()
    dp.add_persistent_vector(
        matrix="test",
        data_array=data,
        indices_array=edges,
        flip_array=flip,
    )
    mm = mu.MappedMatrix(packages=[dp], matrix="test")
    mapper = mm.col_mapper.to_dict()
    assert get_path_from_matrix(
        matrix=mm.matrix, source=mapper[A], target=mapper[C]
    ) == [mapper[A], mapper[B], mapper[C]]


def test_take_longer_path_direct_edge_available():
    A = 101
    B = 102
    C = 103
    edges = np.array(
        [
            (A, A),
            (B, B),
            (C, C),
            (B, A),
            (C, B),
            (C, A),
        ],
        dtype=bwp.INDICES_DTYPE,
    )
    data = np.array([1, 1, 1, 1, 1, 0.1])
    flip = np.array([0, 0, 0, 1, 1, 1], dtype=bool)
    dp = bwp.create_datapackage()
    dp.add_persistent_vector(
        matrix="test",
        data_array=data,
        indices_array=edges,
        flip_array=flip,
    )
    mm = mu.MappedMatrix(packages=[dp], matrix="test")
    mapper = mm.col_mapper.to_dict()
    assert get_path_from_matrix(
        matrix=mm.matrix, source=mapper[A], target=mapper[C]
    ) == [mapper[A], mapper[B], mapper[C]]


def test_take_longer_path_no_direct_edge():
    A = 101
    B = 102
    C = 103
    D = 104
    edges = np.array(
        [
            (A, A),
            (B, B),
            (C, C),
            (D, D),
            (B, A),
            (C, B),
            (C, A),
            (D, C),
        ],
        dtype=bwp.INDICES_DTYPE,
    )
    data = np.array([1, 1, 1, 1, 1, 1, 0.1, 1])
    flip = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=bool)
    dp = bwp.create_datapackage()
    dp.add_persistent_vector(
        matrix="test",
        data_array=data,
        indices_array=edges,
        flip_array=flip,
    )
    mm = mu.MappedMatrix(packages=[dp], matrix="test")
    mapper = mm.col_mapper.to_dict()
    assert get_path_from_matrix(
        matrix=mm.matrix, source=mapper[A], target=mapper[D]
    ) == [mapper[A], mapper[B], mapper[C], mapper[D]]
