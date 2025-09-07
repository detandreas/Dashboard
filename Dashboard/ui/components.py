from dash import html, dcc
import plotly.graph_objects as go
from typing import Optional, List
import logging

from models.portfolio import TickerData, PerformanceMetrics
from services.calculation_service import StandardCalculationService
from config.settings import Config

logger = logging.getLogger(__name__)

class UIComponentFactory:
    """Factory for creating reusable UI components."""
    
    def __init__(self, config: Config):
        self.config = config
        self.colors = config.ui.colors
        self.card_style = config.ui.card_style.copy()
        self.calculator = StandardCalculationService()
    
    def create_metric_card(self, title: str, value: str, 
                          value_color: Optional[str] = None, 
                          subtitle: Optional[str] = None) -> html.Div:
        """Create a standardized metric card."""
        text_color = value_color or self.colors["text_primary"]
        
        content = [
            html.H6(title, style={
                "color": self.colors["text_secondary"],
                "marginBottom": "10px",
                "fontSize": "0.9rem"
            }),
            html.H4(value, style={
                "margin": "0",
                "color": text_color,
                "fontWeight": "bold"
            })
        ]
        
        if subtitle:
            content.append(
                html.P(subtitle, style={
                    "margin": "5px 0 0 0",
                    "color": self.colors["text_secondary"],
                    "fontSize": "0.8rem"
                })
            )
        
        return html.Div(content, style=self.card_style)
    
    def create_performance_cards(self, metrics: PerformanceMetrics, 
                               show_entry_price: bool = True) -> html.Div:
        """Create performance metric cards with invested amount."""
        profit_color = self.colors["green"] if metrics.is_profitable else self.colors["red"]
        return_color = self.colors["green"] if metrics.return_percentage >= 0 else self.colors["red"]
        
        cards = []
        
        # Always show invested amount
        cards.append(
            self.create_metric_card("Invested", f"${metrics.invested:.2f}")
        )
        
        if show_entry_price and metrics.average_buy_price > 0:
            cards.append(
                self.create_metric_card(
                    "Average Entry Price", 
                    f"${metrics.average_buy_price:.2f}"
                )
            )
        
        cards.extend([
            self.create_metric_card(
                "Current Value", 
                f"${metrics.current_value:.2f}", 
                self.colors["accent"]
            ),
            self.create_metric_card(
                "Profit/Loss", 
                f"${metrics.profit_absolute:.2f}", 
                profit_color
            ),
            self.create_metric_card(
                "Return", 
                f"{metrics.return_percentage:.2f}%", 
                return_color
            )
        ])
        
        return html.Div(cards, style={
            "display": "flex",
            "justifyContent": "center",
            "flexWrap": "wrap",
            "marginBottom": "20px"
        })
    
    def create_price_chart(self, ticker_data: TickerData) -> go.Figure:
        """Create interactive price chart with DCA and buy signals."""
        try:
            fig = go.Figure()
            
            # Add close price line
            fig.add_trace(go.Scatter(
                x=ticker_data.price_history.index,
                y=ticker_data.price_history["Close"],
                name="Close Price",
                line=dict(width=3, color=self.colors["accent"]),
                hovertemplate='<b>Close Price</b><br>' +
                             'Date: %{x|%d %b %Y}<br>' +
                             'Price: $%{y:.2f}<extra></extra>'
            ))
            
            # Add DCA line if available
            if ticker_data.has_trades:
                fig.add_trace(go.Scatter(
                    x=ticker_data.price_history.index,
                    y=ticker_data.dca_history,
                    name="DCA Price",
                    line=dict(width=2, dash="dash", color=self.colors["green"]),
                    hovertemplate='<b>Dollar Cost Average</b><br>' +
                                 'Date: %{x|%d %b %Y}<br>' +
                                 'DCA: $%{y:.2f}<extra></extra>'
                ))
                
                # Add buy signals
                fig.add_trace(go.Scatter(
                    x=ticker_data.buy_dates,
                    y=ticker_data.buy_prices,
                    mode="markers",
                    name="Buy Orders",
                    marker=dict(size=12, color=self.colors["red"], symbol="triangle-up"),
                    hovertemplate='<b>Buy Order</b><br>' +
                                 'Date: %{x|%d %b %Y}<br>' +
                                 'Price: $%{y:.2f}<extra></extra>'
                ))
            
            # Configure layout
            dtick = self.config.market.y_axis_ticks.get(ticker_data.symbol)
            
            fig.update_layout(
                height=500,
                template="plotly_dark",
                title={
                    "text": f"{ticker_data.symbol} Performance Analysis",
                    "font": {"size": 20, "color": self.colors["text_primary"]},
                    "y": 0.95, "x": 0.5, "xanchor": "center", "yanchor": "top"
                },
                xaxis_title="Date",
                yaxis_title="Price ($)",
                legend={
                    "orientation": "h",
                    "yanchor": "bottom", "y": 1.02,
                    "xanchor": "center", "x": 0.5
                },
                yaxis=dict(
                    dtick=dtick,
                    showgrid=True, gridcolor=self.colors["grid"],
                    zeroline=True, zerolinecolor=self.colors["text_secondary"]
                ),
                xaxis=dict(showgrid=True, gridcolor=self.colors["grid"]),
                plot_bgcolor=self.colors["card_bg"],
                paper_bgcolor=self.colors["card_bg"],
                font=dict(color=self.colors["text_primary"]),
                hovermode="x unified",
                margin=dict(l=60, r=40, t=80, b=60)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating price chart for {ticker_data.symbol}: {e}")
            # Return empty figure on error
            return go.Figure().update_layout(
                title=f"Error loading chart for {ticker_data.symbol}",
                template="plotly_dark"
            )
    
    def create_profit_chart(self, ticker_data_list: List[TickerData], 
                           title: str = "Portfolio Profit History") -> go.Figure:
        """Create portfolio profit progression chart."""
        try:
            fig = go.Figure()
            
            # Calculate total profit series
            if ticker_data_list and ticker_data_list[0].price_history is not None:
                dates = ticker_data_list[0].price_history.index
                total_profit = sum(ticker.profit_series for ticker in ticker_data_list)
                
                # Find extrema
                (max_val, max_date), (min_val, min_date) = self.calculator.find_extrema(total_profit, dates)
                
                # Add main profit line
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=total_profit,
                    name="Portfolio Profit",
                    line=dict(width=3, color=self.colors["accent"]),
                    hovertemplate='<b>Portfolio Profit</b><br>' +
                                 'Date: %{x|%d %b %Y}<br>' +
                                 'Profit: $%{y:,.2f}<extra></extra>'
                ))
                
                # Add extrema markers
                fig.add_trace(go.Scatter(
                    x=[max_date], y=[max_val],
                    mode="markers", name="Maximum Profit",
                    marker=dict(size=14, color=self.colors["green"]),
                    hovertemplate='<b>Maximum Profit</b><br>' +
                                 'Date: %{x|%d %b %Y}<br>' +
                                 'Profit: $%{y:,.2f}<extra></extra>'
                ))
                
                fig.add_trace(go.Scatter(
                    x=[min_date], y=[min_val],
                    mode="markers", name="Minimum Profit",
                    marker=dict(size=14, color=self.colors["red"]),
                    hovertemplate='<b>Minimum Profit</b><br>' +
                                 'Date: %{x|%d %b %Y}<br>' +
                                 'Profit: $%{y:,.2f}<extra></extra>'
                ))
                
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
                    "text": title,
                    "font": {"size": 20, "color": self.colors["text_primary"]},
                    "y": 0.95, "x": 0.5, "xanchor": "center", "yanchor": "top"
                },
                xaxis_title="Date",
                yaxis_title="Profit ($)",
                legend={
                    "orientation": "h",
                    "yanchor": "bottom", "y": 1.02,
                    "xanchor": "center", "x": 0.5
                },
                yaxis=dict(
                    dtick=self.config.market.portfolio_profit_tick,
                    showgrid=True, gridcolor=self.colors["grid"]
                ),
                xaxis=dict(showgrid=True, gridcolor=self.colors["grid"]),
                plot_bgcolor=self.colors["card_bg"],
                paper_bgcolor=self.colors["card_bg"],
                font=dict(color=self.colors["text_primary"]),
                hovermode="x unified"
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating profit chart: {e}")
            return go.Figure().update_layout(title="Error loading profit chart", template="plotly_dark")
    
    def create_chart_container(self, figure: go.Figure) -> html.Div:
        """Wrap chart in styled container."""
        return html.Div([
            dcc.Graph(figure=figure)
        ], style={
            "backgroundColor": self.colors["card_bg"],
            "borderRadius": "12px",
            "boxShadow": "0 4px 12px rgba(0,0,0,0.3)",
            "border": "1px solid #333333",
            "marginBottom": "20px"
        })
