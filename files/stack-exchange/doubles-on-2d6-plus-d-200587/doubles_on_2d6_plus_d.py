from typing import Optional

from dyce import H, P
from dyce.p import RollT


def mechanic(
    die: H,
    base_target: int,
    extra_target: Optional[int],
    count_ones: bool,
) -> H:
    def _eval(roll: RollT) -> H:
        our_victories = 0
        their_victories = 0

        # Achieving our target goes to us; failing goes to them
        roll_total = sum(roll)

        if roll_total >= base_target:
            our_victories += 1

            if extra_target is not None and roll_total >= extra_target:
                our_victories += 1
        else:
            their_victories += 1

        # Doubles and triples go to us
        distinct_outcomes = set(roll)
        our_victories += 3 - len(distinct_outcomes)

        # Ones go to them
        if count_ones:
            their_victories += sum(outcome == 1 for outcome in roll)
        else:
            their_victories += any(outcome == 1 for outcome in roll)

        return our_victories, their_victories  # type: ignore

    return P.foreach(_eval, roll=P(6, 6, die))
