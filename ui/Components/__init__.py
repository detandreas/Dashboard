"""UI component factory composed from modular mixins."""

from services.calculation_service import StandardCalculationService
from config.settings import Config

from .cards import CardComponentsMixin
from .charts import ChartComponentsMixin
from .layout import LayoutComponentsMixin
from .portfolio_com import PortfolioComponentsMixin


class UIComponentFactory(
    CardComponentsMixin,
    ChartComponentsMixin,
    LayoutComponentsMixin,
    PortfolioComponentsMixin,
):
    """Factory for creating reusable UI components."""

    def __init__(self, config: Config):
        self.config = config
        self.colors = config.ui.colors
        self.card_style = config.ui.card_style.copy()
        self.calculator = StandardCalculationService()


__all__ = ["UIComponentFactory"]
