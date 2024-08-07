from enum import Enum
from typing import Optional

from anydyce import HPlotterChooser
from degrading_target import (
    AdjustedTargetT,
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
    D100 = "d100"
    CUSTOM = "Custom Die"


DIE_MAP = {
    Die.D4: H(4),
    Die.D6: H(6),
    Die.D8: H(8),
    Die.D10: H(10),
    Die.D12: H(12),
    Die.D20: H(20),
    Die.D100: H(100),
}


class AdjMethod(str, Enum):
    REDUCE_ONCE_PER_TRY = "Reduce Target Once Per Try"
    REDUCE_TWICE_PER_TRY = "Reduce Target Twice Per Try"
    CUSTOM = "Custom Implementation"


ADJ_METHOD_MAP: dict[AdjMethod, AdjustedTargetT] = {
    AdjMethod.REDUCE_ONCE_PER_TRY: reduce_once_per_try,
    AdjMethod.REDUCE_TWICE_PER_TRY: reduce_twice_per_try,
}

DEFAULT_DIE = Die.D20
DEFAULT_ADJ_METHOD = AdjMethod.REDUCE_ONCE_PER_TRY


def showit():
    last_die_enum = DEFAULT_DIE

    def _display(
        die: Die,
        die_custom: str,
        initial_target: int,
        adj_method: AdjMethod,
        adj_method_custom: str,
    ) -> None:
        nonlocal last_die_enum
        die_exc: Optional[Exception] = None
        adj_method_exc: Optional[Exception] = None
        needs_refresh = False

        if die in DIE_MAP:
            die_h = DIE_MAP[die]
        else:
            assert die is Die.CUSTOM

            die_h, die_exc = _grab_die_custom(die_custom)

            if die_exc:
                die_custom_widget.add_class("parse-error")
            else:
                die_custom_widget.remove_class("parse-error")

        if die != last_die_enum:
            last_die_enum = die
            initial_target_widget.value = max(die_h)
            needs_refresh = True

        if needs_refresh:
            return

        if adj_method in ADJ_METHOD_MAP:
            adj_method_func = ADJ_METHOD_MAP[adj_method]
        else:
            assert adj_method is AdjMethod.CUSTOM
            adj_method_func, adj_method_exc = _grab_adj_method_custom(adj_method_custom)

            if adj_method_exc:
                adj_method_custom_widget.add_class("parse-error")
            else:
                adj_method_custom_widget.remove_class("parse-error")

        breakdown = H(0)

        if die_exc:
            msg = f"Error {die_exc}"
        elif adj_method_exc:
            msg = f"Error {adj_method_exc}"
        else:
            try:
                breakdown = degrading_target_customizable_adjustment(
                    die_h, initial_target, adj_method_func
                )
                msg = f"Distribution of tries needed to reach success\nMean: {breakdown.mean():0.2f}; Std Dev: {breakdown.stdev():0.2f}"
            except Exception as exc:
                die_custom_widget.add_class("parse-error")
                adj_method_custom_widget.add_class("parse-error")
                msg = f"Error {exc}"

        chooser.update_hs([(msg, breakdown)])

    die_widget = widgets.Dropdown(
        value=last_die_enum,
        options=[(die.value, die) for die in Die],
        description="Die",
    )

    die_custom_widget = widgets.Text(
        value="2 @ H(6)  # <-- this means 2d6",
        description="Value",
        disabled=die_widget.value is not Die.CUSTOM,
        layout={
            "visibility": "hidden" if die_widget.value is not Die.CUSTOM else "visible"
        },
    )

    die_custom_widget.add_class("code-input")

    def _handle_die(change) -> None:
        custom = change["new"] is Die.CUSTOM
        die_custom_widget.disabled = not custom
        die_custom_widget.layout.visibility = "visible" if custom else "hidden"

    die_widget.observe(_handle_die, names="value")

    initial_target_widget = widgets.BoundedIntText(
        value=max(DIE_MAP[last_die_enum]),
        min=min(DIE_MAP[last_die_enum]),
        step=1,
        continuous_update=False,
        description="Initial Target",
    )

    adj_method_widget = widgets.Dropdown(
        value=DEFAULT_ADJ_METHOD,
        options=[(method.value, method) for method in AdjMethod],
        description="Adj. Method",
    )

    adj_method_custom_widget = widgets.Textarea(
        value="lambda target, prior_tries: target - prior_tries // 2",
        description="Value",
        disabled=adj_method_widget.value is not AdjMethod.CUSTOM,
        layout={
            "visibility": "hidden"
            if adj_method_widget.value is not AdjMethod.CUSTOM
            else "visible"
        },
        height="auto",
        width="auto",
    )

    adj_method_custom_widget.add_class("code-input")

    def _handle_adj_method(change) -> None:
        custom = change["new"] is AdjMethod.CUSTOM
        adj_method_custom_widget.disabled = not custom
        adj_method_custom_widget.layout.visibility = "visible" if custom else "hidden"

    adj_method_widget.observe(_handle_adj_method, names="value")

    chooser = HPlotterChooser()

    display(
        widgets.VBox(
            [
                widgets.HTML(
                    "<style>.code-input input[type=text], .code-input textarea { font-family: monospace; }</style>"
                    "<style>.parse-error input[type=text], .parse-error textarea { color: #f33; font-weight: bold; }</style>"
                ),
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

    chooser.interact()


def _grab_adj_method_custom(
    value: str,
) -> tuple[AdjustedTargetT, Optional[Exception]]:
    adj_method_globals = {"H": H, "_": ADJ_METHOD_MAP[DEFAULT_ADJ_METHOD]}

    try:
        try:
            adj_method_func = eval(value, adj_method_globals)
        except SyntaxError:
            del adj_method_globals["_"]
            exec(value, adj_method_globals)
            adj_method_func = adj_method_globals["_"]  # type: ignore

        return adj_method_func, None
    except Exception as exc:

        def adj_method_func(_: int, __: int) -> int:
            return 0

        return adj_method_func, exc


def _grab_die_custom(value: str) -> tuple[H, Optional[Exception]]:
    try:
        return H(eval(value, {"H": H})), None
    except Exception as exc:
        return H(0), exc
