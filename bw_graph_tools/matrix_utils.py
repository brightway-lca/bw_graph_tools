from typing import Tuple

import matrix_utils as mu
import numpy as np
from scipy import sparse

from .errors import UnclearProductionExchange


def to_normalized_adjacency_matrix(
    matrix: sparse.spmatrix, log_transform: bool = True
) -> sparse.csr_matrix:
    """Take a technosphere matrix constructed with Brightway conventions, and return a normalized adjacency matrix.

    In the adjacency matrix A, `A[i,j]` indicates a directed edge **from** row `i` **to** column `j`. However,
    this is the opposite of what we normally want, which is to find a path from the functional activity to
    somewhere in its supply chain. In a Brightway technosphere matrix, `A[i,j]` means **activity** `j` consumes
    the output of activity `i`. To go down the supply chain, however, we would need to go from ``j`` to ``i``.
    Therefore, we take the transpose of the technosphere matrix.

    Normalization is done to remove the effect of activities which don't produce one unit of their reference product.
    For example, if activity `foo` produces two units of `bar` and consumes two units of `baz`, the weight of the
    `baz` edge should be :math:`2 / 2 = 1`.

    In addition to this normalization, we subtract the diagonal and flip the signs of all matrix values. Flipping
    the sign is needed because we want to use a shortest path algorithm, but actually want the longest path. The
    longest path is the path with the highest weight, i.e. the path where the most consumption occurs on.

    By default, we also take the natural log of the data values. This is because our supply chain is multiplicative,
    not additive, and :math:`a \\cdot b = e^{\\ln(a) + \\ln(b)}`. The idea of using the log was borrowed from `David Richardby on Stack Overflow <https://cs.stackexchange.com/questions/83656/traverse-direct-graph-with-multiplicative-edges>`__.

    Assumes that production amounts are on the diagonal.
    """
    matrix = matrix.tocsr().T

    # TBD these values should the NET production values, i.e. we use the production exchanges to get the matrix
    # indices, ensure that we have 1-1 match for production-activity, construct the normalization vector, turn
    # into a diagonal matrix, and then multiply
    normalization = sparse.diags(-1 * matrix.diagonal())
    normalized = (matrix * normalization) + sparse.eye(*matrix.shape)

    if log_transform:
        normalized = normalized.tocoo()
        normalized.data = np.log(normalized.data) * -1
        normalized = normalized.tocsr()

    return normalized


def gpe_first_heuristic(mm: mu.MappedMatrix) -> Tuple[np.ndarray, np.ndarray]:
    """Use first heuristic (same input and output ids) to find production exchange indices.

    If we treat activities and products the same, then an exchange with the row and column id
    is definitely a production exchange location. We don't care if there are duplicates (e.g.
    production and some loss), we will return unique pairs.

    If activities have different ids than products, this won't find anything.

    Returns a tuple of numpy integer matrix indices, rows by columns.
    """

    def get_used_mapped_indices_for_group(
        group: mu.ResourceGroup,
    ) -> Tuple[np.ndarray, np.ndarray]:
        indices = group.get_indices_data()

        # Need to check the original input values, not after mapping when they are
        # normalized to [0, X] range.
        ident_mask = indices["row"] == indices["col"]
        row_mapped = group.row_mapper.map_array(indices["row"][ident_mask])
        col_mapped = group.col_mapper.map_array(indices["col"][ident_mask])

        if (row_mapped == -1).sum() or (col_mapped == -1).sum():
            ERROR = """
Found unmapped values in technosphere matrix generator, but that should be impossible.

{} unmapped values in the row indices: {}
{} unmapped values in the column indices: {}

Please report this as an issue, something went very wrong!
            """
            raise ValueError(
                ERROR.format(
                    (row_mapped == -1).sum(),
                    indices["row"][row_mapped == -1],
                    (col_mapped == -1).sum(),
                    indices["col"][col_mapped == -1],
                )
            )

        return row_mapped, col_mapped

    first_heuristic = [get_used_mapped_indices_for_group(group) for group in mm.groups]

    row_indices = np.hstack([array for array, _ in first_heuristic])
    col_indices = np.hstack([array for _, array in first_heuristic])

    return row_indices, col_indices


