from dash import html
import plotly.graph_objects as go
import logging

from ui.Pages.base_page import BasePage
from models.portfolio import PortfolioSnapshot
from services.portfolio_service import PortfolioService
from ui.Components import UIComponentFactory

logger = logging.getLogger(__name__)

class PortfolioPage(BasePage):
    """Portfolio overview page."""
    
    def __init__(self, portfolio_service: PortfolioService, ui_factory: UIComponentFactory):
        super().__init__(ui_factory)
        self.portfolio_service = portfolio_service
    
    
    def render(self) -> html.Div:
        """Render portfolio overview."""
        try:
            portfolio = self.portfolio_service.get_portfolio_snapshot()
            
            sections = [
                # Portfolio composition pie chart
                self.ui_factory.create_portfolio_composition(portfolio),
                
                # Portfolio profit chart with current profit/loss above
                self._create_profit_section(portfolio),
                
                # Portfolio yield chart
                self._create_yield_section(portfolio)
            ]
            
            return html.Div(sections)
            
        except Exception as e:
            logger.error(f"Error rendering portfolio page: {e}")
            return self._create_error_message(str(e))
    
    def _create_profit_section(self, portfolio: PortfolioSnapshot) -> html.Div:
        """Create profit analysis section with metrics above the chart."""
        profit_chart = self.ui_factory.create_profit_chart(
            portfolio.tickers, 
            "Portfolio Profit History"
        )
        
        # Add extrema information - use proper profit series calculation
        total_profit = portfolio.total_profit_series
        if len(total_profit) > 0 and len(portfolio.tickers) > 0:
            # Get dates from the first ticker that has price history
            dates = None
            for ticker in portfolio.tickers:
                if ticker.has_trades and len(ticker.price_history) > 0:
                    dates = ticker.price_history.index
                    break
            
            if dates is not None and len(dates) == len(total_profit):
                (max_profit, max_date), (min_profit, min_date) = \
                    self.ui_factory.calculator.find_extrema(total_profit, dates)
                
                # Current profit/loss values
                current_profit = portfolio.total_metrics.profit_absolute
                current_return = portfolio.total_metrics.return_percentage
                profit_color = self.colors["green"] if current_profit >= 0 else self.colors["red"]
                
                # Metrics above chart: Maximum Profit, Minimum Profit, Current P&L
                profit_metrics = html.Div([
                    self.ui_factory.create_metric_card(
                        "Maximum Profit",
                        f"${max_profit:.2f}",
                        self.colors["green"],
                        f"on {max_date.strftime('%d %b %Y')}"
                    ),
                    self.ui_factory.create_metric_card(
                        "Minimum Profit",
                        f"${min_profit:.2f}",
                        self.colors["red"],
                        f"on {min_date.strftime('%d %b %Y')}"
                    ),
                    self.ui_factory.create_metric_card(
                        "Current P&L",
                        f"${current_profit:.2f}",
                        profit_color,
                        f"Return: {current_return:.2f}%"
                    )
                ], style={
                    "display": "flex",
                    "justifyContent": "center",
                    "flexWrap": "wrap",
                    "marginBottom": "20px"
                })
            else:
                profit_metrics = html.Div([
                    html.P("Unable to calculate profit metrics - date mismatch", style={
                        "textAlign": "center",
                        "color": self.colors["text_secondary"]
                    })
                ])
        else:
            profit_metrics = html.Div([
                html.P("No profit data available", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ])
        
        return html.Div([
            profit_metrics,
            self.ui_factory.create_chart_container(profit_chart)
        ])
    
    def _create_yield_section(self, portfolio: PortfolioSnapshot) -> html.Div:
        """Create yield analysis section."""
        yield_series = portfolio.portfolio_yield_series
        
        if len(yield_series) == 0:
            return html.Div([
                html.H4("Portfolio Yield", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                }),
                html.P("No yield data available", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ])
        
        # Get dates from equity tickers that have price history
        dates = None
        for ticker in portfolio.equity_tickers:
            if ticker.has_trades and len(ticker.price_history) > 0:
                dates = ticker.price_history.index
                break
        
        # Fallback to any ticker with price history
        if dates is None:
            for ticker in portfolio.tickers:
                if ticker.has_trades and len(ticker.price_history) > 0:
                    dates = ticker.price_history.index
                    break
        
        if dates is None or len(dates) != len(yield_series):
            return html.Div([
                html.H4("Portfolio Yield", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                }),
                html.P("Unable to calculate yield - insufficient data", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ])
        
        (max_yield, max_date), (min_yield, min_date) = \
            self.ui_factory.calculator.find_extrema(yield_series, dates)
        
        # Create yield chart
        fig = go.Figure([
            go.Scatter(
                x=dates,
                y=yield_series,
                name="Portfolio Yield",
                line=dict(width=3, color=self.colors["accent"]),
                hovertemplate='<b>Portfolio Yield</b><br>' +
                             'Date: %{x|%d %b %Y}<br>' +
                             'Yield: %{y:.2f}%<extra></extra>'
            ),
            go.Scatter(
                x=[max_date], y=[max_yield],
                mode="markers", name="Maximum Yield",
                marker=dict(size=14, color=self.colors["green"]),
                hovertemplate='<b>Maximum Yield</b><br>' +
                             'Date: %{x|%d %b %Y}<br>' +
                             'Yield: %{y:.2f}%<extra></extra>'
            ),
            go.Scatter(
                x=[min_date], y=[min_yield],
                mode="markers", name="Minimum Yield",
                marker=dict(size=14, color=self.colors["red"]),
                hovertemplate='<b>Minimum Yield</b><br>' +
                             'Date: %{x|%d %b %Y}<br>' +
                             'Yield: %{y:.2f}%<extra></extra>'
            )
        ])
        
        # Add zero line
        fig.add_shape(
            type="line",
            x0=dates[0], x1=dates[-1],
            y0=0, y1=0,
            line=dict(color="white", width=1, dash="dot")
        )
        
        fig.update_layout(
            height=500,
            template="plotly_dark",
            title={
                "text": "Portfolio Yield Percentage",
                "font": {"size": 20, "color": self.colors["text_primary"]},
                "y": 0.95, "x": 0.5, "xanchor": "center", "yanchor": "top"
            },
            xaxis_title="Date",
            yaxis_title="Yield (%)",
            legend={
                "orientation": "h",
                "yanchor": "bottom", "y": 1.02,
                "xanchor": "center", "x": 0.5
            },
            yaxis=dict(
                dtick=self.config.market.portfolio_yield_tick,
                showgrid=True, gridcolor=self.colors["grid"]
            ),
            xaxis=dict(showgrid=True, gridcolor=self.colors["grid"]),
            plot_bgcolor=self.colors["card_bg"],
            paper_bgcolor=self.colors["card_bg"],
            font=dict(color=self.colors["text_primary"]),
            hovermode="x unified"
        )
        
        # Yield summary cards
        yield_cards = html.Div([
            self.ui_factory.create_metric_card(
                "Maximum Yield",
                f"{max_yield:.2f}%",
                self.colors["green"],
                f"on {max_date.strftime('%d %b %Y')}"
            ),
            self.ui_factory.create_metric_card(
                "Minimum Yield",
                f"{min_yield:.2f}%",
                self.colors["red"],
                f"on {min_date.strftime('%d %b %Y')}"
            ),
            self.ui_factory.create_metric_card(
                "Current Yield",
                f"{yield_series[-1]:.2f}%",
                self.colors["green"] if yield_series[-1] >= 0 else self.colors["red"]
            )
        ], style={
            "display": "flex",
            "justifyContent": "center",
            "flexWrap": "wrap",
            "marginBottom": "20px"
        })
        
        return html.Div([
            yield_cards,
            self.ui_factory.create_chart_container(fig)
        ])
    
    def _create_error_message(self, error: str) -> html.Div:
        """Create error message display."""
        return html.Div([
            html.H3("Error Loading Portfolio", style={
                "color": self.colors["red"],
                "textAlign": "center"
            }),
            html.P(f"An error occurred: {error}", style={
                "textAlign": "center",
                "color": self.colors["text_secondary"]
            })
        ], style=self.config.ui.card_style)
