import sys
from fractions import Fraction
from time import time

from dyce import H

try:
    from dyce.evaluation import LimitT
except ImportError:
    from dyce.evaluation import _LimitT as LimitT

# Local imports
from dyce_impl import Params, mechanic_dyce_fudged
from icepool_impl import mechanic_icepool, mechanic_icepool_fudged

__all__ = ()


_OVERRIDE_DIE_MAP = {
    "d4": H(4),
    "d6": H(6),
    "d8": H(8),
    "d10": H(10),
    "d12": H(12),
    "d20": H(20),
    "d0": H({0: 1}),
    "d10*2": H(10) * 2,
}


def main() -> None:
    die = H(20)  # d20
    explode_limit: LimitT = Fraction(1, 10_000)

    for notation in sys.argv[1:]:
        try:
            (params,) = Params.parse_from_notation(notation, _OVERRIDE_DIE_MAP)
        except ValueError as exc:
            print(
                f"\nignoring poorly formed notation {notation!r}: {exc}",
                file=sys.stderr,
            )
            continue

        print(f"\n= = = = <([    {params!s}    ])> = = = =")
        t0 = time()
        dyce_result = mechanic_dyce_fudged(params, die, explode_limit)
        t1 = time()
        print(f"\n    dyce (fudged; {t1 - t0:.2f} seconds) ->")
        print(f"        {dyce_result}")

        if False:
            t0 = time()
            icepool_result = mechanic_icepool_fudged(params, die, explode_limit)
            t1 = time()
            print(f"\n    icepool (fudged; {t1 - t0:.2f} seconds) ->")
            print(f"        {icepool_result}")
            assert dyce_result == icepool_result

            if params.extra_bmp == params.extra_std == 0:
                t0 = time()
                icepool_result = mechanic_icepool(params, die, explode_limit)
                t1 = time()
                print(f"\n    icepool (real; {t1 - t0:.2f} seconds) ->")
                print(f"        {icepool_result}")


if __name__ == "__main__":
    main()
