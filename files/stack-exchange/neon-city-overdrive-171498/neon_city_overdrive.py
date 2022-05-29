import sys
from typing import Union

from dyce import H, P
from dyce.p import RollT
from numerary import RealLike

if sys.version_info >= (3, 9):
    from functools import cache
else:
    from functools import lru_cache

    cache = lru_cache(maxsize=None)


@cache
def nco_karonen(
    a_pool_size: int,
    d_pool_size: int,
    n: int = 6,
) -> H:
    # A single one with n - 1 blanks/zeros (e.g., H({0: 5, 1: 1})) where n is 6). This
    # is a histogram modeling how often one can expect to roll a value of n on a single
    # n-sided die.
    dn_w_blanks = H(n).eq(n)

    if a_pool_size <= 0:
        # We have an empty action pool. We express this as a single-sided die with a
        # zero face (i.e., it will only roll blanks).
        num_a_at_n = H({0: 1})
    else:
        # We still have dice in our action pool. We express this as a histogram modeling
        # how many values of n one can roll using a pool of a_pool_size n-sided dice.
        # For example, where a_pool_size is 3 and n is 6, this will be H({0: 125, 1: 75,
        # 2: 15, 3: 1}). This means that when rolling three six-sided dice, one can
        # expect to roll three 6s once out of every 216 (125 + 75 + 15 + 1) times, two
        # 6s and one non-6 15 out of every 216 times, one 6 and two non-6s 75 out of
        # every 216 times, and three non-6s 125 out of every 216 times.
        num_a_at_n = a_pool_size @ dn_w_blanks

    if d_pool_size <= 0:
        # We have an empty danger pool (only blanks left)
        num_d_at_n = H({0: 1})
    else:
        # A histogram modeling how many values of n one can roll using a pool of
        # d_pool_size n-sided dice
        num_d_at_n = d_pool_size @ dn_w_blanks

    # We're now in a position where we want to make a comparison between two separate
    # histograms (our action pool and our danger pool). We want to do something *like*
    # `num_a_at_n - num_d_at_n`, but that is insufficient. Why? It's not enough to know
    # that the difference nets out to a particular value. We need to know how many of
    # each pool needs to be removed in the process. A net zero from having no sixes is
    # very different than a net zero from each pool having four sixes.
    #
    # This means we want to make a dependent computation between specific outcomes from
    # two independent histograms. dyce has several mechanisms for this. H.foreach is
    # particularly well-suited to compactly expressing a dependent term deriving from
    # multiple independent terms, as in this case.
    #
    # We define the dependent term as a callback function and then map sources of the
    # independent outcomes. H.foreach invokes our callback with each combination from
    # the independent sources and handles the probability accounting.

    def cancel_dependent_term(
        count_of_actions_at_n: int,
        count_of_dangers_at_n: int,
    ) -> Union[H, int]:
        how_many_actions_remain_at_n = count_of_actions_at_n - count_of_dangers_at_n

        if how_many_actions_remain_at_n > 0:
            # We found the value of n where we are left with more actions than dangers
            if n == 6:
                # >6 encodes number of boons. 6 is zero boons, 7 is one boon, 8 is two
                # >boons, etc.
                return n + how_many_actions_remain_at_n - 1
            else:
                return n
        else:
            # We have no actions (left) for this value of n
            if n > 1:
                # Pull any actions or dangers at n out of their respective pools and
                # recurse at n - 1. We exploit the feature that nested functions can
                # access the scopes of their defining functions.
                return nco_karonen(
                    a_pool_size - count_of_actions_at_n,
                    d_pool_size - count_of_dangers_at_n,
                    n - 1,
                )
            else:
                # All action dice have been canceled.
                return 0

    return H.foreach(
        cancel_dependent_term,
        count_of_actions_at_n=num_a_at_n,
        count_of_dangers_at_n=num_d_at_n,
    )


def nco_carcer(
    a_pool_size: int,
    d_pool_size: int,
) -> H:
    a_pool = a_pool_size @ P(6) if a_pool_size > 0 else P(H({0: 1}))
    d_pool = d_pool_size @ P(6) if d_pool_size > 0 else P(H({0: 1}))

    def cancel_dependent_term(
        a_roll: RollT,
        d_roll: RollT,
    ) -> int:
        a_roll_as_h = H(a_roll)  # count up outcomes for the action roll
        d_roll_as_h = H(d_roll)  # count up outcomes for the danger roll
        res = 0
        for n in range(6, 0, -1):
            a_vs_d_at_n = a_roll_as_h.get(n, 0) - d_roll_as_h.get(n, 0)
            if a_vs_d_at_n > 0:
                if n == 6:
                    res = n + a_vs_d_at_n - 1
                else:
                    res = n
                # We found the value of n where we are left with more actions than
                # dangers so we can stop looking
                break
        return res

    # P.foreach behaves like H.foreach, but whose dependent term’s arguments are rolls,
    # not outcomes
    return P.foreach(cancel_dependent_term, a_roll=a_pool, d_roll=d_pool)


def nco_so_dangerous(
    a_pool_size: int,
    d_pool_size: int,
) -> H:
    def _a_vs_d(a_roll: RollT, d_roll: RollT) -> RealLike:
        actions_not_canceled_by_dangers = []
        # We want to walk through each roll, opportunistically canceling the best action
        # we can given our maximum unspent danger. Rolls are ordered least-to- greatest,
        # so we start at the end and walk backwards, accumulating or canceling actions
        # as we go.
        action_index = len(a_roll) - 1
        danger_index = len(d_roll) - 1

        while action_index >= 0:
            if danger_index >= 0 and a_roll[action_index] <= d_roll[danger_index]:
                # We have unspent danger, and our current (max unexamined) action is
                # cancelable by our current (max unspent) danger, so we decrement both
                # counters without counting the action
                action_index -= 1
                danger_index -= 1
            else:
                # Either we're out of dangers, or our current (max unexamined) action is
                # not cancelable (i.e., greater than) our current (max unspent) danger,
                # so we count that action and decrement only the action counter, leaving
                # any unspent danger for the next iteration
                actions_not_canceled_by_dangers.append(a_roll[action_index])
                action_index -= 1

        if actions_not_canceled_by_dangers:
            # We have at least one remaining action. Note: We accumulated actions not
            # canceled by dangers in order of greatest-to-least above, which is the
            # opposite of roll ordering.
            result = actions_not_canceled_by_dangers[0]

            if result == 6:
                result += sum(
                    1 for action in actions_not_canceled_by_dangers[1:] if action == 6
                )
        else:
            # We're out of actions, so reduce the base number by one for each unspent
            # six in the danger pool
            zero_actions_base = 0
            unspent_d = d_roll[: max(0, danger_index + 1)]
            result = zero_actions_base - sum(1 for d in unspent_d if d == 6)

        return result

    a_pool = a_pool_size @ P(6) if a_pool_size > 0 else P(H({0: 1}))
    d_pool = d_pool_size @ P(6) if d_pool_size > 0 else P(H({0: 1}))

    return P.foreach(_a_vs_d, a_roll=a_pool, d_roll=d_pool)
