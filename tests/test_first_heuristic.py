import bw_processing as bwp
import matrix_utils as mu
import numpy as np
from bw2calc import LCA
from bw2data import Database
from bw2data.tests import bw2test

from bw_graph_tools.matrix_tools import gpe_first_heuristic


@bw2test
def test_first_heuristic_from_database_with_products():
    Database("bio").write(
        {
            ("bio", "a"): {
                "type": "emission",
                "name": "a",
                "exchanges": [],
            },
        }
    )
    Database("t").write(
        {
            ("t", "1"): {
                "name": "1",
                "exchanges": [
                    {
                        "input": ("bio", "a"),
                        "amount": 0.5,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "p2"),
                        "amount": 1,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "p1"),
                        "amount": 2,
                        "type": "production",
                    },
                ],
            },
            ("t", "2"): {
                "name": "2",
                "exchanges": [
                    {
                        "input": ("bio", "a"),
                        "amount": 1,
                        "type": "biosphere",
                    },
                    {
                        "input": ("t", "p1"),
                        "amount": 2,
                        "type": "technosphere",
                    },
                    {
                        "input": ("t", "p2"),
                        "amount": 4,
                        "type": "production",
                    },
                ],
            },
            ("t", "p2"): {"type": "product", "name": "2p", "exchanges": []},
            ("t", "p1"): {"type": "product", "name": "1p", "exchanges": []},
        }
    )
    lca = LCA({("t", "p2"): 8})
    lca.lci()

    row, col = gpe_first_heuristic(lca.technosphere_mm)
    assert row.shape == (0,)
    assert col.shape == (0,)


def test_gpe_first_heuristic_single_dp():
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
    row, col = gpe_first_heuristic(mm)
    assert np.array_equal(np.array([1, 0]), row)
    assert np.array_equal(np.array([1, 0]), col)


def test_gpe_first_heuristic_multiple_dp():
    dp1 = bwp.create_datapackage()
    data = np.array([1, 2])
    indices = np.array(
        [
            (1, 1),
            (0, 1),
        ],
        dtype=bwp.INDICES_DTYPE,
    )
    dp1.add_persistent_vector(
        matrix="test",
        indices_array=indices,
        name="foo",
        data_array=data,
    )
    dp2 = bwp.create_datapackage()
    indices = np.array(
        [
            (0, 0),
            (1, 0),
        ],
        dtype=bwp.INDICES_DTYPE,
    )
    data = np.array([3, 4])
    dp2.add_persistent_vector(
        matrix="test",
        indices_array=indices,
        name="foo",
        data_array=data,
    )
    mm = mu.MappedMatrix(
        packages=[dp1, dp2],
        matrix="test",
    )
    row, col = gpe_first_heuristic(mm)
    assert np.array_equal(np.array([1, 0]), row)
    assert np.array_equal(np.array([1, 0]), col)


def test_gpe_first_heuristic_multiple_dp_one_empty():
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
    dp2 = bwp.create_datapackage()
    dp2.add_persistent_vector(
        matrix="other",
        indices_array=indices,
        name="foo",
        data_array=data,
    )
    mm = mu.MappedMatrix(
        packages=[dp1, dp2],
        matrix="test",
    )
    row, col = gpe_first_heuristic(mm)
    assert np.array_equal(np.array([1, 0]), row)
    assert np.array_equal(np.array([1, 0]), col)


def test_gpe_first_heuristic_mix_product_no_product():
    dp1 = bwp.create_datapackage()
    data = np.array([1, 2, 3, 4])
    indices = np.array(
        [
            (1, 1),
            (2, 1),
            (1, 0),
            (3, 0),
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
    row, col = gpe_first_heuristic(mm)
    # First row (product) is 1
    assert np.array_equal(np.array([0]), row)
    # First column is 0; we need second (1)
    assert np.array_equal(np.array([1]), col)


def test_gpe_first_heuristic_multiple_always_split_products():
    dp1 = bwp.create_datapackage()
    data = np.array([1, 2, 3, 4])
    indices = np.array(
        [
            (3, 1),
            (2, 1),
            (2, 0),
            (3, 0),
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
    row, col = gpe_first_heuristic(mm)
    assert row.shape == (0,)
    assert col.shape == (0,)
