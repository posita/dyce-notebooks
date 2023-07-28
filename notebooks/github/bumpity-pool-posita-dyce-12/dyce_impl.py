import unittest
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
    return mechanic_dyce_base(params, die) + _aggregate_exploded_deltas(
        die, explode_limit
    )


def mechanic_dyce_base(
    params: Params,
    die: H,
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

    return unexploded_result


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


class TestExplosions(unittest.TestCase):
    def test_explosions_by_outcome(self):
        d2 = H(2)
        self.assertEqual(_explosions_by_outcome(d2, explode_limit=0), {})
        self.assertEqual(
            _explosions_by_outcome(d2, explode_limit=1),
            {
                # H(2).eq(1) -> H({False: 1, True: 1}) ; explode(H(2), limit=1) -> H({2: 3, 3: 1})  # i.e., 1+1 (2) * 1, 1+2 (3) * 1, 2 * 2
                1: H({0: 4, 2: 3, 3: 1}),
                # H(2).eq(2) -> H({False: 1, True: 1}) ; explode(H(2), limit=1) -> H({2: 3, 3: 1})  # i.e., 1 * 2, 2+1 (3) * 1, 2+2 (4) * 1
                2: H({0: 4, 1: 2, 3: 1, 4: 1}),
            },
        )
        self.assertEqual(
            _explosions_by_outcome(H({1: 1, 2: 2}), explode_limit=1),
            {
                # H({1: 1, 2: 2}).eq(1) -> H({False: 2, True: 1}) ; explode(H({1: 1, 2: 2}), limit=1) -> H({2: 7, 3: 2})  # i.e., 1+1 (2) * 1, 1+2 (3) * 2, 2 * 6
                1: H({0: 18, 2: 7, 3: 2}),
                # H({1: 1, 2: 2}).eq(2) -> H({False: 1, True: 2}) ; explode(H({1: 1, 2: 2}), limit=1) -> H({1: 3, 2: 2, 3: 4})  # i.e., 1 * 3, 2+1 (3) * 2, 2+2 (4) * 4
                2: H({0: 9, 1: 6, 3: 4, 4: 8}),
            },
        )
        self.assertEqual(
            _explosions_by_outcome(d2, explode_limit=2),
            {
                # H(2).eq(1) -> H({False: 1, True: 1}) ; explode(H(2), limit=1) -> H({2: 4, 3: 3, 4: 1})  # i.e., 1+1+1 (3) * 1, 1+1+2 (4) * 1, 1+2 (3) * 2, 2 * 4
                1: H({0: 8, 2: 4, 3: 3, 4: 1}),
                # H(2).eq(2) -> H({False: 1, True: 1}) ; explode(H(2), limit=1) -> H({1: 4, 3: 2, 5: 1, 6: 1})  # i.e., 1 * 4, 2+1 (3) * 2, 2+2+1 (5) * 1, 2+2+2 (6) * 1
                2: H({0: 8, 1: 4, 3: 2, 5: 1, 6: 1}),
            },
        )

    def test_aggregate_exploded_deltas(self):
        d2 = H(2)
        self.assertEqual(_aggregate_exploded_deltas(d2, 0), H({0: 1}))
        self.assertEqual(_aggregate_exploded_deltas(d2, 1), H({0: 2, 1: 1, 2: 1}))
        self.assertEqual(
            _aggregate_exploded_deltas(H({1: 1, 2: 2}), 1), H({0: 12, 1: 5, 2: 10})
        )
        self.assertEqual(
            _aggregate_exploded_deltas(d2, 2), H({0: 8, 1: 2, 2: 3, 3: 2, 4: 1})
        )


class TestMechanic(unittest.TestCase):
    def test_base(self):
        d2, d6 = H(2), H(6)

        notation = "1s0b@1"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(mechanic_dyce_base(params, d2), d2)

        notation = "1s1b@2"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(mechanic_dyce_base(params, d2), H({2: 2, 3: 1, 4: 1}))

        notation = "1s0b@1>1"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(mechanic_dyce_base(params, d2), H({1: 1, 2: 3}))

        notation = "1s0b@1<1"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(mechanic_dyce_base(params, d2), H({1: 3, 2: 1}))

        notation = "1s0b@1+@1"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(mechanic_dyce_base(params, d2), 2 * d2)

        notation = "1s0b@1>1+@1"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(mechanic_dyce_base(params, d2), H({2: 1, 4: 3}))

        notation = "1s0b@1<1+@1"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(mechanic_dyce_base(params, d2), H({2: 3, 4: 1}))

        notation = "1s0b@1>1"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(
            mechanic_dyce_base(params, d6), H({1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11})
        )

        notation = "1s0b@1<1"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(
            mechanic_dyce_base(params, d6), H({1: 11, 2: 9, 3: 7, 4: 5, 5: 3, 6: 1})
        )

        notation = "2s1b@2"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(
            mechanic_dyce_base(params, d6), H({1: 3, 2: 13, 3: 20, 4: 24, 5: 25, 6: 23})
        )

        notation = "1s2b@2"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(
            mechanic_dyce_base(params, d6), H({1: 1, 2: 15, 3: 29, 4: 43, 5: 57, 6: 71})
        )

        notation = "1s2b@1>1"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(
            mechanic_dyce_base(params, d6),
            H({1: 7, 2: 57, 3: 98, 4: 118, 5: 105, 6: 47}),
        )

        notation = "1s2b@1<1"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(
            mechanic_dyce_base(params, d6),
            H({1: 421, 2: 363, 3: 269, 4: 163, 5: 69, 6: 11}),
        )

        notation = "1s2b@1+@3"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(
            mechanic_dyce_base(params, d6),
            H(
                {
                    2: 1,
                    3: 4,
                    4: 9,
                    5: 16,
                    6: 25,
                    7: 36,
                    8: 35,
                    9: 32,
                    10: 27,
                    11: 20,
                    12: 11,
                }
            ),
        )

        notation = "1s2b@1>1+@3"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(
            mechanic_dyce_base(params, d6),
            H(
                {
                    2: 1,
                    3: 4,
                    4: 15,
                    5: 35,
                    6: 71,
                    7: 123,
                    8: 195,
                    9: 239,
                    10: 252,
                    11: 220,
                    12: 141,
                }
            ),
        )

        notation = "1s2b@1<1+@3"
        (params,) = Params.parse_from_notation(notation)
        self.assertEqual(
            mechanic_dyce_base(params, d6),
            H(
                {
                    2: 21,
                    3: 80,
                    4: 147,
                    5: 208,
                    6: 237,
                    7: 216,
                    8: 163,
                    9: 112,
                    10: 69,
                    11: 32,
                    12: 11,
                }
            ),
        )


if __name__ == "__main__":
    unittest.main()
