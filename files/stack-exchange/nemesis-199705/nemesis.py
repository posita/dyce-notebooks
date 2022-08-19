import sys
from enum import IntEnum

from dyce import H
from dyce.evaluation import HResult, foreach

if sys.version_info >= (3, 9):
    from functools import cache
else:
    from functools import lru_cache

    cache = lru_cache(maxsize=None)

d6 = H(6)


class Result(IntEnum):
    LOSS = -1
    WIN = 1


def nemesis(
    our_yang_pool_size: int,
    our_yin_pool_size: int,
    our_trait: int,
    our_initial_chi: int,
    their_yang_pool_size: int,
    their_yin_pool_size: int,
    their_trait: int,
    their_initial_chi: int,
) -> H:
    our_successes = d6.le(our_trait)
    our_anticipated_hits = (
        our_yang_pool_size @ our_successes if our_yang_pool_size else H({0: 1})
    )
    our_anticipated_blocks = (
        our_yin_pool_size @ our_successes if our_yin_pool_size else H({0: 1})
    )

    their_successes = d6.le(their_trait)
    their_anticipated_hits = (
        their_yang_pool_size @ their_successes if their_yang_pool_size else H({0: 1})
    )
    their_anticipated_blocks = (
        their_yin_pool_size @ their_successes if their_yin_pool_size else H({0: 1})
    )

    # We peg chi losses at 0, which assumes we can't gain chi back by blocking more hits
    # than were actually delivered
    our_anticipated_chi_losses = H(
        (max(outcome, 0), count)
        for outcome, count in (their_anticipated_hits - our_anticipated_blocks).items()
    )
    their_anticipated_chi_losses = H(
        (max(outcome, 0), count)
        for outcome, count in (our_anticipated_hits - their_anticipated_blocks).items()
    )

    @cache
    def _resolve_combat(
        our_chi_this_round: int,
        their_chi_this_round: int,
        this_round: int = 0,
    ) -> H:
        if our_chi_this_round < 0 or their_chi_this_round < 0:
            return (
                H({Result.WIN: 1})
                if our_chi_this_round >= their_chi_this_round
                else H({Result.LOSS: 1})
            )

        def _next(our_chi_loss: HResult, their_chi_loss: HResult) -> H:
            if our_chi_loss.outcome or their_chi_loss.outcome:
                return _resolve_combat(
                    our_chi_this_round - our_chi_loss.outcome,
                    their_chi_this_round - their_chi_loss.outcome,
                    this_round + 1,
                )
            else:
                # Neither side lost any chi, so consider this a dead-end to avoid
                # infinite recursion
                return H({})

        return foreach(
            _next,
            our_chi_loss=our_anticipated_chi_losses,
            their_chi_loss=their_anticipated_chi_losses,
            # We set limit to -1 to explicitly remove any externally imposed recursion
            # cutoff, since the default is effectively 1
            limit=-1,
        )

    return _resolve_combat(our_initial_chi, their_initial_chi)
