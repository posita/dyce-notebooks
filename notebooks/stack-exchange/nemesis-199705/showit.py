import matplotlib
from anydyce.viz import plot_burst_subplot
from IPython.display import display
from ipywidgets import widgets
from nemesis import nemesis


def showit():
    def _display(
        our_yang_pool_size: int,
        our_yin_pool_size: int,
        our_trait: int,
        our_initial_chi: int,
        their_yang_pool_size: int,
        their_yin_pool_size: int,
        their_trait: int,
        their_initial_chi: int,
    ) -> None:
        expected_outcome = nemesis(
            our_yang_pool_size,
            our_yin_pool_size,
            our_trait,
            our_initial_chi,
            their_yang_pool_size,
            their_yin_pool_size,
            their_trait,
            their_initial_chi,
        )
        plot_burst_subplot(
            expected_outcome,
            alpha=0.5,
            title="Expected Outcome for Player",
        )
        matplotlib.pyplot.show()

    our_yang_pool_size_widget = widgets.IntSlider(
        value=4,
        min=0,
        max=10,
        step=1,
        continuous_update=False,
        description="Yang Pool",
    )

    our_yin_pool_size_widget = widgets.IntSlider(
        value=1,
        min=0,
        max=10,
        step=1,
        continuous_update=False,
        description="Yin Pool",
    )

    our_trait_widget = widgets.IntSlider(
        value=2,
        min=0,
        max=5,
        step=1,
        continuous_update=False,
        description="Trait",
    )

    our_initial_chi_widget = widgets.IntSlider(
        value=5,
        min=0,
        max=10,
        step=1,
        continuous_update=False,
        description="Starting Chi",
    )

    their_yang_pool_size_widget = widgets.IntSlider(
        value=4,
        min=0,
        max=10,
        step=1,
        continuous_update=False,
        description="Yang Pool",
    )

    their_yin_pool_size_widget = widgets.IntSlider(
        value=1,
        min=0,
        max=10,
        step=1,
        continuous_update=False,
        description="Yin Pool",
    )

    their_trait_widget = widgets.IntSlider(
        value=2,
        min=0,
        max=5,
        step=1,
        continuous_update=False,
        description="Trait",
    )

    their_initial_chi_widget = widgets.IntSlider(
        value=5,
        min=0,
        max=10,
        step=1,
        continuous_update=False,
        description="Starting Chi",
    )

    display(
        widgets.HBox(
            [
                widgets.VBox(
                    [
                        widgets.HTML("<b>Player</b>"),
                        our_yang_pool_size_widget,
                        our_yin_pool_size_widget,
                        our_trait_widget,
                        our_initial_chi_widget,
                    ],
                ),
                widgets.VBox(
                    [
                        widgets.HTML("<b>Nemesis</b>"),
                        their_yang_pool_size_widget,
                        their_yin_pool_size_widget,
                        their_trait_widget,
                        their_initial_chi_widget,
                    ],
                ),
            ]
        ),
        widgets.interactive_output(
            _display,
            {
                "our_yang_pool_size": our_yang_pool_size_widget,
                "our_yin_pool_size": our_yin_pool_size_widget,
                "our_trait": our_trait_widget,
                "our_initial_chi": our_initial_chi_widget,
                "their_yang_pool_size": their_yang_pool_size_widget,
                "their_yin_pool_size": their_yin_pool_size_widget,
                "their_trait": their_trait_widget,
                "their_initial_chi": their_initial_chi_widget,
            },
        ),
    )
