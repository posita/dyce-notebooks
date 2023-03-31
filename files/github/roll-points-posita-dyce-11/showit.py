from enum import Enum
from typing import Callable, Optional

from anydyce import HPlotterChooser
from dyce import H
from IPython.display import display
from ipywidgets import widgets

MechanicT = Callable[[int, int, int, Optional[H]], H]


class Die(str, Enum):
    D4 = "d4"
    D6 = "d6"
    D8 = "d8"
    D10 = "d10"
    D12 = "d12"
    D20 = "d20"
    D100 = "d100"


DIE_MAP = {
    Die.D4: H(4),
    Die.D6: H(6),
    Die.D8: H(8),
    Die.D10: H(10),
    Die.D12: H(12),
    Die.D20: H(20),
    Die.D100: H(100),
}

DEFAULT_DIE = Die.D20


def showit(mechanic: MechanicT):
    def _display(
        pool_size: int,
        roll_points: int,
        target: int,
        die: Die,
    ) -> None:
        expected_outcomes = mechanic(pool_size, roll_points, target, DIE_MAP[die])
        chooser.update_hs(
            (
                (
                    f"Expected outcomes\nmean: {expected_outcomes.mean():0.02f}\nstdev: {expected_outcomes.stdev():0.02f}",
                    expected_outcomes,
                ),
            )
        )

    pool_size_widget = widgets.BoundedIntText(
        value=5,
        min=1,
        max=20,
        step=1,
        description="Pool Size",
    )

    roll_points_widget = widgets.BoundedIntText(
        value=10,
        min=0,
        max=200,
        step=1,
        description="Roll Points",
    )

    target_widget = widgets.BoundedIntText(
        value=25,
        min=2,
        max=200,
        step=1,
        description="Target",
    )

    die_widget = widgets.Dropdown(
        value=DEFAULT_DIE,
        options=[(die.value, die) for die in Die],
        description="Die",
    )

    chooser = HPlotterChooser()

    display(
        widgets.VBox(
            [
                pool_size_widget,
                roll_points_widget,
                target_widget,
                die_widget,
            ]
        ),
        widgets.interactive_output(
            _display,
            {
                "pool_size": pool_size_widget,
                "roll_points": roll_points_widget,
                "target": target_widget,
                "die": die_widget,
            },
        ),
    )

    chooser.interact()
