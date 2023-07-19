from fractions import Fraction
from typing import Callable

from anydyce import HPlotterChooser
from anydyce.viz import PlotWidgets
from dyce import H
from dyce.evaluation import _LimitT
from dyce_impl import mechanic_dyce_fudged
from icepool_impl import mechanic_icepool, mechanic_icepool_fudged
from IPython.display import display
from ipywidgets import widgets

# Local imports
from params import Params

_MechanicImplementationT = Callable[[Params, H, _LimitT], H]

_IMPLEMENTATION_MAP: dict[str, _MechanicImplementationT] = {
    "dyce (explosions fudged within limit)": mechanic_dyce_fudged,
    "icepool (explosions fudged within limit)": mechanic_icepool_fudged,
    "icepool (explosions accurately limited)": mechanic_icepool,
}


def showit(
    notations: str,
    die_map: dict[str, H],
    selected_die: H | None = None,
):
    if selected_die is None:
        selected_die = next(iter(die_map.values()))

    def _display(
        mechanic_implementation: _MechanicImplementationT,
        die: H,
        explode_limit: _LimitT,
    ) -> None:
        chooser.update_hs(
            (
                (
                    f"{params.comment if params.comment else params!s}\nmean: {h.mean():0.02f}\nstdev: {h.stdev():0.02f}",
                    h,
                )
                for params, h in (
                    (
                        params,
                        mechanic_implementation(
                            params,
                            params.override_die if params.override_die else die,
                            explode_limit,
                        ),
                    )
                    for params in Params.parse_from_notation(notations, die_map)
                )
            ),
        )

    implementation_widget = widgets.Dropdown(
        value=mechanic_dyce_fudged,
        options=_IMPLEMENTATION_MAP,
        description="Implementation",
    )

    die_widget = widgets.Dropdown(
        value=selected_die,
        options=die_map,
        description="Default Die",
    )

    explode_limit_widget = widgets.SelectionSlider(
        value=Fraction(1, 10),
        options={
            "until ¹/₁₀₀₀₀": Fraction(1, 10_000),
            "until ¹/₁₀₀₀": Fraction(1, 1_000),
            "until ¹/₁₀₀": Fraction(1, 100),
            "until ¹/₁₀": Fraction(1, 10),
            "depth of 0": 0,
            "depth of 1": 1,
            "depth of 2": 2,
            "depth of 3": 3,
            "depth of 4": 4,
            "depth of 5": 5,
        },
        description="Exp. Limit",
        continuous_update=False,
        orientation="horizontal",
        readout=True,
    )

    chooser = HPlotterChooser(
        plot_widgets=PlotWidgets(
            initial_burst_zero_fill_normalize=True,
        )
    )

    display(
        widgets.HBox([implementation_widget, die_widget, explode_limit_widget]),
        widgets.interactive_output(
            _display,
            {
                "mechanic_implementation": implementation_widget,
                "die": die_widget,
                "explode_limit": explode_limit_widget,
            },
        ),
    )

    chooser.interact()
