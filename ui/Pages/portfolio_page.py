from dash import html, dcc
import plotly.graph_objects as go
import logging
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

from ui.Pages.base_page import BasePage
from models.portfolio import PortfolioSnapshot
from services.portfolio_service import PortfolioService
from ui.Components import UIComponentFactory

logger = logging.getLogger(__name__)

class PortfolioPage(BasePage):
    """Portfolio overview page."""
    
    def __init__(self, portfolio_service: PortfolioService, ui_factory: UIComponentFactory, goal_service=None):
        super().__init__(ui_factory)
        self.portfolio_service = portfolio_service
        self.goal_service = goal_service
    
    
    def render(self) -> html.Div:
        """Render portfolio overview."""
        try:
            portfolio = self.portfolio_service.get_portfolio_snapshot()

            # Top row: composition (left) and goals (right) side-by-side
            top_row = html.Div([
                html.Div(
                    self.ui_factory.create_portfolio_composition(portfolio),
                    style={
                        "flex": "1 1 38%",
                        "maxWidth": "38%",
                        "minWidth": "300px",
                        "boxSizing": "border-box"
                    }
                ),
                html.Div(
                    self._create_goal_section(portfolio),
                    style={
                        "flex": "1 1 60%",
                        "maxWidth": "62%",
                        "minWidth": "380px",
                        "boxSizing": "border-box"
                    }
                )
            ], style={
                "display": "flex",
                "gap": "20px",
                "flexWrap": "wrap",
                "alignItems": "stretch",
                "marginBottom": "20px"
            })

            sections = [
                top_row,
                # Combined chart section with dropdown
                self._create_combined_chart_section(portfolio),
                # Tickers table with USD/EUR filter
                self.ui_factory.create_tickers_table_section(
                    tickers=portfolio.tickers,
                    total_portfolio_value=portfolio.total_metrics.current_value
                )
            ]

            return html.Div(sections)
            
        except Exception as e:
            logger.error(f"Error rendering portfolio page: {e}")
            return self._create_error_message(str(e))
    
    
    def _create_goal_section(self, portfolio: PortfolioSnapshot) -> html.Div:
        """Δημιουργεί το goal progress section."""
        if not self.goal_service:
            return html.Div()  # Δεν εμφανίζει τίποτα αν δεν υπάρχει goal service
        
        try:
            current_value = portfolio.total_metrics.current_value
            goal_data = self.goal_service.update_milestone_status(current_value)
            
            return self.ui_factory.create_goal_progress_bar(goal_data)
            
        except Exception as e:
            logger.error(f"Error creating goal section: {e}")
            return html.Div([
                html.P("Error loading goals", style={
                    "color": self.colors["red"],
                    "textAlign": "center"
                })
            ], style=self.config.ui.card_style)
    
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
    
    def _create_combined_chart_section(self, portfolio: PortfolioSnapshot) -> html.Div:
        """Create combined chart section using utility functions."""
        # Generate initial content
        try:
            initial_chart_fig = self._create_enhanced_value_chart(
                portfolio, "All", include_usd=False
            )
            initial_chart = self.ui_factory.create_chart_container(initial_chart_fig)
            initial_metrics = self._get_value_metrics(portfolio, include_usd=False, timeframe="All")
        except Exception as e:
            logger.error(f"Error creating initial portfolio chart: {e}")
            initial_chart = html.Div([
                html.P("Error loading chart", style={
                    "textAlign": "center",
                    "color": self.colors["red"]
                })
            ])
            initial_metrics = html.Div()
        
        # Use utility functions
        chart_dropdown = self.ui_factory.create_chart_dropdown(
            chart_id_prefix="portfolio",
            chart_options=[
                {"label": "Portfolio Value", "value": "value"},
                {"label": "Portfolio Profit History", "value": "profit"},
                {"label": "Portfolio Yield Percentage", "value": "yield"}
            ],
            default_chart="value",
            width="200px"
        )
        
        timeframe_buttons = self.ui_factory.create_timeframe_buttons("portfolio")
        
        stores = [dcc.Store(id="portfolio-active-timeframe", data="All")]
        
        return self.ui_factory.create_chart_layout(
            chart_id_prefix="portfolio",
            chart_dropdown=chart_dropdown,
            timeframe_buttons=timeframe_buttons,
            initial_chart=initial_chart,
            initial_metrics=initial_metrics,
            stores=stores
        )
    
    def _get_profit_metrics(self, portfolio: PortfolioSnapshot, include_usd: bool, timeframe: str = "All") -> html.Div:
        """Get profit metrics for the side panel."""
        total_profit = self.portfolio_service.get_total_profit_series(include_usd)
        if len(total_profit) == 0:
            return html.Div([
                html.P("No profit data available", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style={
                "height": "525px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
        # Get dates from the first ticker that has price history
        dates = self.ui_factory.calculator.get_portfolio_dates(portfolio)

        if dates is None or len(dates) != len(total_profit):
            return html.Div([
                html.P("Unable to calculate profit metrics", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style={
                "height": "525px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
        
        
        
        side_metrics = self.ui_factory.calculator.calculate_side_metrics(total_profit, dates, timeframe)
        max_profit = side_metrics["max_value"]
        max_date = side_metrics["max_date"]
        min_profit = side_metrics["min_value"]
        min_date = side_metrics["min_date"]
        # Current P&L values
        current_profit = side_metrics["current_value"]
        profit_color = self.colors["green"] if current_profit >= 0 else self.colors["red"]
        pnl_label = "Current P&L"
        
        # Stacked metrics for right side
        return html.Div([
            html.H4("Profit Analysis", style={
                "color": self.colors["accent"],
                "marginBottom": "20px",
                "textAlign": "center",
                "fontSize": "1rem"
            }),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    pnl_label,
                    f"${current_profit:.2f}",
                    profit_color
                    
                )
            ]),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Maximum Profit",
                    f"${max_profit:.2f}",
                    self.colors["green"] if max_profit >= 0 else self.colors["red"],
                    f"on {max_date.strftime('%d %b %Y')}"
                )
            ], style={"marginBottom": "15px"}),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Minimum Profit",
                    f"${min_profit:.2f}",
                    self.colors["red"] if min_profit < 0 else self.colors["green"],
                    f"on {min_date.strftime('%d %b %Y')}"
                )
            ], style={"marginBottom": "15px"}),
        ], style={
            "height": "525px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-evenly"
        })
    
    
    def _get_yield_metrics(self, portfolio: PortfolioSnapshot, include_usd: bool, timeframe: str = "All") -> html.Div:
        """Get yield metrics for the side panel."""
        yield_series = self.ui_factory.calculator.calculate_yield_series(portfolio, include_usd)

        if len(yield_series) == 0:
            return html.Div([
                html.P("No yield data available", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style={
                "height": "525px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
        
        # Get dates from equity tickers that have price history
        dates = self.ui_factory.calculator.get_portfolio_dates(portfolio)

        if dates is None or len(dates) != len(yield_series):
            return html.Div([
                html.P("Unable to calculate yield metrics", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style={
                "height": "525px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
        
        side_metrics = \
            self.ui_factory.calculator.calculate_side_metrics(yield_series, dates, timeframe)
        
        max_yield = side_metrics["max_value"]
        min_yield = side_metrics["min_value"]
        max_date = side_metrics["max_date"]
        min_date = side_metrics["min_date"]
        current_yield = side_metrics["current_value"]
        
        # Stacked yield metrics for right side
        return html.Div([
            html.H4("Yield Analysis", style={
                "color": self.colors["accent"],
                "marginBottom": "20px",
                "textAlign": "center",
                "fontSize": "1rem"
            }),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Current Yield",
                    f"{current_yield:.2f}%",
                    self.colors["green"] if yield_series[-1] >= 0 else self.colors["red"]
                )
            ]),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Maximum Yield",
                    f"{max_yield:.2f}%",
                    self.colors["green"] if max_yield >= 0 else self.colors["red"],
                    f"on {max_date.strftime('%d %b %Y')}"
                )
            ], style={"marginBottom": "15px"}),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Minimum Yield",
                    f"{min_yield:.2f}%",
                    self.colors["red"] if min_yield < 0 else self.colors["green"],
                    f"on {min_date.strftime('%d %b %Y')}"
                )
            ], style={"marginBottom": "15px"}),
        ], style={
            "height": "525px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-evenly"
        })
    
    def _get_value_metrics(self, portfolio : PortfolioSnapshot, include_usd : bool, timeframe : str) -> html.Div:
        """Get value metrics for side panel."""
        total_value = self.portfolio_service.get_portfolio_value_series(include_usd)

        if len(total_value) == 0:
            return html.Div([
                html.P("No value data available", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style={
                "height": "525px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
    
        #Get dates from the first ticker that has price history
        dates = self.ui_factory.calculator.get_portfolio_dates(portfolio)
        if dates is None or len(dates) != len(total_value):
            return html.Div([
                html.P("Unable to calculate value metrics", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style={
                "height": "525px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
        
        
        side_metrics = self.ui_factory.calculator.calculate_side_metrics(total_value, dates, timeframe)
        max_value = side_metrics['max_value']
        max_date = side_metrics['max_date']
        min_value = side_metrics['min_value']
        min_date = side_metrics['min_date']
        current_value = side_metrics['current_value']
        value_color = self.colors['accent']
        #staced metrics for right side
        return html.Div([
            html.H4("Value Analysis", style={
                "color" : self.colors["accent"],
                "marginBottom" : "20px",
                "textAlign" : "center",
                "fontSize" : "1rem"
            }),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Current Value",
                    f"${current_value:.2f}",
                    value_color  
                )
            ]),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Maximum Value",
                    f"{max_value:.2f}",
                    self.colors['text_primary'],
                    f"on {max_date.strftime('%d %b %Y')}"
                )
            ], style={"marginBottom" : "15px"}),
            html.Div([
                    self.ui_factory.create_side_metric_card(
                        "Minimum Value",
                        f"${min_value:.2f}",
                        self.colors["text_primary"],
                        f"on {min_date.strftime('%d %b %Y')}"
                    )
                ], style={"marginBottom": "15px"})
        ], style={
            "height": "525px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-evenly"
        })
    
    
    def _create_enhanced_profit_chart(self, portfolio: PortfolioSnapshot, ticker_data_list, title: str, timeframe: str = "All", include_usd: bool = False):
        """Create enhanced profit chart with timeframe filtering."""
        try:
            # Get data
            dates = self.ui_factory.calculator.get_portfolio_dates(portfolio)
            
            if dates is None:
                return go.Figure().update_layout(
                    title="No profit data available",
                    template="plotly_dark"
                )
            
            total_profit = self.portfolio_service.get_total_profit_series(include_usd)
            
            if len(total_profit) == 0:
                return go.Figure().update_layout(
                    title="No profit data available",
                    template="plotly_dark"
                )
            
            # Apply timeframe filter
            filtered_dates, filtered_profit = self.ui_factory.calculator.filter_data_by_timeframe(dates, total_profit, timeframe)
            
            if len(filtered_dates) == 0:
                return go.Figure().update_layout(
                    title="No data available for selected timeframe",
                    template="plotly_dark"
                )
            
            # Calculate extrema for filtered data
            (max_val, max_date), (min_val, min_date) = self.ui_factory.calculator.find_extrema(
                filtered_profit, filtered_dates
            )
            
            fig = go.Figure()
            
            # Create main trace - always area style
            fig.add_trace(
                go.Scatter(
                    x=filtered_dates,
                    y=filtered_profit,
                    name="",
                    fill='tonexty' if filtered_profit.min() < 0 else 'tozeroy',
                    fillcolor='rgba(99, 102, 241, 0.2)',
                    line=dict(width=3, color=self.colors["accent"]),
                    hovertemplate='<b>Portfolio Profit</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Profit: $%{y:,.2f}<extra></extra>',
                    showlegend=False
                )
            )
            
            # Add extrema markers
            fig.add_trace(
                go.Scatter(
                    x=[max_date],
                    y=[max_val],
                    mode="markers",
                    name="Maximum",
                    marker=dict(size=12, color=self.colors["green"], symbol="circle"),
                    hovertemplate='<b>Maximum Profit</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Profit: $%{y:,.2f}<extra></extra>',
                )
            )
            
            fig.add_trace(
                go.Scatter(
                    x=[min_date],
                    y=[min_val],
                    mode="markers",
                    name="Minimum",
                    marker=dict(size=12, color=self.colors["red"], symbol="circle"),
                    hovertemplate='<b>Minimum Profit</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Profit: $%{y:,.2f}<extra></extra>',
                )
            )
            
            # Add zero line
            fig.add_shape(
                type="line",
                x0=filtered_dates[0],
                x1=filtered_dates[-1],
                y0=0,
                y1=0,
                line=dict(color="rgba(255,255,255,0.3)", width=1, dash="dot"),
            )
            
            # Enhanced layout
            fig.update_layout(
                height=500,
                template="plotly_dark",
                xaxis_title="Date",
                yaxis_title="Profit ($)",
                legend={
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "center",
                    "x": 0.5,
                },
                yaxis=dict(
                    dtick=200,
                    showgrid=True,
                    gridcolor=self.colors["grid"],
                    zeroline=True,
                    zerolinecolor="rgba(255,255,255,0.3)",
                    zerolinewidth=1,
                ),
                xaxis=dict(
                    showgrid=True, 
                    gridcolor=self.colors["grid"],
                    rangeslider=dict(visible=False),
                    type="date"
                ),
                plot_bgcolor=self.colors["card_bg"],
                paper_bgcolor=self.colors["card_bg"],
                font=dict(color=self.colors["text_primary"]),
                hovermode="x unified",
                margin=dict(l=60, r=40, t=80, b=60),
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating enhanced profit chart: {e}")
            return go.Figure().update_layout(
                title="Error loading profit chart", 
                template="plotly_dark"
            )
    
    def _create_enhanced_yield_chart(self, portfolio: PortfolioSnapshot, timeframe: str = "All", include_usd: bool = False):
        """Create enhanced yield chart with timeframe filtering."""
        try:
            # Get dates using the same method as profit chart
            dates = self.ui_factory.calculator.get_portfolio_dates(portfolio)
            
            if dates is None:
                return go.Figure().update_layout(
                    title="Unable to calculate yield - insufficient data",
                    template="plotly_dark"
                )
            
            # Get data
            yield_series = self.portfolio_service.get_yield_series(include_usd)
            
            if len(yield_series) == 0:
                return go.Figure().update_layout(
                    title="No yield data available",
                    template="plotly_dark"
                )
            
            # Apply timeframe filter
            filtered_dates, filtered_yield = self.ui_factory.calculator.filter_data_by_timeframe(dates, yield_series, timeframe)
            
            if len(filtered_dates) == 0:
                return go.Figure().update_layout(
                    title="No data available for selected timeframe",
                    template="plotly_dark"
                )
            
            # Calculate extrema for filtered data
            (max_yield, max_date), (min_yield, min_date) = self.ui_factory.calculator.find_extrema(
                filtered_yield, filtered_dates
            )
            
            fig = go.Figure()
            
            # Create main trace - always area style
            fig.add_trace(
                go.Scatter(
                    x=filtered_dates,
                    y=filtered_yield,
                    name="",
                    fill='tonexty' if filtered_yield.min() < 0 else 'tozeroy',
                    fillcolor='rgba(99, 102, 241, 0.2)',
                    line=dict(width=3, color=self.colors["accent"]),
                    hovertemplate='<b>Portfolio Yield</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Yield: %{y:.2f}%<extra></extra>',
                    showlegend=False
                )
            )
            
            # Add extrema markers
            fig.add_trace(
                go.Scatter(
                    x=[max_date],
                    y=[max_yield],
                    mode="markers",
                    name="Maximum",
                    marker=dict(size=12, color=self.colors["green"], symbol="circle"),
                    hovertemplate='<b>Maximum Yield</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Yield: %{y:.2f}%<extra></extra>',
                )
            )
            
            fig.add_trace(
                go.Scatter(
                    x=[min_date],
                    y=[min_yield],
                    mode="markers",
                    name="Minimum",
                    marker=dict(size=12, color=self.colors["red"], symbol="circle"),
                    hovertemplate='<b>Minimum Yield</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Yield: %{y:.2f}%<extra></extra>',
                )
            )
            
            # Add zero line
            fig.add_shape(
                type="line",
                x0=filtered_dates[0],
                x1=filtered_dates[-1],
                y0=0,
                y1=0,
                line=dict(color="rgba(255,255,255,0.3)", width=1, dash="dot"),
            )
            
            # Enhanced layout
            fig.update_layout(
                height=500,
                template="plotly_dark",
                xaxis_title="Date",
                yaxis_title="Yield (%)",
                legend={
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "center",
                    "x": 0.5,
                },
                yaxis=dict(
                    dtick=3,
                    showgrid=True,
                    gridcolor=self.colors["grid"],
                    zeroline=True,
                    zerolinecolor="rgba(255,255,255,0.3)",
                    zerolinewidth=1,
                ),
                xaxis=dict(
                    showgrid=True, 
                    gridcolor=self.colors["grid"],
                    rangeslider=dict(visible=False),
                    type="date"
                ),
                plot_bgcolor=self.colors["card_bg"],
                paper_bgcolor=self.colors["card_bg"],
                font=dict(color=self.colors["text_primary"]),
                hovermode="x unified",
                margin=dict(l=60, r=40, t=80, b=60),
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating enhanced yield chart: {e}")
            return go.Figure().update_layout(
                title="Error loading yield chart",
                template="plotly_dark"
            )
    
    def _create_enhanced_value_chart(self, portfolio: PortfolioSnapshot, timeframe: str = "All", include_usd: bool = False):
        """Create enhanced value chart with timeframe filtering."""
        try:
            # Get dates using the same method as profit chart
            dates = self.ui_factory.calculator.get_portfolio_dates(portfolio)
            
            if dates is None:
                return go.Figure().update_layout(
                    title="Unable to calculate value - insufficient data",
                    template="plotly_dark"
                )
            
            # Get data
            value_series = self.portfolio_service.get_portfolio_value_series(include_usd)
            
            if len(value_series) == 0:
                return go.Figure().update_layout(
                    title="No value data available",
                    template="plotly_dark"
                )
            
            # Apply timeframe filter
            filtered_dates, filtered_value = self.ui_factory.calculator.filter_data_by_timeframe(dates, value_series, timeframe)
            
            if len(filtered_dates) == 0:
                return go.Figure().update_layout(
                    title="No data available for selected timeframe",
                    template="plotly_dark"
                )
            
            # Calculate extrema for filtered data
            (max_value, max_date), (min_value, min_date) = self.ui_factory.calculator.find_extrema(
                filtered_value, filtered_dates
            )
            
            fig = go.Figure()
            
            # Create main trace - always area style
            fig.add_trace(
                go.Scatter(
                    x=filtered_dates,
                    y=filtered_value,
                    name="",
                    fill='tozeroy',
                    fillcolor='rgba(99, 102, 241, 0.2)',
                    line=dict(width=3, color=self.colors["accent"]),
                    hovertemplate='<b>Portfolio Value</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Value: $%{y:,.2f}<extra></extra>',
                    showlegend=False
                )
            )
            
            # Add extrema markers
            fig.add_trace(
                go.Scatter(
                    x=[max_date],
                    y=[max_value],
                    mode="markers",
                    name="Maximum",
                    marker=dict(size=12, color=self.colors["green"], symbol="circle"),
                    hovertemplate='<b>Maximum Value</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Value: $%{y:,.2f}<extra></extra>',
                )
            )
            
            fig.add_trace(
                go.Scatter(
                    x=[min_date],
                    y=[min_value],
                    mode="markers",
                    name="Minimum",
                    marker=dict(size=12, color=self.colors["red"], symbol="circle"),
                    hovertemplate='<b>Minimum Value</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Value: $%{y:,.2f}<extra></extra>',
                )
            )
            
            # Enhanced layout
            fig.update_layout(
                height=500,
                template="plotly_dark",
                xaxis_title="Date",
                yaxis_title="Portfolio Value ($)",
                legend={
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "center",
                    "x": 0.5,
                },
                yaxis=dict(
                    dtick=1000,
                    showgrid=True,
                    gridcolor=self.colors["grid"],
                    zeroline=False,
                ),
                xaxis=dict(
                    showgrid=True, 
                    gridcolor=self.colors["grid"],
                    rangeslider=dict(visible=False),
                    type="date"
                ),
                plot_bgcolor=self.colors["card_bg"],
                paper_bgcolor=self.colors["card_bg"],
                font=dict(color=self.colors["text_primary"]),
                hovermode="x unified",
                margin=dict(l=60, r=40, t=80, b=60),
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating enhanced value chart: {e}")
            return go.Figure().update_layout(
                title="Error loading value chart",
                template="plotly_dark"
            )
    
