from itertools import chain
from math import trunc
from typing import Iterator

import matplotlib.pyplot
from anydyce.viz import DEFAULT_BURST_ALPHA, DEFAULT_GRAPH_COLOR, plot_burst
from dyce import H
from IPython.display import display
from ipywidgets import widgets
from year_zero_and_a_half import (
    count_banes_with_push,
    count_successes,
    count_successes_with_push,
    dyz,
    dyz_legacy,
)


def showit():
    def _display(
        pool_size: int,
        round_halves: bool,
        burst_graph_color: str,
        alpha: float,
    ) -> None:
        successes = count_successes(pool=pool_size @ dyz)

        if round_halves:
            successes = H(
                (trunc(outcome) + 0.0 if outcome > 1 else outcome, count)  # type: ignore
                for outcome, count in successes.items()
            )

        successes_legacy = count_successes(pool=pool_size @ dyz_legacy)
        successes_empty = H(
            {outcome: 0 for outcome in chain(successes, successes_legacy)}
        )
        successes = successes.accumulate(successes_empty)
        successes_legacy = successes_legacy.accumulate(successes_empty)

        successes_with_push = count_successes_with_push(pool=pool_size @ dyz)

        if round_halves:
            successes_with_push = H(
                (trunc(outcome) + 0.0 if outcome > 1 else outcome, count)  # type: ignore
                for outcome, count in successes_with_push.items()
            )

        successes_with_push_legacy = count_successes_with_push(
            pool=pool_size @ dyz_legacy
        )
        successes_with_push_empty = H(
            {
                outcome: 0
                for outcome in chain(successes_with_push, successes_with_push_legacy)
            }
        )
        successes_with_push = successes_with_push.accumulate(successes_with_push_empty)
        successes_with_push_legacy = successes_with_push_legacy.accumulate(
            successes_with_push_empty
        )

        banes_with_push = count_banes_with_push(pool=pool_size @ dyz)
        banes_with_push_legacy = count_banes_with_push(pool=pool_size @ dyz_legacy)
        banes_with_push_empty = H(
            {outcome: 0 for outcome in chain(banes_with_push, banes_with_push_legacy)}
        )
        banes_with_push = banes_with_push.accumulate(banes_with_push_empty)
        banes_with_push_legacy = banes_with_push_legacy.accumulate(
            banes_with_push_empty
        )

        matplotlib.rcParams.update(matplotlib.rcParamsDefault)
        rows, columns = (1, 3)
        grid = (rows, columns)

        row, col = (0, 0)
        ax = matplotlib.pyplot.subplot2grid(grid, (row, col))
        plot_burst(
            ax,
            h_inner=successes,
            h_outer=successes_legacy,
            title="Succ. After First Roll",
            inner_color=burst_graph_color,
            alpha=alpha,
        )

        row, col = (0, 1)
        ax = matplotlib.pyplot.subplot2grid(grid, (row, col))
        plot_burst(
            ax,
            h_inner=successes_with_push,
            h_outer=successes_with_push_legacy,
            title="Succ. After Push",
            inner_color=burst_graph_color,
            alpha=alpha,
        )

        row, col = (0, 2)
        ax = matplotlib.pyplot.subplot2grid(grid, (row, col))
        plot_burst(
            ax,
            h_inner=banes_with_push,
            h_outer=banes_with_push_legacy,
            title="Banes After Push",
            inner_color=burst_graph_color[:-2]
            if burst_graph_color.endswith("_r")
            else burst_graph_color + "_r",  # use reverse color set for banes
            alpha=alpha,
        )

        matplotlib.pyplot.tight_layout()
        matplotlib.pyplot.show()

        display(
            widgets.HTML(
                """
The burst graphs above depict comparisons between aspects of the legacy Year Zero Engine mechanic and the half-success modification.
Outer graphs depict the legacy mechanic.
Inner graphs depict the modification.
Raw data is below.
"""
            )
        )

        display(
            widgets.HTML(
                "<table>"
                "<tr><th colspan=2>Successes After First Roll</th></tr>"
                "<tr><th>w/ Halves</th><th>Legacy</th></tr>"
                f"<tr><td><pre>{successes.format()}</pre></td><td><pre>{successes_legacy.format()}</pre></td></tr>"
                "<tr><th colspan=2>Successes After Push</th></tr>"
                "<tr><th>w/ Halves</th><th>Legacy</th></tr>"
                f"<tr><td><pre>{successes_with_push.format()}</pre></td><td><pre>{successes_with_push_legacy.format()}</pre></td></tr>"
                "<tr><th colspan=2>Banes After Push</th></tr>"
                "<tr><th>w/ Halves</th><th>Legacy</th></tr>"
                f"<tr><td><pre>{banes_with_push.format()}</pre></td><td><pre>{banes_with_push_legacy.format()}</pre></td></tr>"
                "</table>"
            )
        )

    pool_size_widget = widgets.IntSlider(
        value=4,
        min=1,
        max=10,
        step=1,
        continuous_update=False,
        description="Pool Size",
    )

    round_halves_widget = widgets.Checkbox(
        value=True,
        description="Round Half Successes",
    )

    def _color_names() -> Iterator[str]:
        color_names = set(matplotlib.cm.cmap_d.keys())

        for name in color_names:
            if name + "_r" in color_names:
                yield name
                yield name + "_r"

    burst_graph_color_widget = widgets.Dropdown(
        value=DEFAULT_GRAPH_COLOR,
        options=sorted(_color_names()),
        description="Graph Colors",
    )

    alpha_widget = widgets.FloatSlider(
        value=DEFAULT_BURST_ALPHA,
        min=0.0,
        max=1.0,
        step=0.1,
        continuous_update=False,
        description="Opacity",
    )

    display(
        widgets.VBox(
            [
                widgets.HBox([pool_size_widget, round_halves_widget]),
                widgets.HBox([burst_graph_color_widget, alpha_widget]),
            ]
        ),
        widgets.interactive_output(
            _display,
            {
                "pool_size": pool_size_widget,
                "round_halves": round_halves_widget,
                "burst_graph_color": burst_graph_color_widget,
                "alpha": alpha_widget,
            },
        ),
    )