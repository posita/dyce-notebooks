import re
import traceback
import unittest
from dataclasses import dataclass
from typing import ClassVar, Iterator

from dyce import H

__all__ = ()


@dataclass
class Params:
    num_std: int
    num_bmp: int
    set_die: int  # zero-indexed, i.e., [0, num_std + num_bmp)
    extra_std: int = 0
    extra_bmp: int = 0
    bonus_dice: tuple[int, ...] = ()
    comment: str = ""
    override_die: H | None = None
    override_die_str: str | None = None

    NOTATION_RE: ClassVar = re.compile(
        r"""
    ^
    (?:\[(?P<override>[^]]+)\])?\s*
    (?P<std>\+?[1-9]\d*)\s*s\s*
    (?P<bmp>(?:\+?[1-9]\d*)?\d)\s*b\s*
    @\s*(?P<set>\+?[1-9]\d*)\s*  # one-indexed (not zero-) for readability
    (?:<\s*(?P<ex_std>\+?[1-9]\d*)|>\s*(?P<ex_bmp>\+?[1-9]\d*))?\s*
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
                set_str, std_str, bmp_str, bonuses_str = m.group(
                    "set", "std", "bmp", "bonuses"
                )
                num_std = int(std_str)
                num_bmp = int(bmp_str)
                set_die = int(set_str) - 1  # translate to zero-indexed
                bonus_dice = tuple(
                    int(bonus_str) - 1  # translate to zero-indexed
                    for bonus_str in cls.BONUS_RE.findall(bonuses_str)
                )
                ex_std = int(m.group("ex_std")) if m.group("ex_std") else 0
                ex_bmp = int(m.group("ex_bmp")) if m.group("ex_bmp") else 0
                comment = m.group("comment").strip() if m.group("comment") else ""
                override_str = (
                    m.group("override").strip() if m.group("override") else ""
                )

                assert (
                    override_die_map or not override_str
                ), f"must provide override die map if overriding dice ({override_str})"

                params = Params(
                    num_std,
                    num_bmp,
                    set_die,
                    ex_std,
                    ex_bmp,
                    bonus_dice,
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
        extra_bmp = f">{self.extra_bmp}" if self.extra_bmp else ""
        comment = f"  # {self.comment}" if self.comment else ""

        return f"{override_die}{self.num_std}s{self.num_bmp}b@{self.set_die + 1}{extra_std or extra_bmp}{bonuses}{comment}"

    def __post_init__(self) -> None:
        pool_size = self.num_std + self.num_bmp

        if self.num_std < 1:
            raise ValueError(
                f"the standard pool must contain at least one die ({self.num_std})"
            )

        if self.num_bmp < 0:
            raise ValueError(
                f"the bump pool must contain at least zero dice ({self.num_bmp})"
            )

        if not (0 <= self.set_die < pool_size):
            raise ValueError(
                f"the set die must refer to a die within the pool ({self.set_die})"
            )

        # Normalize relative differences in extra_std and extra_bmp so that one is zero
        # and the other is greater-than-or-equal-to zero
        extra_lowest = min(self.extra_std, self.extra_bmp)
        self.extra_std -= extra_lowest
        self.extra_bmp -= extra_lowest
        assert (
            self.extra_std >= 0
            and self.extra_bmp >= 0
            and 0 in (self.extra_std, self.extra_bmp)
        ), f"normalization failed ({self.extra_std}, {self.extra_bmp})"

        self.bonus_dice = tuple(self.bonus_dice)

        if not all(0 <= bonus_die < pool_size for bonus_die in self.bonus_dice):
            raise ValueError(
                f"each bonus die must refer to a die within the pool {self.bonus_dice}"
            )


class TestParams(unittest.TestCase):
    def test_bad_bonus_die(self):
        good_bonus_dice = tuple(range(3))
        extras = tuple(range(3))

        for bad_bonus_die in (-1, 3):
            bonus_dice = good_bonus_dice + (bad_bonus_die,)

            with self.assertRaisesRegex(
                ValueError,
                rf"\Aeach bonus die must refer to a die within the pool {re.escape(str(bonus_dice))}\Z",
                msg=f"bonus_dice = {bonus_dice}; bad_bonus_die = {bad_bonus_die}",
            ):
                Params(1, 2, 0, bonus_dice=bonus_dice)

            for extra_std in extras:
                with self.assertRaisesRegex(
                    ValueError,
                    rf"\Aeach bonus die must refer to a die within the pool {re.escape(str(bonus_dice))}\Z",
                    msg=f"extra_std = {extra_std}; bonus_dice = {bonus_dice}; bad_bonus_die = {bad_bonus_die}",
                ):
                    Params(1, 2, 0, extra_std=extra_std, bonus_dice=bonus_dice)

            for extra_bmp in extras:
                with self.assertRaisesRegex(
                    ValueError,
                    rf"\Aeach bonus die must refer to a die within the pool {re.escape(str(bonus_dice))}\Z",
                    msg=f"extra_bmp = {extra_bmp}; bonus_dice = {bonus_dice}; bad_bonus_die = {bad_bonus_die}",
                ):
                    Params(1, 2, 0, extra_bmp=extra_bmp, bonus_dice=bonus_dice)

    def test_bad_notation(self):
        override_die_map = {
            "d10": H(10),
            "d20": H(20),
        }

        for notation in (
            " nonsense 1s 0b @1",  # bad line
            " 1s 0b @1 nonsense ",  # bad line
            "0s 0b @1",  # bad num_std
            "1s 0b @0",  # bad set_die
            "1s 0b @1 <0",  # bad extra_std
            "1s 0b @1 >0",  # bad extra_bmp
            "1s 0b @1 +@0",  # bad bonus
            "[d8] 1s 0b @1 +@0",  # missing override
        ):
            self.assertEqual(
                len(tuple(Params.parse_from_notation(notation, override_die_map))),
                0,
                msg=f"notation = {notation!r}",
            )

    def test_bad_num_bmp(self):
        with self.assertRaisesRegex(
            ValueError,
            r"\Athe bump pool must contain at least zero dice \(-1\)\Z",
        ):
            Params(2, -1, 0)

    def test_bad_num_std(self):
        for num_std in (-1, 0):
            with self.assertRaisesRegex(
                ValueError,
                rf"\Athe standard pool must contain at least one die \({re.escape(str(num_std))}\)\Z",
                msg=f"num_std = {num_std}",
            ):
                Params(num_std, 1, 0)

    def test_bad_set_die(self):
        for set_die in (-1, 1):
            with self.assertRaisesRegex(
                ValueError,
                rf"\Athe set die must refer to a die within the pool \({re.escape(str(set_die))}\)\Z",
                msg=f"set_die = {set_die}",
            ):
                Params(1, 0, set_die)

    def test_bonus_iter(self):
        params = Params(3, 0, 0, bonus_dice=range(3))
        self.assertEqual(params.bonus_dice, (0, 1, 2))

    def test_defaults(self):
        params = Params(1, 0, 0)
        self.assertEqual(params.bonus_dice, ())
        self.assertEqual(params.extra_std, 0)
        self.assertEqual(params.extra_bmp, 0)
        self.assertEqual(params.comment, "")
        self.assertIsNone(params.override_die)
        self.assertIsNone(params.override_die_str)

    def test_extra(self):
        params = Params(1, 0, 0, extra_std=-1, extra_bmp=-1)
        self.assertEqual(params.extra_std, 0)
        self.assertEqual(params.extra_bmp, 0)

        params = Params(1, 0, 0, extra_std=-2, extra_bmp=-1)
        self.assertEqual(params.extra_std, 0)
        self.assertEqual(params.extra_bmp, 1)

        params = Params(1, 0, 0, extra_std=2, extra_bmp=-1)
        self.assertEqual(params.extra_std, 3)
        self.assertEqual(params.extra_bmp, 0)

    def test_minimal(self):
        params = Params(1, 0, 0)
        self.assertEqual(params.num_std, 1)
        self.assertEqual(params.num_bmp, 0)
        self.assertEqual(params.set_die, 0)

    def test_notation(self):
        default_extra_std = 0
        default_extra_bmp = 0
        default_bonus_dice = ()
        default_comment = ""
        default_override_die = None
        default_override_die_str = None

        override_die_map = {
            "d10": H(10),
            "d20": H(20),
        }

        for (
            notation,
            notation_str,
            num_std,
            num_bmp,
            set_die,
            extra_std,
            extra_bmp,
            bonus_dice,
            comment,
            override_die,
            override_die_str,
        ) in (
            (
                "1s 0b @1",
                "1s0b@1",
                1,  # num_std
                0,  # num_bmp
                0,  # set_die
                default_extra_std,
                default_extra_bmp,
                default_bonus_dice,
                default_comment,
                default_override_die,
                default_override_die_str,
            ),
            (
                "1s 2b @2",
                "1s2b@2",
                1,  # num_std
                2,  # num_bmp
                1,  # set_die
                default_extra_std,
                default_extra_bmp,
                default_bonus_dice,
                default_comment,
                default_override_die,
                default_override_die_str,
            ),
            (
                "1s 2b @2 >2",
                "1s2b@2>2",
                1,  # num_std
                2,  # num_bmp
                1,  # set_die
                default_extra_std,
                2,  # extra_bmp
                default_bonus_dice,
                default_comment,
                default_override_die,
                default_override_die_str,
            ),
            (
                "1s 2b @2 <2",
                "1s2b@2<2",
                1,  # num_std
                2,  # num_bmp
                1,  # set_die
                2,  # extra_std
                default_extra_bmp,
                default_bonus_dice,
                default_comment,
                default_override_die,
                default_override_die_str,
            ),
            (
                "1s 2b @2 +@1",
                "1s2b@2+@1",
                1,  # num_std
                2,  # num_bmp
                1,  # set_die
                default_extra_std,
                default_extra_bmp,
                (0,),  # bonus_dice
                default_comment,
                default_override_die,
                default_override_die_str,
            ),
            (
                "1s 2b @2 +@1 +@2 +@1",
                "1s2b@2+@1+@2+@1",
                1,  # num_std
                2,  # num_bmp
                1,  # set_die
                default_extra_std,
                default_extra_bmp,
                (0, 1, 0),  # bonus_dice
                default_comment,
                default_override_die,
                default_override_die_str,
            ),
            (
                "1s 0b @1#  ",
                "1s0b@1",
                1,  # num_std
                0,  # num_bmp
                0,  # set_die
                default_extra_std,
                default_extra_bmp,
                default_bonus_dice,
                default_comment,
                default_override_die,
                default_override_die_str,
            ),
            (
                "1s 0b @1  # hellooo  ",
                "1s0b@1  # hellooo",
                1,  # num_std
                0,  # num_bmp
                0,  # set_die
                default_extra_std,
                default_extra_bmp,
                default_bonus_dice,
                "hellooo",  # comment
                default_override_die,
                default_override_die_str,
            ),
            (
                "[d20] 1s 0b @1",
                "[d20]1s0b@1",
                1,  # num_std
                0,  # num_bmp
                0,  # set_die
                default_extra_std,
                default_extra_bmp,
                default_bonus_dice,
                default_comment,
                override_die_map["d20"],
                "d20",  # override_die_str
            ),
            (
                "[d10] 1s 2b @2 >2 +@1 +@2 +@1  # hellooo  ",
                "[d10]1s2b@2>2+@1+@2+@1  # hellooo",
                1,  # num_std
                2,  # num_bmp
                1,  # set_die
                0,  # extra_std
                2,  # extra_bmp
                (0, 1, 0),  # bonus_dice
                "hellooo",  # comment
                override_die_map["d10"],
                "d10",  # override_die_str
            ),
        ):
            try:
                (params,) = Params.parse_from_notation(notation, override_die_map)
            except Exception as exc:
                raise AssertionError(
                    f"unable to parse notation ({notation!r})"
                ) from exc

            self.assertEqual(str(params), notation_str, msg=f"notation = {notation!r}")
            self.assertEqual(params.num_std, num_std, msg=f"notation = {notation!r}")
            self.assertEqual(params.num_bmp, num_bmp, msg=f"notation = {notation!r}")
            self.assertEqual(params.set_die, set_die, msg=f"notation = {notation!r}")
            self.assertEqual(
                params.extra_std, extra_std, msg=f"notation = {notation!r}"
            )
            self.assertEqual(
                params.extra_bmp, extra_bmp, msg=f"notation = {notation!r}"
            )
            self.assertEqual(
                params.bonus_dice, bonus_dice, msg=f"notation = {notation!r}"
            )
            self.assertEqual(params.comment, comment, msg=f"notation = {notation!r}")

            if override_die is None:
                self.assertIsNone(params.override_die, msg=f"notation = {notation!r}")
                self.assertIsNone(
                    params.override_die_str, msg=f"notation = {notation!r}"
                )
            else:
                self.assertEqual(
                    params.override_die, override_die, msg=f"notation = {notation!r}"
                )
                self.assertEqual(
                    params.override_die_str,
                    override_die_str,
                    msg=f"notation = {notation!r}",
                )


if __name__ == "__main__":
    unittest.main()
