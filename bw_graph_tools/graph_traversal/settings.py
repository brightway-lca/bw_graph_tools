from typing import List, Optional

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Annotated


class GraphTraversalSettings(BaseModel):
    """
    Graph traversal settings object with reasonable defaults.

    Parameters
    ----------
    cutoff : float
        Cutoff value used to stop graph traversal. Fraction of total score,
        should be in `(0, 1)`
    biosphere_cutoff : float
        Cutoff value used to determine if a separate biosphere node is
        added. Fraction of total score.
    max_calc : int | None
        Maximum number of inventory calculations to perform
    max_depth : int
        Maximum depth in the supply chain traversal. Default is no maximum.
    skip_coproducts : bool
        Don't traverse co-production edges, i.e. production edges other
        than the reference product
    separate_biosphere_flows : bool
        Add separate `Flow` nodes for important individual biosphere
        emissions
    """

    cutoff: Annotated[float, Field(strict=True, gt=0, lt=1)] = 5e-3
    biosphere_cutoff: Annotated[float, Field(strict=True, gt=0, lt=1)] = 1e-4
    max_calc: Annotated[int, Field(strict=True, gt=0)] = 1000
    max_depth: Optional[int] = None
    skip_coproducts: bool = False
    separate_biosphere_flows: bool = True

    @model_validator(mode="after")
    def max_depth_positive(self):
        if self.max_depth is not None and self.max_depth <= 0:
            raise ValueError(f"If specified, `max_depth` must be greater than zero")
        return self


class TaggedGraphTraversalSettings(GraphTraversalSettings):
    """
    Supply Chain Traversal Settings with a functional unit tag

    Parameters
    ----------
    tags : List[str]
        A list of tags to group nodes by
    """

    tags: List[str] = Field(default_factory=list)