def gpe_second_heuristic(
    mm: mu.MappedMatrix, row_existing: np.ndarray, col_existing: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    # Second heuristic: If there is a single value *per column* where flip is false
    not_flipped = []

    for group in mm.groups:
        try:
            # Get indices where flip is false and only one value is present
            h2_col_indices, h2_col_counts = np.unique(
                group.col_masked[~group.flip], return_counts=True
            )
            h2_col_indices = h2_col_indices[h2_col_counts == 1]

            # Remove elements found by first heuristic
            existing_mask = np.in1d(h2_col_indices, col_existing)

            # Need mask with correct shape for both row and col indices
            mask = np.in1d(
                group.col_masked[~group.flip], h2_col_indices[~existing_mask]
            )

            not_flipped.append(
                (
                    group.row_masked[~group.flip][mask],
                    group.col_masked[~group.flip][mask],
                )
            )
        except KeyError:
            # No flip array given
            pass

    try:
        row_not_flipped = np.hstack([array for array, _ in not_flipped])
        col_not_flipped = np.hstack([array for _, array in not_flipped])
        return np.hstack([row_existing, row_not_flipped]), np.hstack(
            [col_existing, col_not_flipped]
        )
    except ValueError:
        return row_existing, col_existing


def gpe_third_heuristic(
    mm: mu.MappedMatrix, row_existing: np.ndarray, col_existing: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    # Third heuristic: Single positive value
    matrix = mm.matrix.tocoo()

    positive_mask = matrix.data > 0
    row, col = matrix.row[positive_mask], matrix.col[positive_mask]

    existing_mask = ~np.in1d(col, col_existing)
    row, col = row[existing_mask], col[existing_mask]

    col_indices, col_counts = np.unique(col, return_counts=True)
    single_mask = np.in1d(col, col_indices[col_counts == 1])
    row, col = row[single_mask], col[single_mask]

    if row.size:
        return np.hstack([row_existing, row]), np.hstack([col_existing, col])
    else:
        return row_existing, col_existing


def guess_production_exchanges(mm: mu.MappedMatrix) -> Tuple[np.ndarray, np.ndarray]:
    """Try to guess productions exchanges in a mapped technosphere matrix using heuristics from the input data packages.

    Try the following in order per activity (column):

    * Same input and output index
    * Single value where ``flip`` is negative
    * Single positive value

    Raises ``UnclearProductionExchange`` if these conditions are not met for any activity.

    Returns integer arrays of the matrix row and column indices where production exchanges were found.

    """
    if mm.matrix.shape[0] == 0:
        raise ValueError("Empty matrix")

    row_indices, col_indices = gpe_first_heuristic(mm)

    # Every column must have an activity with some reference product or the system
    # is not solvable. Therefore we can look across all columns. We will do
    # all the work in matrix indices.
    missing = np.setdiff1d(
        np.arange(mm.matrix.shape[0]), col_indices, assume_unique=True
    )

    # Short circuit other steps if possible; assumption is that this step will
    # be taken for most matrices
    if not missing.size:
        return (row_indices, col_indices)

    row_indices, col_indices = gpe_second_heuristic(mm, row_indices, col_indices)
    row_indices, col_indices = gpe_third_heuristic(mm, row_indices, col_indices)

    # No idea how this could happen, but better raise an error than pass bad data
    if row_indices.shape != col_indices.shape:
        raise ValueError("Guessed row indices do not match guessed column indices.")

    missing = np.setdiff1d(
        np.arange(mm.matrix.shape[0]), col_indices, assume_unique=True
    )
    if missing.size:
        raise UnclearProductionExchange(
            "Can't find production exchanges for columns: {}".format(list(missing))
        )

    return (row_indices, col_indices)


def reorder_mapped_matrix(matrix: mu.MappedMatrix) -> sparse.csr_matrix:
    return None
