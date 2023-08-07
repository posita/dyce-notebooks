from enum import Enum, auto

from dyce import H
from dyce.evaluation import HResult, foreach

d6 = H(6)
d20 = H(20)


class ContestType(Enum):
    PC_ATTACKS = auto()
    PC_DEFENDS = auto()
    PC_VS_PC = auto()


def expected_dmg_frm_rnd_pc_attacks(
    th_mod: int,
    th_pool: int,
    dc_target: int,
    dc_pool: int,
    dmg: int,
    arm: int,
    rof: int,
) -> H:
    def _dependent_term(th_die: HResult, th_pool: HResult, dc_pool: HResult):
        modded_th = th_die.outcome + th_mod + th_pool.outcome
        modded_dc = dc_target + dc_pool.outcome
        hits = max(0, modded_th - modded_dc + 1)

        if th_die.outcome == 20:
            hits = max(hits, 1)  # crit hit for attacking PC
        elif th_die.outcome == 1:
            hits = 0  # crit miss for attacking PC

        return min(rof, hits) * max(0, dmg - arm)

    return foreach(
        _dependent_term,
        th_die=d20,
        th_pool=H({0: 1}) if th_pool == 0 else th_pool @ d6,
        dc_pool=H({0: 1}) if dc_pool == 0 else dc_pool @ d6,
    )


def expected_dmg_frm_rnd_pc_defends(
    dc_mod: int,
    dc_pool: int,
    th_target: int,
    th_pool: int,
    dmg: int,
    arm: int,
    rof: int,
) -> H:
    def _dependent_term(dc_die: HResult, dc_pool: HResult, th_pool: HResult):
        modded_th = th_target + th_pool.outcome
        modded_dc = dc_die.outcome + dc_mod + dc_pool.outcome
        hits = max(0, modded_th - modded_dc + 1)

        if dc_die.outcome == 20:
            hits = 0  # crit miss against defending PC
        elif dc_die.outcome == 1:
            hits = max(hits, 1)  # crit hit against defending PC

        return min(rof, hits) * max(0, dmg - arm)

    return foreach(
        _dependent_term,
        dc_die=d20,
        dc_pool=H({0: 1}) if dc_pool == 0 else dc_pool @ d6,
        th_pool=H({0: 1}) if th_pool == 0 else th_pool @ d6,
    )


def expected_dmg_frm_rnd_pc_v_pc(
    th_mod: int,
    th_pool: int,
    dc_mod: int,
    dc_pool: int,
    dmg: int,
    arm: int,
    rof: int,
) -> H:
    def _dependent_term(
        th_die: HResult, th_pool: HResult, dc_die: HResult, dc_pool: HResult
    ):
        modded_th = th_die.outcome + th_mod + th_pool.outcome
        modded_dc = dc_die.outcome + dc_mod + dc_pool.outcome
        hits = max(0, modded_th - modded_dc + 1)

        if (
            th_die.outcome == 20
            and dc_die.outcome != 20
            or th_die.outcome != 1
            and dc_die.outcome == 1
        ):
            hits = max(hits, 1)  # crit hit
        elif (
            th_die.outcome == 1
            and dc_die.outcome != 1
            or th_die.outcome != 20
            and dc_die.outcome == 20
        ):
            hits = 0  # crit miss

        return min(rof, hits) * max(0, dmg - arm)

    return foreach(
        _dependent_term,
        th_die=d20,
        th_pool=H({0: 1}) if th_pool == 0 else th_pool @ d6,
        dc_die=d20,
        dc_pool=H({0: 1}) if dc_pool == 0 else dc_pool @ d6,
    )
