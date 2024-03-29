from itertools import chain
from math import trunc

from anydyce import jupyter_visualize
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

        jupyter_visualize(
            [
                ("Succ. After First Roll", successes, successes_legacy),
                ("Succ. After Push", successes_with_push, successes_with_push_legacy),
                ("Banes After Push", banes_with_push, banes_with_push_legacy),
            ]
        )

        display(
            widgets.HTML(
                """
The burst graphs above depict comparisons between aspects of the legacy Year Zero Engine mechanic and the half-success modification.
Outer graphs depict the legacy mechanic.
Inner graphs depict the modification.
Bane counts are negative to signal that they work <em>against</em> the success mechanic.
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

    display(
        widgets.HBox([pool_size_widget, round_halves_widget]),
        widgets.interactive_output(
            _display,
            {
                "pool_size": pool_size_widget,
                "round_halves": round_halves_widget,
            },
        ),
    )
