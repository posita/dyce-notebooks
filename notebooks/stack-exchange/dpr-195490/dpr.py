from enum import Enum, auto

from dyce import H

d6 = H(6)
d20 = H(20)


class ContestType(Enum):
    PC_ATTACKS = auto()
    PC_DEFENDS = auto()
    PC_V_PC = auto()


def expected_dmg_frm_rnd_pc_attacks(
    th_mod: int,
    th_pool: int,
    dc_target: int,
    dc_pool: int,
    dmg: int,
    arm: int,
    rof: int,
) -> H:
    def _dependent_term(
        th_die_outcome: int, th_pool_outcome: int, dc_pool_outcome: int
    ):
        modded_th = th_die_outcome + th_mod + th_pool_outcome
        modded_dc = dc_target + dc_pool_outcome
        hits = max(0, modded_th - modded_dc + 1)

        if th_die_outcome == 20:
            hits = max(hits, 1)  # crit hit for attacking PC
        elif th_die_outcome == 1:
            hits = 0  # crit miss for attacking PC

        return min(rof, hits) * max(0, dmg - arm)

    return H.foreach(
        _dependent_term,
        th_die_outcome=d20,
        th_pool_outcome=H({0: 1}) if th_pool == 0 else th_pool @ d6,
        dc_pool_outcome=H({0: 1}) if dc_pool == 0 else dc_pool @ d6,
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
    def _dependent_term(
        dc_die_outcome: int, dc_pool_outcome: int, th_pool_outcome: int
    ):
        modded_th = th_target + th_pool_outcome
        modded_dc = dc_die_outcome + dc_mod + dc_pool_outcome
        hits = max(0, modded_th - modded_dc + 1)

        if dc_die_outcome == 20:
            hits = 0  # crit miss against defending PC
        elif dc_die_outcome == 1:
            hits = max(hits, 1)  # crit hit against defending PC

        return min(rof, hits) * max(0, dmg - arm)

    return H.foreach(
        _dependent_term,
        dc_die_outcome=d20,
        dc_pool_outcome=H({0: 1}) if dc_pool == 0 else dc_pool @ d6,
        th_pool_outcome=H({0: 1}) if th_pool == 0 else th_pool @ d6,
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
        th_die_outcome: int,
        th_pool_outcome: int,
        dc_die_outcome: int,
        dc_pool_outcome: int,
    ):
        modded_th = th_die_outcome + th_mod + th_pool_outcome
        modded_dc = dc_die_outcome + dc_mod + dc_pool_outcome
        hits = max(0, modded_th - modded_dc + 1)

        if (
            th_die_outcome == 20
            and dc_die_outcome != 20
            or th_die_outcome != 1
            and dc_die_outcome == 1
        ):
            hits = max(hits, 1)  # crit hit
        elif (
            th_die_outcome == 1
            and dc_die_outcome != 1
            or th_die_outcome != 20
            and dc_die_outcome == 20
        ):
            hits = 0  # crit miss

        return min(rof, hits) * max(0, dmg - arm)

    return H.foreach(
        _dependent_term,
        th_die_outcome=d20,
        th_pool_outcome=H({0: 1}) if th_pool == 0 else th_pool @ d6,
        dc_die_outcome=d20,
        dc_pool_outcome=H({0: 1}) if dc_pool == 0 else dc_pool @ d6,
    )
