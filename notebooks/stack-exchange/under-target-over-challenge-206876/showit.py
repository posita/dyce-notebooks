from typing import Callable, cast

from anydyce import HPlotterChooser
from anydyce.viz import PlotWidgets
from dyce import H
from IPython.display import display
from ipywidgets import widgets


def showit(
    player_dice: dict[str, H],
    challenge_dice: dict[str, H],
    expected_result: Callable[[H, H, int], H],
):
    def _display(
        selected_player_dice: list[str],
        selected_challenge_dice: list[str],
        target_range: tuple[int, int],
    ) -> None:
        lo, hi = target_range
        chooser.update_hs(
            (
                (
                    f"{player_die} vs. {target} w/ {challenge_die}",
                    expected_result(
                        player_dice[player_die], challenge_dice[challenge_die], target
                    ),
                )
                for player_die in selected_player_dice
                for target in range(lo, hi + 1)
                for challenge_die in selected_challenge_dice
            ),
        )

    player_dice_keys = list(player_dice.keys())
    player_dice_widget = widgets.SelectMultiple(
        options=player_dice_keys,
        value=player_dice_keys[:2],
        description="Player Dice",
    )
    challenge_dice_keys = list(challenge_dice.keys())
    challenge_dice_widget = widgets.SelectMultiple(
        options=challenge_dice_keys,
        value=challenge_dice_keys[:3],
        description="Challenge Dice",
    )

    min_target = cast(int, min(min(player_die) for player_die in player_dice.values()))
    max_target = cast(
        int, max(max(player_die) for player_die in player_dice.values()) + 1
    )
    targets = list(range(min_target, max_target + 1))
    target_range_widget = widgets.IntRangeSlider(
        value=(
            max(targets[len(targets) // 2 - 1], min_target),
            min(targets[len(targets) // 2 + 1], max_target),
        ),
        min=min_target,
        max=max_target,
        step=1,
        continuous_update=False,
        description="Target(s)",
    )

    chooser = HPlotterChooser(
        plot_widgets=PlotWidgets(
            initial_burst_cmap_inner="Set2",
            initial_burst_zero_fill_normalize=True,
        )
    )

    display(
        widgets.HBox([player_dice_widget, target_range_widget, challenge_dice_widget]),
        widgets.interactive_output(
            _display,
            {
                "selected_player_dice": player_dice_widget,
                "selected_challenge_dice": challenge_dice_widget,
                "target_range": target_range_widget,
            },
        ),
    )

    chooser.interact()
