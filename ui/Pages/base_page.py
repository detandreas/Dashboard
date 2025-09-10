from abc import ABC, abstractmethod
from dash import html
import logging

logger = logging.getLogger(__name__)

class BasePage(ABC):
    """Abstract base class for dashboard pages."""
    
    def __init__(self, ui_factory):
        self.ui_factory = ui_factory
        self.config = ui_factory.config
        self.colors = ui_factory.colors
    
    @abstractmethod
    def render(self) -> html.Div:
        """Render the page content."""
        pass
