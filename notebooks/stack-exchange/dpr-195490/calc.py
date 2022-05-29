from enum import Enum, auto

import matplotlib.pyplot
from anydyce.viz import plot_burst_subplot
from dyce import H
from IPython.display import display
from ipywidgets import widgets

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


def show():
    def _display(
        contest_type: ContestType,
        th_target: int,
        th_mod: int,
        th_pool: int,
        dmg: int,
        rof: int,
        dc_target: int,
        dc_mod: int,
        dc_pool: int,
        arm: int,
    ) -> None:
        if contest_type is ContestType.PC_ATTACKS:
            th_mod_widget.layout.visibility = "visible"
            th_target_widget.layout.visibility = "hidden"
            dc_mod_widget.layout.visibility = "hidden"
            dc_target_widget.layout.visibility = "visible"
            expected_dmg = expected_dmg_frm_rnd_pc_attacks(
                th_mod=th_mod,
                th_pool=th_pool,
                dc_target=dc_target,
                dc_pool=dc_pool,
                dmg=dmg,
                arm=arm,
                rof=rof,
            )
        elif contest_type is ContestType.PC_DEFENDS:
            th_mod_widget.layout.visibility = "hidden"
            th_target_widget.layout.visibility = "visible"
            dc_mod_widget.layout.visibility = "visible"
            dc_target_widget.layout.visibility = "hidden"
            expected_dmg = expected_dmg_frm_rnd_pc_defends(
                dc_pool=dc_pool,
                dc_mod=dc_mod,
                th_target=th_target,
                th_pool=th_pool,
                dmg=dmg,
                arm=arm,
                rof=rof,
            )
        elif contest_type is ContestType.PC_V_PC:
            th_mod_widget.layout.visibility = "visible"
            th_target_widget.layout.visibility = "hidden"
            dc_mod_widget.layout.visibility = "visible"
            dc_target_widget.layout.visibility = "hidden"
            expected_dmg = expected_dmg_frm_rnd_pc_v_pc(
                th_mod=th_mod,
                th_pool=th_pool,
                dc_mod=dc_mod,
                dc_pool=dc_pool,
                dmg=dmg,
                arm=arm,
                rof=rof,
            )

        plot_burst_subplot(
            expected_dmg,
            alpha=0.5,
            title=f"Expected damage for round\nmean: {expected_dmg.mean():0.02f}\nstdev: {expected_dmg.stdev():0.02f}",
        )

        matplotlib.pyplot.show()

    contest_type_widget = widgets.RadioButtons(
        value=ContestType.PC_ATTACKS,
        options=(
            ("PC attacking", ContestType.PC_ATTACKS),
            ("PC defending", ContestType.PC_DEFENDS),
            ("PC v. PC", ContestType.PC_V_PC),
        ),
    )

    th_target_widget = widgets.IntSlider(
        value=10,
        min=1,
        max=30,
        step=1,
        continuous_update=False,
        description="TH target",
    )

    th_mod_widget = widgets.IntSlider(
        value=0,
        min=-10,
        max=10,
        step=1,
        readout_format="+0",
        continuous_update=False,
        description="TH mods",
    )

    th_pool_widget = widgets.IntSlider(
        value=0,
        min=0,
        max=10,
        step=1,
        readout_format="+0",
        continuous_update=False,
        description="+d6s",
    )

    dmg_widget = widgets.IntSlider(
        value=1,
        min=1,
        max=10,
        step=1,
        continuous_update=False,
        description="DMG",
    )

    rof_widget = widgets.IntSlider(
        value=3,
        min=1,
        max=10,
        step=1,
        continuous_update=False,
        description="RoF",
    )

    dc_target_widget = widgets.IntSlider(
        value=10,
        min=1,
        max=30,
        step=1,
        continuous_update=False,
        description="DC target",
    )

    dc_mod_widget = widgets.IntSlider(
        value=0,
        min=-10,
        max=10,
        step=1,
        readout_format="+0",
        continuous_update=False,
        description="DC mods",
    )

    dc_pool_widget = widgets.IntSlider(
        value=0,
        min=0,
        max=10,
        step=1,
        readout_format="+0",
        continuous_update=False,
        description="+d6s",
    )

    arm_widget = widgets.IntSlider(
        value=0,
        min=0,
        max=10,
        step=1,
        continuous_update=False,
        description="Armor",
    )

    display(
        widgets.VBox(
            [
                contest_type_widget,
                widgets.HBox(
                    [
                        widgets.VBox(
                            [
                                th_mod_widget,
                                th_target_widget,
                                th_pool_widget,
                                dmg_widget,
                                rof_widget,
                            ],
                        ),
                        widgets.VBox(
                            [
                                dc_target_widget,
                                dc_mod_widget,
                                dc_pool_widget,
                                arm_widget,
                            ],
                        ),
                    ],
                ),
            ]
        ),
        widgets.interactive_output(
            _display,
            {
                "contest_type": contest_type_widget,
                "th_target": th_target_widget,
                "th_mod": th_mod_widget,
                "th_pool": th_pool_widget,
                "dmg": dmg_widget,
                "rof": rof_widget,
                "dc_target": dc_target_widget,
                "dc_mod": dc_mod_widget,
                "dc_pool": dc_pool_widget,
                "arm": arm_widget,
            },
        ),
    )
