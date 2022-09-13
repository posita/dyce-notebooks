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


dyz = P(
    H(
        {
            YearZeroOutcomes.BANE: 1,
            YearZeroOutcomes.BLANK: 3,
            YearZeroOutcomes.HALF_SUCCESS: 1,
            YearZeroOutcomes.FULL_SUCCESS: 1,
        }
    )
)

dyz_legacy = P(
    H(
        {
            YearZeroOutcomes.BANE: 1,
            YearZeroOutcomes.BLANK: 4,
            YearZeroOutcomes.FULL_SUCCESS: 1,
        }
    )
)


@expandable
def count_successes(pool: PResult) -> Union[H, float]:
    counter = Counter(pool.roll)
    successes = (
        counter[YearZeroOutcomes.HALF_SUCCESS]
        + 2 * counter[YearZeroOutcomes.FULL_SUCCESS]
    ) / 2

    return successes


@expandable
def count_successes_with_push(pool: PResult) -> Union[H, float]:
    counter = Counter(pool.roll)
    blanks = counter[YearZeroOutcomes.BLANK]
    successes_so_far = (
        counter[YearZeroOutcomes.HALF_SUCCESS]
        + 2 * counter[YearZeroOutcomes.FULL_SUCCESS]
    ) / 2
    assert pool.p.is_homogeneous()

    if blanks:
        reroll = count_successes(pool=blanks @ pool.p[:1])

        return reroll + successes_so_far
    else:
        return successes_so_far


@expandable
def count_banes(pool: PResult) -> Union[H, float]:
    counter = Counter(pool.roll)
    banes = counter[YearZeroOutcomes.BANE]

    return banes


@expandable
def count_banes_with_push(pool: PResult) -> Union[H, int]:
    counter = Counter(pool.roll)
    blanks = counter[YearZeroOutcomes.BLANK]
    banes_so_far = counter[YearZeroOutcomes.BANE]
    assert pool.p.is_homogeneous()

    if blanks:
        reroll = count_banes(pool=blanks @ pool.p[:1])

        return reroll + banes_so_far
    else:
        return banes_so_far
