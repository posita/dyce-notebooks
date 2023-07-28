from enum import IntEnum, auto
from functools import cache

from dyce import H, P
from dyce.evaluation import HResult, PResult, explode, foreach

try:
    from dyce.evaluation import LimitT
except ImportError:
    from dyce.evaluation import _LimitT as LimitT

# Local imports
from params import Params

__all__ = ()


class Pool(IntEnum):
    STANDARD = auto()
    BUMP = auto()


assert Pool.STANDARD < Pool.BUMP


def mechanic_dyce_fudged(
    params: Params,
    die: H,
    explode_limit: LimitT = 0,
) -> H:
    r"""
    *set_die* is the zero-based index into each roll (i.e., on the interval ``#!python
    [0, num_std + num_bmp)``) for determining the check die. *num_std* is how many of
    *die* are in the standard pool. *num_bmp* is how many of *die* are in the bump pool.
    Note this interface only allows for homogeneous pools. *bonus_dice* are an optional
    sequence of zero-based indexes into each roll whose values are added to the total.
    *explode_limit* has same meaning as ``#!python dyce.evaluation.expandable``.
    """
    pool_size = params.num_std + params.num_bmp
    extra_std = min(params.extra_std, pool_size)
    extra_bmp = min(params.extra_bmp, pool_size)

    if params.extra_std:
        extra_bonus = -2 * max(params.extra_std - pool_size, 0)
        roll_slice = slice(None, -extra_std)
    elif params.extra_bmp:
        extra_bonus = 2 * max(params.extra_bmp - pool_size, 0)
        roll_slice = slice(extra_bmp, None)
    else:
        extra_bonus = 0
        roll_slice = slice(None)

    p_std = (params.num_std + extra_std) @ P(die)
    p_bmp = (params.num_bmp + extra_bmp) @ P(die)

    def _mechanic(std: PResult, bmp: PResult | None = None):
        roll = list((outcome, Pool.STANDARD) for outcome in std.roll)

        if bmp is not None:
            roll.extend((outcome, Pool.BUMP) for outcome in bmp.roll)

        roll.sort()
        roll = roll[roll_slice]
        assert len(roll) == pool_size
        check_die = params.set_die
        check_outcome, set_type = roll[check_die]

        if set_type is Pool.BUMP:
            check_die = (check_die + 1) % len(roll)
            check_outcome, _ = roll[check_die]

        total_outcome = check_outcome

        if check_die < params.set_die:
            wrapped_outcome, _ = roll[params.set_die]
            total_outcome += wrapped_outcome

        return (
            total_outcome
            + sum(roll[bonus_die][0] for bonus_die in params.bonus_dice)
            + extra_bonus
        )

    if p_bmp:
        unexploded_result = foreach(_mechanic, p_std, p_bmp)
    else:
        unexploded_result = foreach(_mechanic, p_std)

    return unexploded_result + _aggregate_exploded_deltas(die, explode_limit)


@cache
def _aggregate_exploded_deltas(die: H, explode_limit: LimitT):
    def _func(h_res: HResult):
        return _explosions_by_outcome(h_res.h, explode_limit).get(h_res.outcome, 0)  # type: ignore

    return foreach(_func, die)


@cache
def _explosions_by_outcome(die: H, explode_limit: LimitT) -> dict[int, H]:
    if explode_limit <= 0:
        return {}
    else:
        return {
            outcome: die.eq(outcome)  # type: ignore
            * explode(
                die,
                predicate=lambda result: result.outcome == outcome,
                limit=explode_limit,
            )
            for outcome in die
        }
