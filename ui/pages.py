from abc import ABC, abstractmethod
from dash import html, dcc, dash_table
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import logging
from typing import List

from models.portfolio import TickerData, PortfolioSnapshot
from services.portfolio_service import PortfolioService
from ui.components import UIComponentFactory
from config.settings import Config

logger = logging.getLogger(__name__)

class BasePage(ABC):
    """Abstract base class for dashboard pages."""
    
    def __init__(self, ui_factory: UIComponentFactory):
        self.ui_factory = ui_factory
        self.config = ui_factory.config
        self.colors = ui_factory.colors
    
    @abstractmethod
    def render(self) -> html.Div:
        """Render the page content."""
        pass

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

class PortfolioPage(BasePage):
    """Portfolio overview page."""
    
    def __init__(self, portfolio_service: PortfolioService, ui_factory: UIComponentFactory):
        super().__init__(ui_factory)
        self.portfolio_service = portfolio_service
    
    def render(self) -> html.Div:
        """Render portfolio overview."""
        try:
            portfolio = self.portfolio_service.get_portfolio_snapshot()
            
            return html.Div([
                # Portfolio composition pie chart
                self.ui_factory.create_portfolio_composition(portfolio),
                
                # Portfolio profit chart with current profit/loss above
                self._create_profit_section(portfolio),
                
                # Portfolio yield chart
                self._create_yield_section(portfolio)
            ])
            
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

