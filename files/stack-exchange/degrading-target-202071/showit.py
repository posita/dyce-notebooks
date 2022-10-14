from enum import Enum

import matplotlib.pyplot
from anydyce.viz import plot_burst_subplot
from degrading_target import (
    degrading_target_customizable_adjustment,
    reduce_once_per_try,
    reduce_twice_per_try,
)
from dyce import H
from IPython.display import display
from ipywidgets import widgets


class Die(str, Enum):
    D4 = "d4"
    D6 = "d6"
    D8 = "d8"
    D10 = "d10"
    D12 = "d12"
    D20 = "d20"
    CUSTOM = "Custom"


DIE_MAP = {
    Die.D4: H(4),
    Die.D6: H(6),
    Die.D8: H(8),
    Die.D10: H(10),
    Die.D12: H(12),
    Die.D20: H(20),
}


class AdjMethod(str, Enum):
    REDUCE_ONCE_PER_TRY = "Reduce Target Once Per Try"
    REDUCE_TWICE_PER_TRY = "Reduce Target Twice Per Try"
    CUSTOM = "Custom"


ADJ_METHOD_MAP = {
    AdjMethod.REDUCE_ONCE_PER_TRY: reduce_once_per_try,
    AdjMethod.REDUCE_TWICE_PER_TRY: reduce_twice_per_try,
}

DEFAULT_DIE = Die.D20
DEFAULT_ADJ_METHOD = AdjMethod.REDUCE_ONCE_PER_TRY


def showit():
    last_die_enum = DEFAULT_DIE

    def _display(
        die: str,
        die_custom: str,
        initial_target: int,
        adj_method: str,
        adj_method_custom: str,
    ) -> None:
        nonlocal last_die_enum
        needs_refresh = False
        die_enum = Die(die)
        adj_method_enum = AdjMethod(adj_method)

        if die_enum in DIE_MAP:
            die_h = DIE_MAP[die_enum]
        else:
            assert die_enum is Die.CUSTOM
            die_h = H(eval(die_custom, {"H": H}))

        if die_enum != last_die_enum:
            last_die_enum = die_enum
            initial_target_widget.value = max(die_h)
            needs_refresh = True

        if needs_refresh:
            return

        if die_custom_widget.disabled != (die_enum is not Die.CUSTOM):
            die_custom_widget.disabled = die_enum is not Die.CUSTOM

        if adj_method_custom_widget.disabled != (
            adj_method_enum is not AdjMethod.CUSTOM
        ):
            adj_method_custom_widget.disabled = adj_method_enum is not AdjMethod.CUSTOM

        if adj_method_enum in ADJ_METHOD_MAP:
            adj_method_func = ADJ_METHOD_MAP[adj_method_enum]
        else:
            assert adj_method_enum is AdjMethod.CUSTOM
            adj_method_globals = {"H": H, "_": ADJ_METHOD_MAP[DEFAULT_ADJ_METHOD]}

            try:
                adj_method_func = eval(adj_method_custom, adj_method_globals)
            except SyntaxError:
                exec(adj_method_custom, adj_method_globals)
                del adj_method_globals["_"]
                adj_method_func = adj_method_globals["_"]  # type: ignore

        breakdown = degrading_target_customizable_adjustment(
            die_h, initial_target, adj_method_func
        )

        plot_burst_subplot(
            breakdown,
            alpha=0.5,
            title=f"Distribution of Number of Tries to Reach Success\nmean: {breakdown.mean():0.02f}\nstdev: {breakdown.stdev():0.02f}",
        )

        matplotlib.pyplot.show()

    die_widget = widgets.Dropdown(
        value=last_die_enum,
        options=[die.value for die in Die],
        description="Die",
    )

    die_custom_widget = widgets.Text(
        value="2 @ H(6)  # <-- this means 2d6",
        description="Custom",
        disabled=die_widget.value is not Die.CUSTOM,
    )

    initial_target_widget = widgets.BoundedIntText(
        value=max(DIE_MAP[last_die_enum]),
        min=min(DIE_MAP[last_die_enum]),
        step=1,
        continuous_update=False,
        description="Initial Target",
    )

    adj_method_widget = widgets.Dropdown(
        value=DEFAULT_ADJ_METHOD,
        options=[method.value for method in AdjMethod],
        description="Adj. Method",
    )

    adj_method_custom_widget = widgets.Textarea(
        value="lambda target, tries: target - (tries - 1) // 2",
        description="Custom",
        disabled=adj_method_widget.value is not AdjMethod.CUSTOM,
        height="auto",
        width="auto",
    )

    display(
        widgets.VBox(
            [
                widgets.HBox([die_widget, die_custom_widget]),
                initial_target_widget,
                widgets.HBox([adj_method_widget, adj_method_custom_widget]),
            ]
        ),
        widgets.interactive_output(
            _display,
            {
                "die": die_widget,
                "die_custom": die_custom_widget,
                "initial_target": initial_target_widget,
                "adj_method": adj_method_widget,
                "adj_method_custom": adj_method_custom_widget,
            },
        ),
    )
