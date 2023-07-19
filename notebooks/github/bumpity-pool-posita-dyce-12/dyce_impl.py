from functools import cache

from dyce import H, P
from dyce.evaluation import HResult, PResult, _LimitT, explode, foreach

# Local imports
from params import Params

__all__ = ()


def mechanic_dyce_fudged(
    params: Params,
    die: H,
    explode_limit: _LimitT = 0,
) -> H:
    r"""
    *set_die* is the zero-based index into each roll (i.e., on the interval ``#!python
    [0, num_std + num_bump)``) for determining the check die. *num_std* is how many of
    *die* are in the standard pool. *num_bump* is how many of *die* are in the bump
    pool. Note this interface only allows for homogeneous pools. *bonus_dice* are an
    optional sequence of zero-based indexes into each roll whose values are added to the
    total. *explode_limit* has same meaning as ``#!python dyce.evaluation.expandable``.
    """
    pool_size = params.num_std + params.num_bump
    extra_std = min(params.extra_std, pool_size)
    extra_bump = min(params.extra_bump, pool_size)

    if params.extra_std:
        extra_bonus = -2 * max(params.extra_std - pool_size, 0)
        roll_slice = slice(None, -extra_std)
    elif params.extra_bump:
        extra_bonus = 2 * max(params.extra_bump - pool_size, 0)
        roll_slice = slice(extra_bump, None)
    else:
        extra_bonus = 0
        roll_slice = slice(None)

    p_std = (params.num_std + extra_std) @ P(die)
    p_bump = (params.num_bump + extra_bump) @ P(die)

    def _mechanic(std: PResult, bump: PResult | None = None):
        roll = list(std.roll)

        if bump is not None:
            roll.extend(bump.roll)
            bumped_outcomes = set(bump.roll)
        else:
            bumped_outcomes = set()

        roll.sort()
        roll = roll[roll_slice]
        assert len(roll) == pool_size
        check_die = params.set_die

        if roll[check_die] in bumped_outcomes:
            check_die = (check_die + 1) % len(roll)

        check_outcome = roll[check_die]
        total_outcome = check_outcome

        if check_die < params.set_die:
            wrapped_outcome = roll[params.set_die]
            total_outcome += wrapped_outcome

        return (
            total_outcome
            + sum(roll[bonus_die] for bonus_die in params.bonus_dice)
            + extra_bonus
        )

    if p_bump:
        unexploded_result = foreach(_mechanic, p_std, p_bump)
    else:
        unexploded_result = foreach(_mechanic, p_std)

    return unexploded_result + _aggregate_exploded_deltas(die, explode_limit)


@cache
def _aggregate_exploded_deltas(die: H, explode_limit: _LimitT):
    def _func(h_res: HResult):
        return _explosions_by_outcome(h_res.h, explode_limit).get(h_res.outcome, 0)  # type: ignore

    return foreach(_func, die)


@cache
def _explosions_by_outcome(die: H, explode_limit: _LimitT) -> dict[int, H]:
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
