from dash import html
import logging

from ui.base_page import BasePage
from models.portfolio import TickerData
from services.portfolio_service import PortfolioService
from ui.components import UIComponentFactory

logger = logging.getLogger(__name__)

class TickersPage(BasePage):
    """Individual ticker analysis page."""
    
    def __init__(self, portfolio_service: PortfolioService, ui_factory: UIComponentFactory):
        super().__init__(ui_factory)
        self.portfolio_service = portfolio_service
    
    def render(self) -> html.Div:
        """Render individual tickers analysis."""
        try:
            portfolio = self.portfolio_service.get_portfolio_snapshot()
            sections = []
            
            for ticker_data in portfolio.tickers:
                if not ticker_data.has_trades:
                    continue
                
                section = self._create_ticker_section(ticker_data)
                sections.append(section)
            
            if not sections:
                return self._create_no_data_message("No ticker data available")
            
            return html.Div(sections)
            
        except Exception as e:
            logger.error(f"Error rendering tickers page: {e}")
            return self._create_error_message(str(e))
    
    def _create_ticker_section(self, ticker_data: TickerData) -> html.Div:
        """Create a section for individual ticker."""
        return html.Div([
            html.H3(f"{ticker_data.symbol} Analysis", style={
                "textAlign": "center",
                "color": self.colors["accent"],
                "marginBottom": "20px"
            }),
            
            # Performance cards
            self.ui_factory.create_performance_cards(ticker_data.metrics),
            
            # Price chart
            self.ui_factory.create_chart_container(
                self.ui_factory.create_price_chart(ticker_data)
            )
        ], style={"marginBottom": "50px"})
    
    def _create_no_data_message(self, message: str) -> html.Div:
        """Create no data available message."""
        return html.Div([
            html.H3("No Data Available", style={
                "textAlign": "center",
                "color": self.colors["text_secondary"]
            }),
            html.P(message, style={
                "textAlign": "center",
                "color": self.colors["text_secondary"]
            })
        ], style=self.config.ui.card_style)
    
    def _create_error_message(self, error: str) -> html.Div:
        """Create error message display."""
        return html.Div([
            html.H3("Error Loading Tickers", style={
                "color": self.colors["red"],
                "textAlign": "center"
            }),
            html.P(f"An error occurred: {error}", style={
                "textAlign": "center",
                "color": self.colors["text_secondary"]
            })
        ], style=self.config.ui.card_style)
