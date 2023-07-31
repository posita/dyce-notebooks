import unittest
from functools import cache

from dyce import H, P
from dyce.evaluation import HResult, PResult, PWithSelection, explode, foreach

try:
    from dyce.evaluation import LimitT
except ImportError:
    from dyce.evaluation import _LimitT as LimitT

# Local imports
from params import Params

__all__ = ()


def mechanic_dyce_fudged(params: Params, die: H, explode_limit: LimitT = 0) -> H:
    return mechanic_dyce_base(params, die) + _aggregate_exploded_deltas(
        die, explode_limit
    )


def mechanic_dyce_base(params: Params, die: H) -> H:
    r"""
    *params* and *die* are used to describe the pool and mechanic constraints. Note this
    interface only allows for homogeneous pools. *explode_limit* has same meaning as
    ``#!python dyce.evaluation.expandable``.
    """
    pool_size = params.num_std + params.num_bmp
    extra_std = min(params.extra_std, pool_size)
    extra_bmp = min(params.extra_bmp, pool_size)
    # double each standard outcome (all even; assumes all outcomes are integers and support
    # bit-wise operations)
    p_std = (params.num_std + extra_std) @ P(
        H(
            (outcome << 1, count)  # faster than outcome * 2
            for outcome, count in die.items()
        )
    )
    # double each bump outcome and add one (all odd)
    p_bmp = (params.num_bmp + extra_bmp) @ P(
        H(
            (outcome << 1 | 0x1, count)  # faster than outcome * 2 + 1
            for outcome, count in die.items()
        )
    )

    if params.extra_std:
        extra_bonus = -2 * max(params.extra_std - pool_size, 0)
        roll_slice = slice(None, pool_size)
    elif params.extra_bmp:
        extra_bonus = 2 * max(params.extra_bmp - pool_size, 0)
        roll_slice = slice(-pool_size, None)
    else:
        extra_bonus = 0
        roll_slice = slice(None, pool_size)

    def _mechanic(std: PResult, bmp: PResult | None = None):
        roll = list(std.roll)

        if bmp is not None:
            roll.extend(bmp.roll)
            roll.sort()
            roll = roll[roll_slice]

        assert len(roll) == pool_size
        check_die = params.set_die
        shifted_check_outcome = roll[check_die]

        # check to see if the shifted check outcome is odd; if so, it's a bump die
        if shifted_check_outcome & 0x1:  # faster than check_outcome % 2 == 1
            check_die = (check_die + 1) % pool_size
            shifted_check_outcome = roll[check_die]

        # add the original value for the check outcome to the total
        total_outcome = shifted_check_outcome >> 1  # faster than outcome // 2

        if check_die < params.set_die:
            wrapped_outcome = roll[params.set_die] >> 1  # faster than outcome // 2
            total_outcome += wrapped_outcome

        return (
            total_outcome
            # halve each bonus outcome (restores original value)
            + sum(
                roll[bonus_die] >> 1  # faster than outcome // 2
                for bonus_die in params.bonus_dice
            )
            + extra_bonus
        )

    if p_bmp:
        unexploded_result = foreach(
            _mechanic,
            PWithSelection(p_std, (roll_slice,)),
            PWithSelection(p_bmp, (roll_slice,)),
        )
    else:
        unexploded_result = foreach(_mechanic, PWithSelection(p_std, (roll_slice,)))

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
    def test_base_simple(self):
        d2 = H(2)

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

    def test_base_options(self):
        d6 = H(6)

        for notation, expected in (
            ("4s1b@4", H({1: 3, 2: 101, 3: 409, 4: 879, 5: 1283, 6: 1213})),
            ("4s1b@3", H({1: 21, 2: 171, 3: 330, 4: 382, 5: 291, 6: 101})),
            ("5s0b@1", H({1: 4651, 2: 2101, 3: 781, 4: 211, 5: 31, 6: 1})),
            ("5s0b@3", H({1: 23, 2: 113, 3: 188, 4: 188, 5: 113, 6: 23})),
            ("5s0b@5", H({1: 1, 2: 31, 3: 211, 4: 781, 5: 2101, 6: 4651})),
            ("4s1b@1", H({1: 671, 2: 369, 3: 175, 4: 65, 5: 15, 6: 1})),
            ("4s1b@2", H({1: 513, 2: 1199, 3: 1123, 4: 717, 5: 293, 6: 43})),
            ("4s1b@3", H({1: 21, 2: 171, 3: 330, 4: 382, 5: 291, 6: 101})),
            ("4s1b@4", H({1: 3, 2: 101, 3: 409, 4: 879, 5: 1283, 6: 1213})),
            (
                "4s1b@5",
                H(
                    {
                        2: 16,
                        3: 145,
                        4: 591,
                        5: 1666,
                        6: 3790,
                        7: 861,
                        8: 435,
                        9: 190,
                        10: 66,
                        11: 15,
                        12: 1,
                    }
                ),
            ),
            ("1s0b@1>2", H({3: 1, 4: 3, 5: 5, 6: 7, 7: 9, 8: 11})),
            ("1s0b@1<2", H({-1: 11, 0: 9, 1: 7, 2: 5, 3: 3, 4: 1})),
            ("1s2b@2", H({1: 1, 2: 15, 3: 29, 4: 43, 5: 57, 6: 71})),
            ("1s2b@1>1", H({1: 7, 2: 57, 3: 98, 4: 118, 5: 105, 6: 47})),
            ("1s2b@1<1", H({1: 421, 2: 363, 3: 269, 4: 163, 5: 69, 6: 11})),
            (
                "1s2b@1+@3",
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
            ),
            (
                "1s2b@1>1+@3",
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
            ),
            (
                "1s2b@1<1+@3",
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
            ),
        ):
            try:
                (params,) = Params.parse_from_notation(notation)
            except Exception as exc:
                raise AssertionError(
                    f"unable to parse notation ({notation!r})"
                ) from exc

            actual = mechanic_dyce_base(params, d6)
            self.assertEqual(expected, actual, msg=f"notation = {notation!r}")


if __name__ == "__main__":
    unittest.main()
