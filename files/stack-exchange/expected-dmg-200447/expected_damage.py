from enum import IntEnum, auto
from functools import partial
from typing import Callable, Optional, Union

from dyce import H, P


class HitResult(IntEnum):
    MISS = 0
    HIT = auto()
    CRIT = auto()


to_hit_normal = H(20)
to_hit_disadv = P(to_hit_normal, to_hit_normal).h(0)
to_hit_adv = P(to_hit_normal, to_hit_normal).h(-1)


def bounds(
    h: H, min_outcome: Optional[int] = None, max_outcome: Optional[int] = None
) -> H:
    def _eval(h_outcome: int) -> Union[H, int]:
        this_min = h_outcome if min_outcome is None else min_outcome
        this_max = h_outcome if max_outcome is None else max_outcome
        return max(min(h_outcome, this_max), this_min)

    return H.foreach(_eval, h_outcome=h)


def crit_normal(target: int, to_hit: H) -> H:
    return H.foreach(partial(to_hit_result, target=target), attack_outcome=to_hit)


def crit_improved(target: int, to_hit: H) -> H:
    return H.foreach(
        partial(to_hit_result, target=target, crits=(19, 20)), attack_outcome=to_hit
    )


def crit_superior(target: int, to_hit: H) -> H:
    return H.foreach(
        partial(to_hit_result, target=target, crits=(18, 19, 20)),
        attack_outcome=to_hit,
    )


def to_hit_result(
    attack_outcome: int,
    *,
    target: int,
    crits: tuple[int, ...] = (20,),
) -> Union[H, int]:
    if attack_outcome in crits:
        return HitResult.CRIT
    elif attack_outcome == 1 or attack_outcome < target:
        return HitResult.MISS
    else:
        return HitResult.HIT


def expected_damage(
    target: int,
    to_hit: H,  # e.g., normal, adv, disadv
    to_hit_func: Callable[[int, H], H],  # e.g., crit_normal, crit_improved, etc.
    normal_dmg: H,  # e.g., H(6) + 3 for 1d6+3
    extra_crit_dmg: H,  # e.g., H(6) for 1d6
) -> H:
    expected_to_hit = to_hit_func(target, to_hit)

    def _eval(expected_to_hit_outcome: int) -> Union[H, int]:
        if expected_to_hit_outcome == HitResult.CRIT:
            # Minimum damage is 1
            return bounds(normal_dmg + extra_crit_dmg, min_outcome=1)
        elif expected_to_hit_outcome == HitResult.HIT:
            # Minimum damage is 1
            return bounds(normal_dmg, min_outcome=1)
        else:
            return 0

    return H.foreach(_eval, expected_to_hit_outcome=expected_to_hit)
