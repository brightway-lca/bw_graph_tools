import bw_processing as bwp
import matrix_utils as mu
import numpy as np
import pytest

from bw_graph_tools.errors import UnclearProductionExchange
from bw_graph_tools.matrix_tools import guess_production_exchanges


@pytest.mark.skip(reason="MappedMatrix won't allow empty matrix construction")
def test_gpe_empty_matrix():
    dp1 = bwp.create_datapackage()
    mm = mu.MappedMatrix(
        packages=[dp1],
        matrix="test",
    )
    with pytest.raises(ValueError):
        guess_production_exchanges(mm)


# Don't remember the intended functionality for test case
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
        guess_production_exchanges(mm)


def test_gpe_unclear_production_exchange():
    # 3x3 matrix with no diagonal entries and two positive values per column.
    # All four heuristics fail: no row==col (first), no flip array (second),
    # multiple positives per column (third), no negatives (fourth).
    dp = bwp.create_datapackage()
    indices = np.array(
        [(1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2)],
        dtype=bwp.INDICES_DTYPE,
    )
    dp.add_persistent_vector(
        matrix="test",
        indices_array=indices,
        name="foo",
        data_array=np.array([1, 2, 3, 4, 5, 6], dtype=float),
    )
    mm = mu.MappedMatrix(packages=[dp], matrix="test")
    with pytest.raises(UnclearProductionExchange):
        guess_production_exchanges(mm)
