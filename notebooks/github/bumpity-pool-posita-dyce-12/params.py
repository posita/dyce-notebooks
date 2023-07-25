import re
import traceback
from dataclasses import dataclass
from typing import ClassVar, Iterator

from dyce import H

__all__ = ()


@dataclass
class Params:
    num_std: int
    num_bump: int
    set_die: int  # zero-indexed, i.e., [0, num_std + num_bump)
    bonus_dice: tuple[int, ...] = ()
    extra_std: int = 0
    extra_bump: int = 0
    comment: str = ""
    override_die: H | None = None
    override_die_str: str | None = None

    NOTATION_RE: ClassVar = re.compile(
        r"""
    ^
    (?:\[(?P<override>[^]]+)\])?\s*
    (?P<std>\+?[1-9]\d*)\s*s\s*
    (?P<bump>(?:\+?[1-9]\d*)?\d)\s*b\s*
    @\s*(?P<set>\+?[1-9]\d*)\s*  # one-indexed (not zero-) for readability
    (?:<\s*(?P<ex_std>\+?[1-9]\d*)|>\s*(?P<ex_bump>\+?[1-9]\d*))?\s*
    (?P<bonuses>(?:\+\s*@\s*\+?[1-9]\d*\s*)*)  # one-indexed (not zero-) for readability
    (?:\#\s*(?P<comment>.*))?
    $
    """,
        re.IGNORECASE | re.VERBOSE,
    )
    BONUS_RE: ClassVar = re.compile(
        r"\+\s*@\s*(?P<bonus>[1-9]\d*)", re.IGNORECASE | re.VERBOSE
    )

    @classmethod
    def parse_from_notation(
        cls,
        s: str,
        override_die_map: dict[str, H] | None = None,
    ) -> Iterator["Params"]:
        for line in s.split("\n"):
            line = line.strip()

            if not line:
                continue

            m = cls.NOTATION_RE.match(line)

            if not m:
                continue

            try:
                set_str, std_str, bump_str, bonuses_str = m.group(
                    "set", "std", "bump", "bonuses"
                )
                num_std = int(std_str)
                num_bump = int(bump_str)
                set_die = int(set_str) - 1  # translate to zero-indexed
                bonus_dice = tuple(
                    int(bonus_str) - 1  # translate to zero-indexed
                    for bonus_str in cls.BONUS_RE.findall(bonuses_str)
                )
                ex_std = int(m.group("ex_std")) if m.group("ex_std") else 0
                ex_bump = int(m.group("ex_bump")) if m.group("ex_bump") else 0
                comment = m.group("comment").strip() if m.group("comment") else ""
                override_str = (
                    m.group("override").strip() if m.group("override") else ""
                )

                assert (
                    override_die_map or not override_str
                ), f"must provide override die map if overriding dice ({override_str})"

                params = Params(
                    num_std,
                    num_bump,
                    set_die,
                    bonus_dice,
                    ex_std,
                    ex_bump,
                    comment,
                    override_die_map[override_str] if override_str else None,  # type: ignore
                    override_str or None,
                )
            except (AssertionError, KeyError, TypeError, ValueError):
                traceback.print_exc()
                continue
            else:
                yield params

    def __str__(self) -> str:
        override_die = f"[{self.override_die_str}]" if self.override_die_str else ""
        bonuses = "".join(f"+@{bonus_die + 1}" for bonus_die in self.bonus_dice)
        extra_std = f"<{self.extra_std}" if self.extra_std else ""
        extra_bump = f">{self.extra_bump}" if self.extra_bump else ""
        comment = f"  # {self.comment}" if self.comment else ""

        return f"{override_die}{self.num_std}s{self.num_bump}b@{self.set_die + 1}{extra_std or extra_bump}{bonuses}{comment}"

    def __post_init__(self) -> None:
        pool_size = self.num_std + self.num_bump
        assert (
            0 <= self.set_die < pool_size
        ), "the set die must refer to a die within the pool ({self.set_die})"
        assert (
            self.num_std >= 1
        ), f"the standard pool must contain at least one die ({self.num_std})"
        assert (
            self.num_bump >= 0
        ), f"the bump pool must contain at least zero dice ({self.num_bump})"

        # Normalize relative differences in extra_std and extra_bump so that one is zero
        # and the other is greater-than-or-equal-to zero
        extra_lowest = min(self.extra_std, self.extra_bump)
        self.extra_std -= extra_lowest
        self.extra_bump -= extra_lowest

        assert (
            self.extra_std >= 0
            and self.extra_bump >= 0
            and 0 in (self.extra_std, self.extra_bump)
        ), f"normalization failed ({self.extra_std}, {self.extra_bump})"
        assert all(
            0 <= bonus_die < pool_size for bonus_die in self.bonus_dice
        ), f"each bonus die must refer to a die within the pool ({self.bonus_dice})"
