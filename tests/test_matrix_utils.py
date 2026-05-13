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


@pytest.mark.xfail(
    reason=(
        "Third heuristic fires before the fourth and misidentifies the waste-treatment "
        "co-product (positive entry) as the production exchange. The correct exchange is "
        "the negative waste entry, which gpe_fourth_heuristic would have found had it "
        "run first."
    )
)
def test_gpe_third_heuristic_false_positive_waste_treatment_coproduct():
    # Activity A (col 0): produces waste W (row 0) — single positive, correctly found
    #                      by the third heuristic.
    # Activity B (col 1): treats waste W (row 0, negative entry) AND produces co-product
    #                      X (row 1, positive entry). Neither A nor B are found by
    #                      heuristics 1 or 2 (row IDs 2, 3 are disjoint from col IDs 0, 1).
    #
    # Third heuristic sees exactly one positive entry in column 1 (the co-product X at
    # row 1) and claims it as B's production exchange — wrong.  Both A and B should have
    # waste W (matrix row 0) as their production exchange: A produces it, B treats it.
    dp = bwp.create_datapackage()
    dp.add_persistent_vector(
        matrix="test",
        indices_array=np.array([(2, 0), (2, 1), (3, 1)], dtype=bwp.INDICES_DTYPE),
        name="foo",
        data_array=np.array([1.0, -1.0, 0.5]),
    )
    mm = mu.MappedMatrix(packages=[dp], matrix="test")
    row, col = guess_production_exchanges(mm)
    # Row IDs 2→matrix row 0, 3→matrix row 1; col IDs map identically.
    assert set(zip(row.tolist(), col.tolist())) == {(0, 0), (0, 1)}


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
