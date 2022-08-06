from typing import Callable

from anydyce import BreakoutType, jupyter_visualize
from dyce import H
from expected_damage import (
    bounds,
    crit_improved,
    crit_normal,
    crit_superior,
    expected_damage,
    to_hit_adv,
    to_hit_disadv,
    to_hit_normal,
)
from IPython.display import display
from ipywidgets import widgets

TO_HIT_METHODS = {
    "Disadvantage": to_hit_disadv,
    "Normal": to_hit_normal,
    "Advantage": to_hit_adv,
}


CRIT_METHODS = {
    "Normal": crit_normal,
    "Improved": crit_improved,
    "Superior": crit_superior,
    # Any others?
}


def showit(damage_dice: dict[str, H]):
    def _display(
        norm_dmg_dice: H,
        norm_dmg_mod: int,
        crit_dmg_dice: H,
        crit_dmg_mod: int,
        link_dmg: bool,
        target: int,
        crit_method: Callable[[int, H], H],
    ) -> None:
        crit_dmg_dice_widget.disabled = link_dmg

        if link_dmg and crit_dmg_dice_widget.value != norm_dmg_dice_widget.value:
            crit_dmg_dice_widget.value = norm_dmg_dice_widget.value

            return  # prevent double display

        norm_h = bounds(norm_dmg_dice + norm_dmg_mod, min_outcome=1)
        crit_h = bounds(crit_dmg_dice + crit_dmg_mod, min_outcome=1)
        expected_dmg_by_to_hit_method = {
            to_hit_name: expected_damage(
                target=target,
                to_hit=to_hit_h,
                attack_func=crit_method,
                normal_dmg=norm_h,
                extra_crit_dmg=crit_h,
            )
            for to_hit_name, to_hit_h in TO_HIT_METHODS.items()
        }

        jupyter_visualize(
            [
                (f"{to_hit_name}\n(Mean: {expected_dmg.mean():.3})", expected_dmg)
                for to_hit_name, expected_dmg in expected_dmg_by_to_hit_method.items()
            ],
            default_breakout_type=BreakoutType.BURST,
        )

    norm_dmg_dice_widget = widgets.Dropdown(options=damage_dice, description="Norm Die")
    crit_dmg_dice_widget = widgets.Dropdown(options=damage_dice, description="Crit Die")
    link_dmg_widget = widgets.Checkbox(value=True, description="Link")

    norm_dmg_mod_widget = widgets.IntSlider(
        value=0,
        min=-10,
        max=+10,
        step=1,
        continuous_update=False,
        description="Norm Mod",
    )

    crit_dmg_mod_widget = widgets.IntSlider(
        value=0,
        min=-10,
        max=+10,
        step=1,
        continuous_update=False,
        description="Crit Mod",
    )

    target_widget = widgets.IntSlider(
        value=10,
        min=2,
        max=20,
        step=1,
        continuous_update=False,
        description="Target",
    )

    crit_method_widget = widgets.Dropdown(
        options=CRIT_METHODS, description="Crit Method"
    )

    display(
        widgets.VBox(
            [
                widgets.HTML(value="<h1>Mechanic</h1>"),
                target_widget,
                widgets.HBox(
                    [
                        norm_dmg_dice_widget,
                        crit_dmg_dice_widget,
                        link_dmg_widget,
                    ],
                ),
                widgets.HBox(
                    [
                        norm_dmg_mod_widget,
                        crit_dmg_mod_widget,
                    ],
                ),
                crit_method_widget,
                widgets.HTML(value="<h1>Visualization</h1>"),
            ]
        ),
        widgets.interactive_output(
            _display,
            {
                "norm_dmg_dice": norm_dmg_dice_widget,
                "norm_dmg_mod": norm_dmg_mod_widget,
                "crit_dmg_dice": crit_dmg_dice_widget,
                "crit_dmg_mod": crit_dmg_mod_widget,
                "link_dmg": link_dmg_widget,
                "target": target_widget,
                "crit_method": crit_method_widget,
            },
        ),
    )
