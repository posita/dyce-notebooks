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


def count_successes_with_push(pool: P) -> H:
    @expandable
    def _expand(p_result: PResult) -> Union[H, float]:
        counter = Counter(p_result.roll)
        blanks = counter[YearZeroOutcomes.BLANK]
        successes_so_far = (
            counter[YearZeroOutcomes.HALF_SUCCESS]
            + 2 * counter[YearZeroOutcomes.FULL_SUCCESS]
        ) / 2
        assert p_result.p.is_homogeneous()

        if blanks:
            reroll = count_successes(blanks @ p_result.p[:1])

            return reroll + successes_so_far
        else:
            return successes_so_far

    return _expand(
        pool,
        limit=2,  # to ensure count_successes is called in the interior
    )


@expandable
def count_banes(pool: PResult) -> Union[H, float]:
    counter = Counter(pool.roll)
    banes = counter[YearZeroOutcomes.BANE]

    return banes


def count_banes_with_push(pool: P) -> H:
    @expandable
    def _expand(p_result: PResult) -> Union[H, int]:
        counter = Counter(p_result.roll)
        blanks = counter[YearZeroOutcomes.BLANK]
        banes_so_far = counter[YearZeroOutcomes.BANE]
        assert p_result.p.is_homogeneous()

        if blanks:
            reroll = count_banes(pool=blanks @ p_result.p[:1])

            return reroll + banes_so_far
        else:
            return banes_so_far

    return _expand(
        pool,
        limit=2,  # to ensure count_successes is called in the interior
    )
