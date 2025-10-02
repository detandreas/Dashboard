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
                
                # Current P&L values
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
            initial_chart_fig = self._create_enhanced_profit_chart(
                portfolio, portfolio.tickers, "Portfolio Profit History", "All", include_usd=False
            )
            initial_chart = self.ui_factory.create_chart_container(initial_chart_fig)
            initial_metrics = self._get_profit_metrics(portfolio, include_usd=False)
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
                {"label": "Portfolio Profit History", "value": "profit"},
                {"label": "Portfolio Yield Percentage", "value": "yield"}
            ],
            default_chart="profit"
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
    
    def _get_profit_metrics(self, portfolio: PortfolioSnapshot, include_usd: bool) -> html.Div:
        """Get profit metrics for the side panel."""
        total_profit = portfolio.total_profit_series(include_usd)
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

                # Current P&L values
                metrics = self._calculate_portfolio_metrics(portfolio, include_usd)
                current_profit = metrics["profit_absolute"]
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
                            "Maximum Profit",
                            f"${max_profit:.2f}",
                            self.colors["green"],
                            f"on {max_date.strftime('%d %b %Y')}"
                        )
                    ], style={"marginBottom": "15px"}),
                    html.Div([
                        self.ui_factory.create_side_metric_card(
                            "Minimum Profit",
                            f"${min_profit:.2f}",
                            self.colors["red"],
                            f"on {min_date.strftime('%d %b %Y')}"
                        )
                    ], style={"marginBottom": "15px"}),
                    html.Div([
                        self.ui_factory.create_side_metric_card(
                            pnl_label,
                            f"${current_profit:.2f}",
                            profit_color
                            
                        )
                    ])
                ], style={
                    "height": "525px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "space-evenly"
                })
        
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
    
    def _get_yield_metrics(self, portfolio: PortfolioSnapshot, include_usd: bool) -> html.Div:
        """Get yield metrics for the side panel."""
        yield_series = self._calculate_yield_series(portfolio, include_usd)

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
        
        (max_yield, max_date), (min_yield, min_date) = \
            self.ui_factory.calculator.find_extrema(yield_series, dates)
        
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
                    "Maximum Yield",
                    f"{max_yield:.2f}%",
                    self.colors["green"],
                    f"on {max_date.strftime('%d %b %Y')}"
                )
            ], style={"marginBottom": "15px"}),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Minimum Yield",
                    f"{min_yield:.2f}%",
                    self.colors["red"],
                    f"on {min_date.strftime('%d %b %Y')}"
                )
            ], style={"marginBottom": "15px"}),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Current Yield",
                    f"{yield_series[-1]:.2f}%",
                    self.colors["green"] if yield_series[-1] >= 0 else self.colors["red"]
                )
            ])
        ], style={
            "height": "525px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-evenly"
        })
    
    def _get_profit_chart_and_metrics(self, portfolio: PortfolioSnapshot) -> tuple:
        """Get profit chart and its metrics."""
        profit_chart_fig = self.ui_factory.create_profit_chart(
            portfolio.tickers, 
            "Portfolio Profit History"
        )
        profit_chart = self.ui_factory.create_chart_container(profit_chart_fig)
        
        # Calculate profit metrics
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
                
                # Current P&L values
                current_profit = portfolio.total_metrics.profit_absolute
                current_return = portfolio.total_metrics.return_percentage
                profit_color = self.colors["green"] if current_profit >= 0 else self.colors["red"]
                
                # Stacked metrics for right side
                profit_metrics = html.Div([
                    html.H4("Profit Analysis", style={
                        "color": self.colors["accent"],
                        "marginBottom": "20px",
                        "textAlign": "center",
                        "fontSize": "1rem"
                    }),
                    html.Div([
                        self.ui_factory.create_side_metric_card(
                            "Maximum Profit",
                            f"${max_profit:.2f}",
                            self.colors["green"],
                            f"on {max_date.strftime('%d %b %Y')}"
                        )
                    ], style={"marginBottom": "15px"}),
                    html.Div([
                        self.ui_factory.create_side_metric_card(
                            "Minimum Profit",
                            f"${min_profit:.2f}",
                            self.colors["red"],
                            f"on {min_date.strftime('%d %b %Y')}"
                        )
                    ], style={"marginBottom": "15px"}),
                    html.Div([
                        self.ui_factory.create_side_metric_card(
                            "Current P&L",
                            f"${current_profit:.2f}",
                            profit_color,
                            f"Return: {current_return:.2f}%"
                        )
                    ])
                ], style={
                    "height": "525px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "space-evenly"
                })
            else:
                profit_metrics = html.Div([
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
        else:
            profit_metrics = html.Div([
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
        
        return profit_chart, profit_metrics
    
    def _get_yield_chart_and_metrics(self, portfolio: PortfolioSnapshot) -> tuple:
        """Get yield chart and its metrics."""
        yield_series = portfolio.portfolio_yield_series
        
        if len(yield_series) == 0:
            empty_chart = html.Div([
                html.H4("Portfolio Yield", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                }),
                html.P("No yield data available", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ])
            empty_metrics = html.Div(style={
                "height": "525px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
            return empty_chart, empty_metrics
        
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
            empty_chart = html.Div([
                html.H4("Portfolio Yield", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                }),
                html.P("Unable to calculate yield - insufficient data", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ])
            empty_metrics = html.Div(style={
                "height": "525px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
            return empty_chart, empty_metrics
        
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
                dtick=3,
                showgrid=True, gridcolor=self.colors["grid"]
            ),
            xaxis=dict(showgrid=True, gridcolor=self.colors["grid"]),
            plot_bgcolor=self.colors["card_bg"],
            paper_bgcolor=self.colors["card_bg"],
            font=dict(color=self.colors["text_primary"]),
            hovermode="x unified"
        )
        
        # Stacked yield metrics for right side
        yield_metrics = html.Div([
            html.H4("Yield Analysis", style={
                "color": self.colors["accent"],
                "marginBottom": "20px",
                "textAlign": "center",
                "fontSize": "1rem"
            }),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Maximum Yield",
                    f"{max_yield:.2f}%",
                    self.colors["green"],
                    f"on {max_date.strftime('%d %b %Y')}"
                )
            ], style={"marginBottom": "15px"}),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Minimum Yield",
                    f"{min_yield:.2f}%",
                    self.colors["red"],
                    f"on {min_date.strftime('%d %b %Y')}"
                )
            ], style={"marginBottom": "15px"}),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Current Yield",
                    f"{yield_series[-1]:.2f}%",
                    self.colors["green"] if yield_series[-1] >= 0 else self.colors["red"]
                )
            ])
        ], style={
            "height": "525px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-evenly"
        })
        
        return self.ui_factory.create_chart_container(fig), yield_metrics
    
    def _filter_data_by_timeframe(self, dates, data_series, timeframe: str):
        """Filter data based on selected timeframe."""
        if timeframe == "All" or len(dates) == 0:
            return dates, data_series

        end_date = dates[-1]
        
        if timeframe == "1M":
            start_date = end_date - timedelta(days=30)
        elif timeframe == "3M":
            start_date = end_date - timedelta(days=90)
        elif timeframe == "6M":
            start_date = end_date - timedelta(days=180)
        elif timeframe == "1Y":
            start_date = end_date - timedelta(days=365)
        else:
            return dates, data_series
        
        # Filter dates and corresponding data
        mask = dates >= start_date
        filtered_dates = dates[mask]
        
        if isinstance(data_series, (list, np.ndarray)):
            filtered_data = np.array(data_series)[mask]
        else:
            filtered_data = data_series[mask]

        return filtered_dates, filtered_data

    def _calculate_portfolio_metrics(self, portfolio: PortfolioSnapshot, include_usd: bool) -> dict:
        """Calculate dynamic portfolio metrics with optional USD/EUR inclusion."""
        equity_tickers = [t for t in portfolio.tickers if t.symbol != "USD/EUR"]
        usd_tickers = [t for t in portfolio.tickers if t.symbol == "USD/EUR"] if include_usd else []

        total_invested = sum(t.metrics.invested for t in equity_tickers)
        total_current = sum(t.metrics.current_value for t in equity_tickers)
        total_profit = sum(t.metrics.profit_absolute for t in equity_tickers)

        if include_usd and usd_tickers:
            total_invested += sum(t.metrics.invested for t in usd_tickers)
            total_current += sum(t.metrics.current_value for t in usd_tickers)
            total_profit += sum(t.metrics.profit_absolute for t in usd_tickers)

        return_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0.0

        return {
            "invested": total_invested,
            "current_value": total_current,
            "profit_absolute": total_profit,
            "return_percentage": return_pct
        }

    def _calculate_yield_series(self, portfolio: PortfolioSnapshot, include_usd: bool) -> np.ndarray:
        """Calculate yield series with optional USD/EUR profit inclusion."""
        invested_series = self._calculate_invested_series(portfolio)
        if len(invested_series) == 0:
            return np.array([])

        profit_series = portfolio.total_profit_series(include_usd)
        if len(profit_series) == 0:
            return np.array([])

        min_length = min(len(invested_series), len(profit_series))
        invested_series = invested_series[:min_length]
        profit_series = profit_series[:min_length]

        yield_values = [
            (profit / invested * 100) if invested > 0 else 0.0
            for profit, invested in zip(profit_series, invested_series)
        ]

        return np.array(yield_values)

    def _calculate_invested_series(self, portfolio: PortfolioSnapshot) -> np.ndarray:
        """Calculate invested capital series for equity tickers."""
        equity_tickers = [t for t in portfolio.tickers if t.symbol != "USD/EUR"]
        if not equity_tickers:
            return np.array([])

        base_dates = None
        for ticker in equity_tickers:
            if ticker.has_trades and len(ticker.price_history) > 0:
                base_dates = ticker.price_history.index
                break

        if base_dates is None:
            return np.array([])

        invested_values = []
        for i, _ in enumerate(base_dates):
            daily_invested = 0.0
            for ticker in equity_tickers:
                if i < len(ticker.dca_history) and i < len(ticker.shares_per_day):
                    dca_value = ticker.dca_history[i]
                    if not np.isnan(dca_value):
                        daily_invested += dca_value * ticker.shares_per_day[i]
            invested_values.append(daily_invested)

        return np.array(invested_values)

    def _create_enhanced_profit_chart(self, portfolio : PortfolioSnapshot, ticker_data_list, title: str, timeframe: str = "All", include_usd: bool = False):
        """Create enhanced profit chart with timeframe filtering and different view modes."""
        try:
            fig = go.Figure()

            dates = None
            for ticker in ticker_data_list:
                if ticker.has_trades and len(ticker.price_history) > 0:
                    dates = ticker.price_history.index
                    break

            if dates is not None:
                total_profit = portfolio.total_profit_series(include_usd)

                # Apply timeframe filter
                filtered_dates, filtered_profit = self._filter_data_by_timeframe(dates, total_profit, timeframe)

                if len(filtered_dates) == 0:
                    return go.Figure().update_layout(
                        title="No data available for selected timeframe",
                        template="plotly_dark"
                    )
                
                # Calculate extrema for filtered data
                (max_val, max_date), (min_val, min_date) = self.ui_factory.calculator.find_extrema(
                    filtered_profit, filtered_dates
                )
                
                # Create main trace - always area style
                fig.add_trace(
                    go.Scatter(
                        x=filtered_dates,
                        y=filtered_profit,
                        name="",
                        fill='tonexty' if min(filtered_profit) < 0 else 'tozeroy',
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
                
            
            else:
                return go.Figure().update_layout(
                    title="No profit data available",
                    template="plotly_dark"
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
                showlegend=True,
                # Remove Plotly toolbar
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
            yield_series = self._calculate_yield_series(portfolio, include_usd)

            if len(yield_series) == 0:
                return go.Figure().update_layout(
                    title="No yield data available",
                    template="plotly_dark"
                )
            
            # Get dates
            dates = None
            for ticker in portfolio.equity_tickers:
                if ticker.has_trades and len(ticker.price_history) > 0:
                    dates = ticker.price_history.index
                    break
            
            if dates is None:
                for ticker in portfolio.tickers:
                    if ticker.has_trades and len(ticker.price_history) > 0:
                        dates = ticker.price_history.index
                        break
            
            if dates is None or len(dates) != len(yield_series):
                return go.Figure().update_layout(
                    title="Unable to calculate yield - insufficient data",
                    template="plotly_dark"
                )
            
            # Apply timeframe filter
            filtered_dates, filtered_yield = self._filter_data_by_timeframe(dates, yield_series, timeframe)
            
            if len(filtered_dates) == 0:
                return go.Figure().update_layout(
                    title="No data available for selected timeframe",
                    template="plotly_dark"
                )
            
            (max_yield, max_date), (min_yield, min_date) = \
                self.ui_factory.calculator.find_extrema(filtered_yield, filtered_dates)
            
            fig = go.Figure()
            
            # Create main trace - always area style
            fig.add_trace(
                go.Scatter(
                    x=filtered_dates,
                    y=filtered_yield,
                    name="",
                    fill='tonexty' if min(filtered_yield) < 0 else 'tozeroy',
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
                    x=[max_date], y=[max_yield],
                    mode="markers", name="Maximum",
                    marker=dict(size=12, color=self.colors["green"], symbol="circle"),
                    hovertemplate='<b>Maximum Yield</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Yield: %{y:.2f}%<extra></extra>'
                )
            )
            
            fig.add_trace(
                go.Scatter(
                    x=[min_date], y=[min_yield],
                    mode="markers", name="Minimum",
                    marker=dict(size=12, color=self.colors["red"], symbol="circle"),
                    hovertemplate='<b>Minimum Yield</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Yield: %{y:.2f}%<extra></extra>'
                )
            )
            
            # Add zero line
            fig.add_shape(
                type="line",
                x0=filtered_dates[0], x1=filtered_dates[-1],
                y0=0, y1=0,
                line=dict(color="rgba(255,255,255,0.3)", width=1, dash="dot")
            )
            
            
            fig.update_layout(
                height=500,
                template="plotly_dark",
                xaxis_title="Date",
                yaxis_title="Yield (%)",
                legend={
                    "orientation": "h",
                    "yanchor": "bottom", "y": 1.02,
                    "xanchor": "center", "x": 0.5
                },
                yaxis=dict(
                    dtick=3,
                    showgrid=True, gridcolor=self.colors["grid"],
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
                # Remove Plotly toolbar
                margin=dict(l=60, r=40, t=80, b=60),
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating enhanced yield chart: {e}")
            return go.Figure().update_layout(
                title="Error loading yield chart",
                template="plotly_dark"
            )
    
