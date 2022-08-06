from enum import IntEnum, auto
from functools import partial
from typing import Optional, Union

from dyce import H, P


class HitResult(IntEnum):
    MISS = 0
    HIT = auto()
    CRIT = auto()


TO_HIT_NORMAL = H(20)
TO_HIT_DISADV = P(TO_HIT_NORMAL, TO_HIT_NORMAL).h(0)
TO_HIT_ADV = P(TO_HIT_NORMAL, TO_HIT_NORMAL).h(-1)


def _limit(h: H, lo: Optional[int] = None, hi: Optional[int] = None) -> H:
    def _eval(h_outcome: int) -> Union[H, int]:
        res = h_outcome
        res = res if lo is None else max(res, lo)
        res = res if hi is None else min(res, hi)

        return res

    return H.foreach(_eval, h_outcome=h)


assert _limit(H(6), lo=2) == H({2: 2, 3: 1, 4: 1, 5: 1, 6: 1})
assert _limit(H(6), hi=5) == H({1: 1, 2: 1, 3: 1, 4: 1, 5: 2})
assert _limit(H(6), lo=2, hi=5) == H({2: 2, 3: 1, 4: 1, 5: 2})


def _to_hit_result(
    to_hit_outcome: int,
    *,
    target: int,
    crits: tuple[int, ...],
) -> Union[H, int]:
    if to_hit_outcome in crits:
        return HitResult.CRIT
    elif to_hit_outcome == 1 or to_hit_outcome < target:
        return HitResult.MISS
    else:
        return HitResult.HIT


def crit_normal(target: int, to_hit: H) -> H:
    return H.foreach(
        partial(_to_hit_result, target=target, crits=(20,)),
        to_hit_outcome=to_hit,
    )


assert crit_normal(10, TO_HIT_NORMAL) == H(
    {HitResult.MISS: 9, HitResult.HIT: 10, HitResult.CRIT: 1}
)


def crit_improved(target: int, to_hit: H) -> H:
    return H.foreach(
        partial(_to_hit_result, target=target, crits=(19, 20)),
        to_hit_outcome=to_hit,
    )


assert crit_improved(10, TO_HIT_NORMAL) == H(
    {HitResult.MISS: 9, HitResult.HIT: 9, HitResult.CRIT: 2}
)


def crit_superior(target: int, to_hit: H) -> H:
    return H.foreach(
        partial(_to_hit_result, target=target, crits=(18, 19, 20)),
        to_hit_outcome=to_hit,
    )


assert crit_superior(10, TO_HIT_NORMAL) == H(
    {HitResult.MISS: 9, HitResult.HIT: 8, HitResult.CRIT: 3}
)


def expected_damage(
    expected_to_hit: H,
    normal_dmg: H,  # e.g., H(6) + 3 for 1d6+3
    extra_crit_dmg: H,  # e.g., H(6) for 1d6
) -> H:
    # Minimum normal damage is 0
    normal_dmg_ltd = _limit(normal_dmg, lo=0)
    # Minimum additional crit damage is 0
    crit_dmg_ltd = normal_dmg_ltd + _limit(extra_crit_dmg, lo=0)

    def _eval(expected_to_hit_outcome: int) -> Union[H, int]:
        if expected_to_hit_outcome == HitResult.CRIT:
            return crit_dmg_ltd
        elif expected_to_hit_outcome == HitResult.HIT:
            return normal_dmg_ltd
        else:
            return 0

    return H.foreach(_eval, expected_to_hit_outcome=expected_to_hit)


assert expected_damage(crit_improved(13, TO_HIT_DISADV), H(6) + 3, H(6)) == H(
    {
        0: 3024,
        4: 90,
        5: 91,
        6: 92,
        7: 93,
        8: 94,
        9: 95,
        10: 6,
        11: 5,
        12: 4,
        13: 3,
        14: 2,
        15: 1,
    }
)
assert expected_damage(crit_improved(13, TO_HIT_NORMAL), H(6) + 3, H(6)) == H(
    {
        0: 216,
        4: 18,
        5: 19,
        6: 20,
        7: 21,
        8: 22,
        9: 23,
        10: 6,
        11: 5,
        12: 4,
        13: 3,
        14: 2,
        15: 1,
    }
)
assert expected_damage(crit_improved(13, TO_HIT_ADV), H(6) + 3, H(6)) == H(
    {
        0: 1296,
        4: 270,
        5: 289,
        6: 308,
        7: 327,
        8: 346,
        9: 365,
        10: 114,
        11: 95,
        12: 76,
        13: 57,
        14: 38,
        15: 19,
    }
)
