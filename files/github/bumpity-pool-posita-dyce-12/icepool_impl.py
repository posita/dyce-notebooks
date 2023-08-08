from enum import IntEnum, auto
from functools import cache

import icepool
from dyce import H
from dyce.evaluation import LimitT

# Local imports
from dyce_impl import _aggregate_exploded_deltas, _explosions_by_outcome
from params import Params

__all__ = ()


class Pool(IntEnum):
    STANDARD = auto()
    BUMP = auto()


assert Pool.STANDARD < Pool.BUMP

_StateT = tuple[tuple[int, Pool], ...]


class IcepoolMechanic(icepool.MultisetEvaluator):
    r"""
    icepool.MultisetEvaluator mechanic implementation, which is vastly more efficient
    than a ``#!python dyce``-based implementation for correct explosion approximation,
    but offers little advantage otherwise (e.g., if fudging explosions).
    """

    def __init__(
        self,
        params: Params,
        die: H,
        explode_limit: LimitT,
    ):
        self._params = params
        self._die = die
        self._explode_limit = explode_limit
        self.pool_size = params.num_std + params.num_bmp
        self.extra_std = min(params.extra_std, self.pool_size)
        self.extra_bmp = min(params.extra_bmp, self.pool_size)

        if params.extra_std:
            self._order = icepool.Order.Ascending
            self._roll_slice = slice(None, self.pool_size)
            self._extra_bonus = -2 * max(params.extra_std - self.pool_size, 0)
        elif params.extra_bmp:
            self._order = icepool.Order.Descending
            self._roll_slice = slice(-self.pool_size, None)
            self._extra_bonus = 2 * max(params.extra_bmp - self.pool_size, 0)
        else:
            self._order = icepool.Order.Descending
            self._roll_slice = slice(None)
            self._extra_bonus = 0

    def final_outcome(self, final_state: _StateT) -> icepool.Die | int:
        final_state = final_state[self._roll_slice]
        assert len(final_state) == self.pool_size
        check_die = self._params.set_die
        _, set_type = final_state[check_die]

        if set_type is Pool.BUMP:
            check_die = (check_die + 1) % len(final_state)

        check_outcome, _ = final_state[check_die]
        total_outcome = check_outcome

        if check_die < self._params.set_die:
            wrapped_outcome, _ = final_state[self._params.set_die]
            total_outcome += wrapped_outcome

        return (
            total_outcome
            + sum(final_state[bonus_die][0] for bonus_die in self._params.bonus_dice)
            + self._extra_bonus
            + _explosions_by_outcome_icepool(self._die, self._explode_limit).get(
                check_outcome, 0
            )
        )

    def next_state(
        self, state: _StateT | None, outcome: int, std_count: int, bmp_count: int
    ) -> _StateT:
        if state is None:
            state = ()

        new_std = ((outcome, Pool.STANDARD),) * std_count
        new_bmp = ((outcome, Pool.BUMP),) * bmp_count

        if self._order is icepool.Order.Ascending:
            return state + new_std + new_bmp
        elif self._order is icepool.Order.Descending:
            return new_std + new_bmp + state
        else:
            assert False, "should never be here"

    def order(self, *_) -> icepool.Order:
        return self._order


def mechanic_icepool(
    params: Params,
    die: H,
    explode_limit: LimitT = 0,
) -> H:
    r"""
    This has the same interface as ``#!python mechanic_dyce``, but translates primitives
    and uses an ``#!python mechanic_icepool``-based implementation.
    """
    mechanic = IcepoolMechanic(params, die, explode_limit)
    p_std = icepool.Die(die).pool(params.num_std + mechanic.extra_std)
    p_bmp = icepool.Die(die).pool(params.num_bmp + mechanic.extra_bmp)
    d_result = mechanic(p_std, p_bmp)

    return H(d_result).lowest_terms()


def mechanic_icepool_fudged(
    params: Params,
    die: H,
    explode_limit: LimitT = 0,
) -> H:
    r"""
    This has the same interface as ``#!python mechanic_dyce``, but translates primitives
    and uses an ``#!python mechanic_icepool``-based implementation.
    """
    return mechanic_icepool(params, die, explode_limit=0) + _aggregate_exploded_deltas(
        die, explode_limit
    )


@cache
def _explosions_by_outcome_icepool(
    die: H, explode_limit: LimitT
) -> dict[int, icepool.Die]:
    return {
        outcome: icepool.Die(h)
        for outcome, h in _explosions_by_outcome(die, explode_limit).items()
    }
