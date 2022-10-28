from enum import Enum

import pandas
from anydyce import HPlotterChooser
from doubles_on_2d6_plus_d import mechanic
from dyce import H
from IPython.display import display
from ipywidgets import widgets


class TargetType(str, Enum):
    TARGET = "Single"
    TARGET_RANGE = "w/ Extra"


class Die(str, Enum):
    D4 = "d4"
    D6 = "d6"
    D8 = "d8"
    D10 = "d10"
    D12 = "d12"
    D20 = "d20"


DIE_MAP = {
    Die.D4: H(4),
    Die.D6: H(6),
    Die.D8: H(8),
    Die.D10: H(10),
    Die.D12: H(12),
    Die.D20: H(20),
}


def showit():
    def _display(
        die: Die,
        target_type: TargetType,
        target: int,
        target_range: tuple[int, int],
        count_ones: bool,
    ) -> None:
        die_h = DIE_MAP[die]

        if target_type is TargetType.TARGET:
            base_target = target
            extra_target = None
        elif target_type is TargetType.TARGET_RANGE:
            base_target, extra_target = target_range
        else:
            assert False, f"unrecognized target type {target_type}"

        net_result = H(  # type: ignore
            (ours - theirs, count)  # type: ignore
            for (ours, theirs), count in mechanic(
                die_h, base_target, extra_target, count_ones
            ).items()
        )
        target_str = (
            f"{base_target}"
            if extra_target is None
            else f"{base_target}\nwith an extra win on {extra_target}"
        )

        if count_ones:
            target_str += "\ncounting each one against us"

        chooser.update_hs(
            (
                (
                    f"Net wins for 2d6 + {die_widget.label} vs. {target_str}\nMean: {net_result.mean():.2f}; Std Dev: {net_result.stdev():.2f}",
                    net_result,
                ),
            )
        )

        columns = ("Our Wins", "Their Wins", "Prob")
        df = pandas.DataFrame(columns=columns)
        result = mechanic(die_h, base_target, extra_target, count_ones)
        our_net_wins: int
        their_net_wins: int

        for (our_net_wins, their_net_wins), count in result.items():  # type: ignore
            row = pandas.DataFrame(
                ((our_net_wins, their_net_wins, count / result.total),),
                columns=columns,
                index=[f"2d6 + {die_widget.label}"],
            )
            df = pandas.concat((df, row))

        df = df.style.format({"Prob": "{:.2%}"})
        display(df)

    die_widget = widgets.Dropdown(
        value=Die.D20, options=[(die.value, die) for die in Die], description="2d6 + "
    )

    target_type_widget = widgets.Select(
        value=next(iter(TargetType)),
        options=[(method.value, method) for method in TargetType],
    )

    def _handle_target_type(change) -> None:
        single = change["new"] is TargetType.TARGET
        target_range_widget.disabled = single
        target_range_widget.layout.visibility = "hidden" if single else "visible"

    target_type_widget.observe(_handle_target_type, names="value")

    target_widget = widgets.IntSlider(
        value=11,
        min=1,
        max=20,
        step=1,
        continuous_update=False,
        description="",
        disabled=False,
    )

    target_range_widget = widgets.IntRangeSlider(
        value=(11, 15),
        min=1,
        max=20,
        step=1,
        continuous_update=False,
        description="",
        disabled=not target_widget.disabled,
    )

    count_ones_widget = widgets.Checkbox(
        value=False,
        description="Count Each One",
    )

    chooser = HPlotterChooser()

    display(
        widgets.VBox(
            [
                die_widget,
                widgets.HBox(
                    [
                        widgets.VBox(
                            [
                                target_type_widget,
                                count_ones_widget,
                            ],
                        ),
                        widgets.VBox(
                            [
                                target_widget,
                                target_range_widget,
                            ],
                        ),
                    ]
                ),
            ]
        )
    )

    chooser.interact()

    display(
        widgets.interactive_output(
            _display,
            {
                "die": die_widget,
                "target_type": target_type_widget,
                "target": target_widget,
                "target_range": target_range_widget,
                "count_ones": count_ones_widget,
            },
        )
    )
