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
