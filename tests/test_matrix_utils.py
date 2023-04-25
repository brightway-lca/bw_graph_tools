import bw_processing as bwp
import matrix_utils as mu
import numpy as np
import pytest

from bw_graph_tools.errors import UnclearProductionExchange
from bw_graph_tools.matrix_utils import guess_production_exchanges


@pytest.mark.skip(reason="MappedMatrix won't allow empty matrix construction")
def test_gpe_empty_matrix():
    dp1 = bwp.create_datapackage()
    mm = mu.MappedMatrix(
        packages=[dp1],
        matrix="test",
    )
    with pytest.raises(ValueError):
        guess_production_exchanges(mm)


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
    row, col = guess_production_exchanges(mm)
    assert np.array_equal(np.array([1, 0]), row)
    assert np.array_equal(np.array([1, 0]), col)


def test_gpe_multiple_datapackages():
    pass


def test_gpe_first_heuristic_one_dp_empty():
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
    row, col = guess_production_exchanges(mm)
    assert np.array_equal(np.array([1, 0]), row)
    assert np.array_equal(np.array([1, 0]), col)


# Don't remember the intended functionality or test case
@pytest.mark.skip("Don't remember the point of this test")
def test_gpe_raise_error():
    dp1 = bwp.create_datapackage()
    data = np.array([1, 2, 4])
    indices = np.array(
        [
            (1, 1),
            (0, 1),
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
    with pytest.raises(UnclearProductionExchange):
        print(guess_production_exchanges(mm))