class TradesPage(BasePage):
    """Trading history page."""
    
    def __init__(self, portfolio_service: PortfolioService, ui_factory: UIComponentFactory):
        super().__init__(ui_factory)
        self.portfolio_service = portfolio_service
    
    def render(self) -> html.Div:
        """Render trades history table."""
        try:
            # Load trades data for display
            df = pd.read_excel(self.config.database.trades_xlsx_path)
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.sort_values("Date", ascending=False)
            
            # Clean up columns for display
            display_df = df.drop(columns=["Number"], errors='ignore')
            display_df = display_df.copy()
            display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
            
            # Create data table
            table = dash_table.DataTable(
                columns=[{"name": col, "id": col} for col in display_df.columns],
                data=display_df.to_dict("records"),
                sort_action="native",
                filter_action="native",
                page_size=25,
                style_table={"overflowX": "auto"},
                style_header={
                    "backgroundColor": self.colors["card_bg"],
                    "color": self.colors["text_primary"],
                    "fontWeight": "bold",
                    "textAlign": "center"
                },
                style_cell={
                    "backgroundColor": self.colors["background"],
                    "color": self.colors["text_primary"],
                    "textAlign": "left",
                    "padding": "12px",
                    "border": f"1px solid {self.colors['grid']}"
                },
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{Direction} = Buy'},
                        'backgroundColor': f'{self.colors["green"]}20',
                        'color': self.colors["green"],
                    },
                    {
                        'if': {'filter_query': '{Direction} = Sell'},
                        'backgroundColor': f'{self.colors["red"]}20',
                        'color': self.colors["red"],
                    }
                ]
            )
            
            # Get portfolio data for summary statistics
            portfolio = self.portfolio_service.get_portfolio_snapshot()
            
            # Create summary statistics using portfolio data
            total_trades = len(df)
            unique_tickers = df['Ticker'].nunique()
            total_invested = portfolio.total_metrics.invested  # Use calculated value
            
            summary_cards = html.Div([
                self.ui_factory.create_metric_card("Total Trades", str(total_trades)),
                self.ui_factory.create_metric_card("Unique Tickers", str(unique_tickers)),
                self.ui_factory.create_metric_card("Total Invested", f"${total_invested:.2f}"),
                self.ui_factory.create_metric_card(
                    "Date Range", 
                    f"{df['Date'].min().strftime('%b %Y')} - {df['Date'].max().strftime('%b %Y')}"
                )
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "flexWrap": "wrap",
                "marginBottom": "30px"
            })
            
            return html.Div([
                html.H2("Trading History", style={
                    "textAlign": "center",
                    "color": self.colors["accent"],
                    "marginBottom": "30px"
                }),
                
                summary_cards,
                
                html.Div([
                    table
                ], style={
                    **self.config.ui.card_style,
                    "padding": "20px"
                })
            ])
            
        except Exception as e:
            logger.error(f"Error rendering trades page: {e}")
            return html.Div([
                html.H3("Error Loading Trades", style={
                    "color": self.colors["red"],
                    "textAlign": "center"
                }),
                html.P(f"Could not load trades data: {str(e)}", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style=self.config.ui.card_style)

class FinancePage(BasePage):
    """Personal finances page."""
    
    def __init__(self, ui_factory: UIComponentFactory, config: Config):
        super().__init__(ui_factory)
        self.config = config
    
    def render(self) -> html.Div:
        """Render personal finance page."""
        try:
            # Use the existing finance_page module for main dashboard
            from services.finance_page import build_finance_page
            main_dashboard = build_finance_page(
                self.config.database.finance_xlsx_path,
                self.colors,
                self.config.ui.card_style
            )
            
            # Add individual charts section
            individual_charts = self._create_individual_charts()
            
            return html.Div([
                main_dashboard,
                html.Hr(style={
                    "margin": "40px 0",
                    "border": f"1px solid {self.colors['grid']}"
                }),
                individual_charts
            ])
            
        except ImportError as e:
            logger.error(f"Could not import finance_page module: {e}")
            return self._create_import_error()
        except Exception as e:
            logger.error(f"Error rendering finance page: {e}")
            return self._create_general_error(str(e))
    
    def _create_individual_charts(self) -> html.Div:
        """Create individual charts for income, expenses, and investments."""
        try:
            from services.finance_service import FinanceAnalysisService
            
            finance_service = FinanceAnalysisService(self.config)
            df, month_columns = finance_service.load_finance_data()
            income_data, expenses_data, investments_data = finance_service.extract_financial_data(df, month_columns)
            
            # Create charts
            income_chart = finance_service.create_income_chart(income_data, month_columns, self.colors)
            expenses_chart = finance_service.create_expenses_chart(expenses_data, month_columns, self.colors)
            investments_chart = finance_service.create_investments_chart(investments_data, month_columns, self.colors)
            
            return html.Div([
                html.H3("Detailed Analysis", style={
                    "textAlign": "center",
                    "color": self.colors["accent"],
                    "marginBottom": "30px"
                }),
                
                # Income Chart
                html.Div([
                    self.ui_factory.create_chart_container(income_chart)
                ], style={"marginBottom": "30px"}),
                
                # Expenses Chart
                html.Div([
                    self.ui_factory.create_chart_container(expenses_chart)
                ], style={"marginBottom": "30px"}),
                
                # Investments Chart
                html.Div([
                    self.ui_factory.create_chart_container(investments_chart)
                ], style={"marginBottom": "30px"})
            ])
            
        except Exception as e:
            logger.error(f"Error creating individual charts: {e}")
            return html.Div([
                html.H3("Individual Charts Error", style={
                    "color": self.colors["red"],
                    "textAlign": "center"
                }),
                html.P(f"Could not load individual charts: {str(e)}", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style=self.config.ui.card_style)
    
    def _create_import_error(self) -> html.Div:
        """Create import error message."""
        return html.Div([
            html.H2("📊 Personal Finances Dashboard", style={
                "textAlign": "center", 
                "color": self.colors["accent"], 
                "marginBottom": "30px"
            }),
            html.Div([
                html.H4("Finance Module Not Available", style={"color": self.colors["red"]}),
                html.P("The finance page module could not be loaded.", style={
                    "color": self.colors["text_secondary"]
                }),
                html.P("Please ensure services/finance_page.py exists and is properly configured.", style={
                    "color": self.colors["text_secondary"]
                })
            ], style=self.config.ui.card_style)
        ])
    
    def _create_general_error(self, error_msg: str) -> html.Div:
        """Create general error message."""
        return html.Div([
            html.H2("📊 Personal Finances Dashboard", style={
                "textAlign": "center", 
                "color": self.colors["accent"], 
                "marginBottom": "30px"
            }),
            html.Div([
                html.H4("Error Loading Finance Data", style={"color": self.colors["red"]}),
                html.P(f"An error occurred: {error_msg}", style={
                    "color": self.colors["text_secondary"]
                })
            ], style=self.config.ui.card_style)
        ])

class SettingsPage(BasePage):
    """Application settings page."""
    
    def __init__(self, ui_factory: UIComponentFactory, config: Config):
        super().__init__(ui_factory)
        self.config = config
    
    def render(self) -> html.Div:
        """Render settings page."""
        try:
            return html.Div([
                # User Profile Section
                self._create_user_profile_section(),
                
                # Application Settings Section
                self._create_app_settings_section(),
                
                # Data Settings Section
                self._create_data_settings_section(),
                
                # About Section
                self._create_about_section()
            ])
            
        except Exception as e:
            logger.error(f"Error rendering settings page: {e}")
            return self._create_error_message(str(e))
    
    def _create_user_profile_section(self) -> html.Div:
        """Create user profile settings section."""
        return html.Div([
            html.H3("User Profile", style={
                "color": self.colors["accent"],
                "marginBottom": "20px"
            }),
            
            html.Div([
                # Profile Picture
                html.Div([
                    html.Img(
                        src="/assets/PATRICK.png",
                        style={
                            "width": "80px",
                            "height": "80px",
                            "borderRadius": "50%",
                            "border": f"3px solid {self.colors['accent']}",
                            "marginBottom": "15px"
                        }
                    ),
                    html.H4("Andreas Papathanasiou", style={
                        "color": self.colors["text_primary"],
                        "margin": "0"
                    }),
                    html.P("Portfolio Investor", style={
                        "color": self.colors["text_secondary"],
                        "margin": "5px 0 0 0"
                    })
                ], style={
                    "textAlign": "center",
                    "marginBottom": "20px"
                }),
                
                # Profile Stats
                html.Div([
                    self.ui_factory.create_metric_card("Member Since", "2025"),
                    self.ui_factory.create_metric_card("Total Trades", "150+"),
                    self.ui_factory.create_metric_card("Active Positions", "3")
                ], style={
                    "display": "flex",
                    "justifyContent": "center",
                    "flexWrap": "wrap"
                })
            ])
        ], style={
            **self.config.ui.card_style,
            "marginBottom": "30px"
        })
    
    def _create_app_settings_section(self) -> html.Div:
        """Create application settings section."""
        return html.Div([
            html.H3("Application Settings", style={
                "color": self.colors["accent"],
                "marginBottom": "20px"
            }),
            
            html.Div([
                # Theme Settings
                html.Div([
                    html.H5("Theme", style={"color": self.colors["text_primary"]}),
                    html.P("Dark Theme (Active)", style={
                        "color": self.colors["text_secondary"],
                        "margin": "10px 0"
                    })
                ], style={"marginBottom": "20px"}),
                
                # Currency Settings
                html.Div([
                    html.H5("Currency", style={"color": self.colors["text_primary"]}),
                    html.P("USD ($)", style={
                        "color": self.colors["text_secondary"],
                        "margin": "10px 0"
                    })
                ], style={"marginBottom": "20px"}),
                
                # Refresh Rate
                html.Div([
                    html.H5("Data Refresh", style={"color": self.colors["text_primary"]}),
                    html.P("Real-time updates enabled", style={
                        "color": self.colors["text_secondary"],
                        "margin": "10px 0"
                    })
                ])
            ])
        ], style={
            **self.config.ui.card_style,
            "marginBottom": "30px"
        })
    
    def _create_data_settings_section(self) -> html.Div:
        """Create data settings section."""
        return html.Div([
            html.H3("Data Sources", style={
                "color": self.colors["accent"],
                "marginBottom": "20px"
            }),
            
            html.Div([
                html.Div([
                    html.H5("Market Data", style={"color": self.colors["text_primary"]}),
                    html.P("Yahoo Finance API", style={
                        "color": self.colors["text_secondary"],
                        "margin": "10px 0"
                    }),
                    html.Div("🟢 Connected", style={
                        "color": self.colors["green"],
                        "fontSize": "0.9rem"
                    })
                ], style={"marginBottom": "20px"}),
                
                html.Div([
                    html.H5("Portfolio Data", style={"color": self.colors["text_primary"]}),
                    html.P("Local Excel Files", style={
                        "color": self.colors["text_secondary"],
                        "margin": "10px 0"
                    }),
                    html.Div("🟢 Loaded", style={
                        "color": self.colors["green"],
                        "fontSize": "0.9rem"
                    })
                ])
            ])
        ], style={
            **self.config.ui.card_style,
            "marginBottom": "30px"
        })
    
    def _create_about_section(self) -> html.Div:
        """Create about section."""
        return html.Div([
            html.H3("About", style={
                "color": self.colors["accent"],
                "marginBottom": "20px"
            }),
            
            html.Div([
                html.P("Portfolio Tracker Dashboard v1.0", style={
                    "color": self.colors["text_primary"],
                    "fontWeight": "bold",
                    "marginBottom": "10px"
                }),
                html.P("A comprehensive investment tracking and analysis platform.", style={
                    "color": self.colors["text_secondary"],
                    "marginBottom": "20px"
                }),
                html.Div([
                    html.Span("Built with: ", style={"color": self.colors["text_secondary"]}),
                    html.Span("Python • Dash • Plotly • Pandas", style={
                        "color": self.colors["accent"],
                        "fontWeight": "bold"
                    })
                ])
            ])
        ], style=self.config.ui.card_style)
    
    def _create_error_message(self, error: str) -> html.Div:
        """Create error message display."""
        return html.Div([
            html.H3("Error Loading Settings", style={
                "color": self.colors["red"],
                "textAlign": "center"
            }),
            html.P(f"An error occurred: {error}", style={
                "textAlign": "center",
                "color": self.colors["text_secondary"]
            })
        ], style=self.config.ui.card_style)

class PageFactory:
    """Factory for creating dashboard pages with lazy loading."""
    
    def __init__(self, portfolio_service: PortfolioService, ui_factory: UIComponentFactory, config: Config):
        self.portfolio_service = portfolio_service
        self.ui_factory = ui_factory
        self.config = config
        
        # Page registry - lazy initialization to avoid circular imports
        self._page_registry = {
            "tickers": self._create_tickers_page,
            "portfolio": self._create_portfolio_page,
            "trades": self._create_trades_page,
            "finances": self._create_finances_page,
            "settings": self._create_settings_page
        }
        
        # Cache for instantiated pages
        self._page_cache = {}
        
        logger.info(f"PageFactory initialized with {len(self._page_registry)} page types")
    
    def create_page(self, page_name: str) -> BasePage:
        """Create page instance by name with caching."""
        if page_name not in self._page_registry:
            available_pages = list(self._page_registry.keys())
            raise ValueError(f"Unknown page: {page_name}. Available: {available_pages}")
        
        # Return cached page if exists
        if page_name in self._page_cache:
            logger.debug(f"Returning cached page: {page_name}")
            return self._page_cache[page_name]
        
        # Create new page instance
        logger.debug(f"Creating new page instance: {page_name}")
        page_instance = self._page_registry[page_name]()
        
        # Cache for future use
        self._page_cache[page_name] = page_instance
        
        return page_instance
    
    def _create_tickers_page(self) -> TickersPage:
        """Create tickers analysis page."""
        return TickersPage(self.portfolio_service, self.ui_factory)
    
    def _create_portfolio_page(self) -> PortfolioPage:
        """Create portfolio overview page."""
        return PortfolioPage(self.portfolio_service, self.ui_factory)
    
    def _create_trades_page(self) -> TradesPage:
        """Create trades history page."""
        return TradesPage(self.portfolio_service, self.ui_factory)
    
    def _create_finances_page(self) -> FinancePage:
        """Create personal finances page."""
        return FinancePage(self.ui_factory, self.config)
    
    def _create_settings_page(self) -> SettingsPage:
        """Create application settings page."""
        return SettingsPage(self.ui_factory, self.config)
    
    def get_available_pages(self) -> List[str]:
        """Get list of available page names."""
        return list(self._page_registry.keys())
    
    def register_page(self, name: str, page_factory_func) -> None:
        """Register a new page type dynamically."""
        if name in self._page_registry:
            logger.warning(f"Overriding existing page registration: {name}")
        
        self._page_registry[name] = page_factory_func
        
        # Clear cache for this page if it exists
        if name in self._page_cache:
            del self._page_cache[name]
        
        logger.info(f"Registered new page type: {name}")
    
    def unregister_page(self, name: str) -> bool:
        """Unregister a page type."""
        if name not in self._page_registry:
            logger.warning(f"Attempted to unregister non-existent page: {name}")
            return False
        
        del self._page_registry[name]
        
        # Clear cache
        if name in self._page_cache:
            del self._page_cache[name]
        
        logger.info(f"Unregistered page type: {name}")
        return True
    
    def clear_cache(self) -> None:
        """Clear all cached page instances."""
        cleared_count = len(self._page_cache)
        self._page_cache.clear()
        logger.info(f"Cleared {cleared_count} cached page instances")
    
    def get_cache_status(self) -> dict:
        """Get cache status information."""
        return {
            "cached_pages": list(self._page_cache.keys()),
            "available_pages": list(self._page_registry.keys()),
            "cache_size": len(self._page_cache),
            "registry_size": len(self._page_registry)
        }
