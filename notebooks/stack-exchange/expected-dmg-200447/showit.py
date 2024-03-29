from typing import Callable

from anydyce import HPlotterChooser
from anydyce.viz import PlotWidgets
from dyce import H
from expected_damage import (
    TO_HIT_ADV,
    TO_HIT_DISADV,
    TO_HIT_NORMAL,
    crit_improved,
    crit_normal,
    crit_superior,
    expected_damage,
)
from IPython.display import display
from ipywidgets import widgets

TO_HIT_METHODS = {
    "Disadvantage": TO_HIT_DISADV,
    "Normal": TO_HIT_NORMAL,
    "Advantage": TO_HIT_ADV,
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
        if link_dmg and crit_dmg_dice_widget.value != norm_dmg_dice_widget.value:
            crit_dmg_dice_widget.value = norm_dmg_dice_widget.value

            return  # prevent double display

        norm_h = norm_dmg_dice + norm_dmg_mod
        crit_h = crit_dmg_dice + crit_dmg_mod

        expected_dmg_by_to_hit_method = {
            to_hit_name: expected_damage(
                expected_to_hit=crit_method(target, to_hit_method),
                normal_dmg=norm_h,
                extra_crit_dmg=crit_h,
            )
            for to_hit_name, to_hit_method in TO_HIT_METHODS.items()
        }

        chooser.update_hs(
            (f"{to_hit_name}\n(Mean: {expected_dmg.mean():.3})", expected_dmg)
            for to_hit_name, expected_dmg in expected_dmg_by_to_hit_method.items()
        )

    norm_dmg_dice_widget = widgets.Dropdown(options=damage_dice, description="Norm Die")
    link_dmg_widget = widgets.Checkbox(value=True, description="Link")
    crit_dmg_dice_widget = widgets.Dropdown(
        options=damage_dice, description="Crit Die", disabled=link_dmg_widget.value
    )

    def _handle_link_dmg(change) -> None:
        crit_dmg_dice_widget.disabled = change["new"]

    link_dmg_widget.observe(_handle_link_dmg, names="value")

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

    plot_widgets = PlotWidgets(initial_burst_zero_fill_normalize=True)
    chooser = HPlotterChooser(plot_widgets=plot_widgets)

    display(
        widgets.VBox(
            [
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
            ]
        )
    )

    display(
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
        )
    )

    chooser.interact()
