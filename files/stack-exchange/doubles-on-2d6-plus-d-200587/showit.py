from enum import Enum, auto

import matplotlib.pyplot
import pandas
from anydyce.viz import plot_burst_subplot
from doubles_on_2d6_plus_d import mechanic
from dyce import H
from IPython.display import display
from ipywidgets import widgets


class TargetType(Enum):
    TARGET = auto()
    TARGET_RANGE = auto()


DICE: dict[str, H] = {
    "d4": H(4),
    "d6": H(6),
    "d8": H(8),
    "d10": H(10),
    "d12": H(12),
    "d20": H(20),
}


def showit():
    def _display(
        die: H,
        target_type: TargetType,
        target: int,
        target_range: tuple[int, int],
        count_ones: bool,
    ) -> None:
        if target_type is TargetType.TARGET:
            if target_widget.disabled:
                target_widget.disabled = False
                target_range_widget.disabled = True

            base_target = target
            extra_target = None
        elif target_type is TargetType.TARGET_RANGE:
            if target_range_widget.disabled:
                target_widget.disabled = True
                target_range_widget.disabled = False

            base_target, extra_target = target_range
        else:
            assert False, f"unrecognized target type {target_type}"

        net_result = H(  # type: ignore
            (ours - theirs, count)  # type: ignore
            for (ours, theirs), count in mechanic(
                die, base_target, extra_target, count_ones
            ).items()
        )
        target_str = (
            f"{base_target}"
            if extra_target is None
            else f"{base_target}\nwith an extra win on {extra_target}"
        )

        if count_ones:
            target_str += "\nand counting each one against us"

        plot_burst_subplot(
            net_result,
            alpha=0.5,
            title=f"Net wins for 2d6 + {die_widget.label} vs. {target_str}\nAvg: {net_result.mean():.2f}; Std Dev: {net_result.stdev():.2f}",
        )
        matplotlib.pyplot.show()

        columns = ("Our Wins", "Their Wins", "Prob")
        df = pandas.DataFrame(columns=columns)
        result = mechanic(die, base_target, extra_target, count_ones)
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

    die_widget = widgets.Dropdown(options=DICE, description="2d6 + ")

    target_type_widget = widgets.RadioButtons(
        value=TargetType.TARGET,
        options=(
            ("Single", TargetType.TARGET),
            ("w/ Extra", TargetType.TARGET_RANGE),
        ),
    )

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
        disabled=True,
    )

    count_ones_widget = widgets.Checkbox(
        value=False,
        description="Count Each One",
    )

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
        ),
        widgets.interactive_output(
            _display,
            {
                "die": die_widget,
                "target_type": target_type_widget,
                "target": target_widget,
                "target_range": target_range_widget,
                "count_ones": count_ones_widget,
            },
        ),
    )
