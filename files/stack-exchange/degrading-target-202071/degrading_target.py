from __future__ import annotations

from typing import Callable

from dyce import H
from dyce.evaluation import HResult, foreach

__all__ = (
    "degrading_target_customizable_adjustment",
    "reduce_once_per_try",
    "reduce_twice_per_try",
)


def degrading_target_nonperformant(
    die: H,
    initial_target: int,
    tries: int = 1,  # first try counts
) -> H:
    r"""
    While this is technically accurate, branching at whether each outcome meets the
    threshold leads to performance of roughly O(*n*!). In practice, this will only work
    with small dice or small targets. A *d* of ``#!python H(20)`` and *target* of
    ``#!python 20`` will take eons (maybe literally).
    """
    adjusted_target = initial_target - tries + 1

    def _callback(d_result: HResult):
        if d_result.outcome >= adjusted_target:
            return tries
        else:
            return degrading_target_nonperformant(
                d_result.h, initial_target, tries=tries + 1
            )

    return foreach(
        _callback,
        die,
        limit=-1,  # do not limit recursion
    )


def degrading_target_performant(
    die: H,
    initial_target: int,
    tries: int = 1,  # first try counts
) -> H:
    r"""
    Rather than branch on each outcome, we can branch on the likelihood of hitting a
    particular target. This takes our branching factor from *n* (the number of sides of
    our die) to 2, which leads to a performance of O(*n*), which is totally reasonable.
    """
    adjusted_target = initial_target - tries + 1
    succeeds_or_fails_at_adjusted_target_h = die.ge(adjusted_target)

    def _callback(ge_result: HResult):
        if ge_result.outcome == 1:
            return tries
        elif ge_result.outcome == 0:
            return degrading_target_performant(die, initial_target, tries=tries + 1)
        else:
            assert False, "should never be here"

    return foreach(
        _callback,
        succeeds_or_fails_at_adjusted_target_h,
        limit=-1,  # do not limit recursion
    )


def reduce_once_per_try(initial_target: int, tries: int) -> int:
    adjustment = tries - 1  # tries start at 1

    return initial_target - adjustment


def reduce_twice_per_try(initial_target: int, tries: int) -> int:
    adjustment = 2 * (tries - 1)  # tries start at 1

    return initial_target - adjustment


def degrading_target_customizable_adjustment(
    die: H,
    initial_target: int,
    adjusted_target_func: Callable[[int, int], int] = reduce_once_per_try,
    tries: int = 1,  # first try counts
) -> H:
    r"""
    This takes our performant approach above and adds the ability to substitute the way
    that the adjusted target is calculated. Callers can supply a callable for
    *adjusted_target_func* that takes the *initial_target* and the current value for
    *tries* and returns the adjusted target.
    """
    adjusted_target = adjusted_target_func(initial_target, tries)
    succeeds_or_fails_at_adjusted_target_h = die.ge(adjusted_target)

    def _callback(ge_result: HResult):
        if ge_result.outcome == 1:
            return tries
        elif ge_result.outcome == 0:
            return degrading_target_customizable_adjustment(
                die,
                initial_target,
                adjusted_target_func=adjusted_target_func,
                tries=tries + 1,
            )
        else:
            assert False, "should never be here"

    return foreach(
        _callback,
        succeeds_or_fails_at_adjusted_target_h,
        limit=-1,  # do not limit recursion
    )
