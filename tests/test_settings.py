import pytest
from pydantic import ValidationError

from bw_graph_tools import GraphTraversalSettings


def test_settings_normal():
    gts = GraphTraversalSettings()
    assert gts.cutoff == 5e-3
    assert gts.biosphere_cutoff == 1e-4
    assert gts.max_calc == 1000
    assert gts.max_depth is None
    assert gts.skip_coproducts is False
    assert gts.separate_biosphere_flows is True


def test_settings_custom():
    gts = GraphTraversalSettings(
        cutoff=0.4,
        biosphere_cutoff=0.6,
        max_calc=5,
        max_depth=50,
        skip_coproducts=True,
        separate_biosphere_flows=False,
    )
    assert gts.cutoff == 0.4
    assert gts.biosphere_cutoff == 0.6
    assert gts.max_calc == 5
    assert gts.max_depth == 50
    assert gts.skip_coproducts is True
    assert gts.separate_biosphere_flows is False


def test_settings_error():
    with pytest.raises(ValidationError):
        GraphTraversalSettings(cutoff=2)
    with pytest.raises(ValidationError):
        GraphTraversalSettings(biosphere_cutoff=2)
    with pytest.raises(ValidationError):
        GraphTraversalSettings(max_calc=-2)
    with pytest.raises(ValidationError):
        GraphTraversalSettings(max_depth=-2)
    with pytest.raises(ValidationError):
        GraphTraversalSettings(skip_coproducts=7)
    with pytest.raises(ValidationError):
        GraphTraversalSettings(separate_biosphere_flows=7)
