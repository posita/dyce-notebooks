from collections import Counter
from enum import IntEnum, auto
from typing import Union

from dyce import H, P
from dyce.evaluation import PResult, expandable


class YearZeroOutcomes(IntEnum):
    BANE = -1
    BLANK = 0
    HALF_SUCCESS = auto()
    FULL_SUCCESS = auto()


# Our legacy die. This is equivalent to a fair, six-sided die with one face showing a
# bane, one face showing a success, and four blank faces.
dyz_legacy = P(
    H(
        (
            YearZeroOutcomes.BANE,
            YearZeroOutcomes.BLANK,
            YearZeroOutcomes.BLANK,
            YearZeroOutcomes.BLANK,
            YearZeroOutcomes.BLANK,
            YearZeroOutcomes.FULL_SUCCESS,
        )
    )
)

# Our modified die. This is equivalent to a fair, six-sided die with one face showing a
# bane, one face showing a success, one face showing a "half" success, and three blank
# faces.
dyz = P(
    H(
        (
            YearZeroOutcomes.BANE,
            YearZeroOutcomes.BLANK,
            YearZeroOutcomes.BLANK,
            YearZeroOutcomes.BLANK,
            YearZeroOutcomes.HALF_SUCCESS,
            YearZeroOutcomes.FULL_SUCCESS,
        )
    )
)


@expandable
def count_successes(pool: PResult) -> Union[H, float]:
    r"""
    When provided a pool of one or more of one of our above dice, this computes the
    distribution with the expected number of successes as outcomes. When using our
    modified die, this can include "half" successes (each of which contribute 0.5 to the
    number of successes).
    """
    counter = Counter(pool.roll)
    successes_for_this_roll = (
        counter[YearZeroOutcomes.HALF_SUCCESS] / 2
        + counter[YearZeroOutcomes.FULL_SUCCESS]
    )

    return successes_for_this_roll


def count_successes_with_push(pool: P) -> H:
    r"""
    When provided a pool of one or more of one of our above dice, this computes the
    distribution after a push with the expected number of successes as outcomes. Like
    count_successes above, when using our modified die, this can include "half"
    successes (each of which contribute 0.5 to the number of successes).
    """

    @expandable
    def _expand(p_result: PResult) -> Union[H, float]:
        counter = Counter(p_result.roll)
        blanks_this_roll = counter[YearZeroOutcomes.BLANK]
        successes_for_this_roll = (
            counter[YearZeroOutcomes.HALF_SUCCESS] / 2
            + counter[YearZeroOutcomes.FULL_SUCCESS]
        )
        assert p_result.p.is_homogeneous()

        if blanks_this_roll:
            push = count_successes(blanks_this_roll @ p_result.p[:1])

            return push + successes_for_this_roll
        else:
            return successes_for_this_roll

    return _expand(
        pool,
        limit=2,  # to ensure count_successes is called in the interior
    )


@expandable
def count_banes(pool: PResult) -> Union[H, float]:
    r"""
    When provided a pool of one or more of one of our above dice, this computes the
    distribution with the expected number of banes as outcomes.
    """
    counter = Counter(pool.roll)
    banes_this_roll = counter[YearZeroOutcomes.BANE]

    return banes_this_roll


def count_banes_with_push(pool: P) -> H:
    r"""
    When provided a pool of one or more of one of our above dice, this computes the
    distribution after a push with the expected number of banes as outcomes.
    """

    @expandable
    def _expand(p_result: PResult) -> Union[H, int]:
        counter = Counter(p_result.roll)
        blanks_this_roll = counter[YearZeroOutcomes.BLANK]
        banes_this_roll = counter[YearZeroOutcomes.BANE]
        assert p_result.p.is_homogeneous()

        if blanks_this_roll:
            push = count_banes(pool=blanks_this_roll @ p_result.p[:1])

            return push + banes_this_roll
        else:
            return banes_this_roll

    return _expand(
        pool,
        limit=2,  # to ensure count_banes is called in the interior
    )
