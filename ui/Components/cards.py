from datetime import datetime
from dash import html, dash_table, dcc
from typing import Optional, List

from models.portfolio import PerformanceMetrics, PortfolioSnapshot, TickerData


class CardComponentsMixin:
    """Reusable metric and info card components."""

    def create_metric_card(
        self,
        title: str,
        value: str,
        value_color: Optional[str] = None,
        subtitle: Optional[str] = None,
    ) -> html.Div:
        """Create a standardized metric card."""
        text_color = value_color or self.colors["text_primary"]

        content = [
            html.H6(
                title,
                style={
                    "color": self.colors["text_secondary"],
                    "marginBottom": "10px",
                    "fontSize": "0.9rem",
                },
            ),
            html.H4(
                value,
                style={"margin": "0", "color": text_color, "fontWeight": "bold"},
            ),
        ]

        if subtitle:
            content.append(
                html.P(
                    subtitle,
                    style={
                        "margin": "5px 0 0 0",
                        "color": self.colors["text_secondary"],
                        "fontSize": "0.8rem",
                    },
                )
            )

        return html.Div(content, style=self.card_style)

    def create_enhanced_metric_card(
        self,
        title: str,
        value: str,
        value_color: Optional[str] = None,
        icon_type: str = "emoji",
        is_positive: Optional[bool] = None,
    ) -> html.Div:
        """Create an enhanced metric card with icons and visual elements."""
        text_color = value_color or self.colors["text_primary"]
        
        # Create icon element based on type
        icon_element = self._create_metric_icon(icon_type, is_positive, value_color)
        
        content = [
            html.Div([
                html.H6(
                    title,
                    style={
                        "color": self.colors["text_secondary"],
                        "marginBottom": "8px",
                        "fontSize": "0.9rem",
                        "fontWeight": "500",
                        "position": "relative",
                        "zIndex": "1",
                        "transition": "all 0.3s ease",
                    },
                ),
                html.Div([
                    html.Div(
                        icon_element,
                        style={
                            "position": "absolute",
                            "top": "50%",
                            "left": "15px",
                            "transform": "translateY(-50%)",
                            "zIndex": "1",
                        }
                    ),
                    html.Div([
                        html.H4(
                            value,
                            style={
                                "margin": "0",
                                "color": text_color,
                                "fontWeight": "bold",
                                "fontSize": "1.4rem",
                                "position": "relative",
                                "zIndex": "1",
                                "transition": "all 0.3s ease",
                            },
                        ),
                    ], style={
                        "textAlign": "center",
                        "width": "100%",
                        "paddingLeft": "0",
                        "paddingRight": "0",
                    })
                ], style={
                    "position": "relative",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "width": "100%",
                    "minHeight": "50px",
                })
            ])
        ]

        return html.Div(
            content,
            className="metric-card-enhanced side-metric-card",
            style={
                **self.card_style,
                "flex": "1 1 0px",
                "minWidth": "220px",
                "maxWidth": "309px",
                "margin": "0",
                "padding": "22px",
                "textAlign": "center",
                "fontSize": "1.1em",
                "cursor": "pointer",
                "transition": "all 0.3s ease",
                "position": "relative",
                "overflow": "hidden",
            }
        )

    def _create_metric_icon(self, icon_type: str, is_positive: Optional[bool], color: str) -> html.Div:
        """Create icon element for metric cards."""
        if icon_type is None:
            return html.Div()
        

        if icon_type == "cash":
            return html.Div(className="icon-cash", style={
                "width": "32px",
                "height": "32px",
                "margin": "0 auto 5px auto"
            })
        elif icon_type == "portfolio":
            return html.Div(className="icon-portfolio", style={
                "width": "32px", 
                "height": "32px",
                "margin": "0 auto 5px auto"
            })
        elif icon_type == 'bag':
            return html.Div(className="icon-bag", style={
                "width": "32px",            
                "height": "32px",
                "margin": "0 auto 5px auto"
            })
        elif icon_type == "profit-loss":
            return self._create_profit_loss_icon(is_positive, color)
        elif icon_type == "percentage":
            return self._create_percentage_icon(is_positive, color)
        elif icon_type == "average":
            return html.Div(className="icon-average", style={
                "width": "32px",
                "height": "32px",
                "margin": "0 auto 5px auto"
            })

    def _create_profit_loss_icon(self, is_positive: bool, color: str) -> html.Div:
        """Create professional profit/loss icon."""
        direction = "positive" if is_positive else "negative"
        
        return html.Div(className=f"profit-loss-{direction}", style={
            "width": "32px",
            "height": "32px",
            "position": "relative"
        })

    def _create_percentage_icon(self, is_positive: bool, color: str) -> html.Div:
        """Create professional percentage icon for return metric."""
        direction = "positive" if is_positive else "negative"
        return html.Div(className=f"percentage-{direction}", style={
            "width": "32px",
            "height": "32px",
            "position": "relative"
        })


    def create_enhanced_performance_cards(
        self, metrics: PerformanceMetrics, show_entry_price: bool = True
    ) -> html.Div:
        """Create enhanced performance metric cards with icons and animations."""
        profit_color = self.colors["green"] if metrics.is_profitable else self.colors["red"]
        return_color = (
            self.colors["green"] if metrics.return_percentage >= 0 else self.colors["red"]
        )

        cards = []
        if show_entry_price and metrics.average_buy_price > 0:
            cards.append(
                self.create_enhanced_metric_card(
                    "Average Entry Price",
                    f"${metrics.average_buy_price:.2f}",
                    self.colors["text_primary"],
                    "average"
                )
            )

        
        cards.append(
            self.create_enhanced_metric_card(
                "Invested", 
                f"${metrics.invested:.2f}",
                self.colors["text_primary"],
                "cash"
            )
        )

        cards.extend([
            self.create_enhanced_metric_card(
                "Current Value",
                f"${metrics.current_value:.2f}",
                self.colors["accent"],
                "portfolio"
            ),
            self.create_enhanced_metric_card(
                "P&L",
                f"${metrics.profit_absolute:.2f}",
                profit_color,
                "profit-loss",
                metrics.is_profitable
            ),
            self.create_enhanced_metric_card(
                "Return",
                f"{metrics.return_percentage:.2f}%",
                return_color,
                "percentage",
                metrics.return_percentage >= 0
            ),
        ])

        return html.Div(
            cards,
            style={
                "display": "flex",
                "justifyContent": "center",
                "flexWrap": "wrap",
                "gap": "15px",
                "marginBottom": "20px",
            },
        )

    def create_portfolio_summary(self, portfolio: PortfolioSnapshot, include_usd: bool = False) -> html.Div:
        """Create dashboard summary section for the portfolio page."""
        # Calculate metrics with optional USD/EUR inclusion
        if include_usd:
            # Include USD/EUR in calculations
            equity_tickers = [t for t in portfolio.tickers if t.symbol != "USD/EUR"]
            usd_tickers = [t for t in portfolio.tickers if t.symbol == "USD/EUR"]
            
            total_invested = sum(t.metrics.invested for t in equity_tickers)
            total_current = sum(t.metrics.current_value for t in equity_tickers)
            total_profit = sum(t.metrics.profit_absolute for t in equity_tickers + usd_tickers)
        else:
            # Exclude USD/EUR from calculations (default behavior)
            total_invested = portfolio.total_metrics.invested
            total_current = portfolio.total_metrics.current_value
            total_profit = portfolio.total_metrics.profit_absolute
        
        return_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0.0
        is_profitable = total_profit >= 0
        
        return html.Div(
            [
                html.Div(
                    [
                        self.create_enhanced_metric_card(
                            "Invested",
                            f"${total_invested:.2f}",
                            self.colors["text_primary"],
                            "cash"
                        ),
                        self.create_enhanced_metric_card(
                            "Portfolio Value",
                            f"${total_current:.2f}",
                            self.colors["accent"],
                            "portfolio"
                        ),
                        self.create_enhanced_metric_card(
                            "P&L",
                            f"${total_profit:.2f}",
                            self.colors["green"] if is_profitable else self.colors["red"],
                            "profit-loss",
                            is_profitable
                        ),
                        self.create_enhanced_metric_card(
                            "Overall Return",
                            f"{return_pct:.2f}%",
                            self.colors["green"] if return_pct >= 0 else self.colors["red"],
                            "percentage",
                            return_pct >= 0
                        ),
                    ],
                    style={"display": "flex", "justifyContent": "center", "flexWrap": "wrap", "gap": "15px"},
                ),
            ]
        )

    def create_trades_summary_cards(self, total_trades: int, unique_tickers: int, total_invested: float, date_range: str) -> html.Div:
        """Create enhanced summary cards for trades page."""
        return html.Div(
            [
                self.create_enhanced_metric_card(
                    "Total Trades",
                    str(total_trades),
                    self.colors["text_primary"],
                    "portfolio"
                ),
                self.create_enhanced_metric_card(
                    "Unique Tickers",
                    str(unique_tickers),
                    self.colors["text_primary"],
                    "bag"
                ),
                self.create_enhanced_metric_card(
                    "Total Invested",
                    f"${total_invested:.2f}",
                    self.colors["text_primary"],
                    "cash"
                ),
                self.create_enhanced_metric_card(
                    "Date Range",
                    date_range,
                    self.colors["text_primary"]
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "center",
                "flexWrap": "wrap",
                "gap": "15px",
                "marginBottom": "30px",
            },
        )


    def create_enhanced_finance_metrics_cards(self, metrics: dict) -> html.Div:
        """Create enhanced metrics cards for finance dashboard."""
        return html.Div(
            [
                self.create_enhanced_metric_card(
                    "Avg Monthly Income",
                    f"€{metrics['avg_income']:,.2f}",
                    self.colors["green"],
                    "profit-loss",
                    True
                ),
                self.create_enhanced_metric_card(
                    "Avg Monthly Expenses",
                    f"€{metrics['avg_expenses']:,.2f}",
                    self.colors["red"],
                    "profit-loss",
                    False
                ),
                self.create_enhanced_metric_card(
                    "Avg Monthly Investments",
                    f"€{metrics['avg_investments']:,.2f}",
                    self.colors["accent"],
                    "portfolio"
                ),
                self.create_enhanced_metric_card(
                    "Last Updated",
                    datetime.now().strftime("%d %b %Y"),
                    self.colors["text_primary"],
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "center",
                "flexWrap": "wrap",
                "gap": "15px",
                "marginBottom": "30px",
            },
        )


    def create_finance_error_display(
        self, error_message: str, file_path: str
    ) -> html.Div:
        """Create error display for finance page."""
        return html.Div(
            [
                html.H2(
                    "📊 Personal Finances Dashboard",
                    style={
                        "textAlign": "center",
                        "color": self.colors["accent"],
                        "marginBottom": "30px",
                    },
                ),
                html.Div(
                    [
                        html.H4(
                            "Error Loading Finance Data",
                            style={"color": self.colors["red"]},
                        ),
                        html.P(error_message, style={"color": self.colors["text_primary"]}),
                        html.P(
                            f"Please ensure the file exists at: {file_path}",
                            style={"color": self.colors["text_secondary"]},
                        ),
                    ],
                    style=self.config.ui.card_style,
                ),
            ]
        )

    def create_finance_no_data_display(self) -> html.Div:
        """Create no data display for finance page."""
        return html.Div(
            [
                html.H2(
                    "📊 Personal Finances Dashboard",
                    style={
                        "textAlign": "center",
                        "color": self.colors["accent"],
                        "marginBottom": "30px",
                    },
                ),
                html.Div(
                    [
                        html.H4(
                            "No Data Available",
                            style={"color": self.colors["red"]},
                        ),
                        html.P(
                            "No valid month columns found for the specified time period.",
                            style={"color": self.colors["text_primary"]},
                        ),
                    ],
                    style=self.config.ui.card_style,
                ),
            ]
        )

    def create_ticker_trade_details(self, total_buy_orders: int, Quantity: int) -> html.Div:
        """Create trade details card for individual ticker analysis."""
        return html.Div(
            [
                html.H3(
                    "Trade Details",
                    style={
                        "color": self.colors["accent"],
                        "marginBottom": "20px",
                        "fontSize": "1.3rem",
                        "fontWeight": "600",
                        "textAlign": "center"
                    },
                ),
                html.Div(
                    [
                        # Total Buy Orders section
                        html.Div(
                            [
                                html.H6(
                                    "Total Buy Orders",
                                    style={
                                        "color": self.colors["text_secondary"],
                                        "marginBottom": "10px",
                                        "fontSize": "0.9rem",
                                        "textAlign": "center"
                                    },
                                ),
                                html.H4(
                                    f"{total_buy_orders}",
                                    style={
                                        "color": self.colors["text_primary"],
                                        "margin": "0",
                                        "fontSize": "1.5rem",
                                        "fontWeight": "bold",
                                        "textAlign": "center"
                                    },
                                ),
                            ],
                            style={
                                "flex": "1",
                                "minWidth": "200px",
                                "display": "flex",
                                "flexDirection": "column",
                                "alignItems": "center"
                            }
                        ),
                        # Total Invested section
                        html.Div(
                            [
                                html.H6(
                                    "Quantity",
                                    style={
                                        "color": self.colors["text_secondary"],
                                        "marginBottom": "10px",
                                        "fontSize": "0.9rem",
                                        "textAlign": "center"
                                    },
                                ),
                                html.H4(
                                    Quantity,
                                    style={
                                        "color": self.colors["text_primary"],
                                        "margin": "0",
                                        "fontSize": "1.5rem",
                                        "fontWeight": "bold",
                                        "textAlign": "center"
                                    },
                                ),
                            ],
                            style={
                                "flex": "1",
                                "minWidth": "200px",
                                "display": "flex",
                                "flexDirection": "column",
                                "alignItems": "center"
                            }
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "flexWrap": "wrap",
                        "gap": "30px",
                    },
                ),
            ],
            style={
                **self.card_style,
                "marginBottom": "20px",
                "padding": "20px",
            }
        )

    def create_recent_trade_card(self, date: str, trade_type: str, quantity: float, price: float) -> html.Div:
        """Create recent trade card for individual ticker analysis."""
        return html.Div(
            [
                html.H3(
                    "Recent Trade",
                    style={
                        "color": self.colors["accent"],
                        "marginBottom": "20px",
                        "fontSize": "1.3rem",
                        "fontWeight": "600",
                        "textAlign": "center"
                    },
                ),
                html.Div(
                    [
                        # Left column - Labels
                        html.Div(
                            [
                                html.Div("Date", style={
                                    "color": self.colors["text_secondary"],
                                    "fontSize": "1rem",
                                    "marginBottom": "15px",
                                    "fontWeight": "500"
                                }),
                                html.Div("Type", style={
                                    "color": self.colors["text_secondary"],
                                    "fontSize": "1rem",
                                    "marginBottom": "15px",
                                    "fontWeight": "500"
                                }),
                                html.Div("Quantity", style={
                                    "color": self.colors["text_secondary"],
                                    "fontSize": "1rem",
                                    "marginBottom": "15px",
                                    "fontWeight": "500"
                                }),
                                html.Div("Price", style={
                                    "color": self.colors["text_secondary"],
                                    "fontSize": "1rem",
                                    "fontWeight": "500"
                                }),
                            ],
                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "alignItems": "flex-end",
                                "paddingRight": "50px"
                            }
                        ),
                        # Right column - Values
                        html.Div(
                            [
                                html.Div(date, style={
                                    "color": self.colors["text_primary"],
                                    "fontSize": "1rem",
                                    "marginBottom": "15px",
                                    "fontWeight": "bold"
                                }),
                                html.Div(trade_type, style={
                                    "color": self.colors["green"] if trade_type.lower() == "buy" else self.colors["red"],
                                    "fontSize": "1rem",
                                    "marginBottom": "15px",
                                    "fontWeight": "bold"
                                }),
                                html.Div(f"{quantity:.2f}", style={
                                    "color": self.colors["text_primary"],
                                    "fontSize": "1rem",
                                    "marginBottom": "15px",
                                    "fontWeight": "bold"
                                }),
                                html.Div(f"${price:.2f}", style={
                                    "color": self.colors["text_primary"],
                                    "fontSize": "1rem",
                                    "fontWeight": "bold"
                                }),
                            ],
                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "alignItems": "flex-start",
                                "paddingLeft": "10px"
                            }
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "alignItems": "flex-start",
                        "gap": "100px",
                        "padding": "10px 0"
                    },
                ),
            ],
            style={
                **self.card_style,
                "marginBottom": "20px",
                "padding": "20px",
            }
        )

    def create_tickers_table(self, tickers: List[TickerData], total_portfolio_value: float, include_usd: bool = False) -> html.Div:
        """Create a comprehensive table displaying all traded tickers with their metrics.
        
        Args:
            tickers: List of TickerData objects with trade information
            total_portfolio_value: Total portfolio value for calculating share percentage
            exclude_usd: Whether to exclude USD/EUR ticker from the table
            
        Returns:
            html.Div containing the formatted ticker table
        """
        # Filter tickers based on exclude_usd flag
        filtered_tickers = [t for t in tickers if t.has_trades and (include_usd or t.symbol != "USD/EUR")]
        
        # Prepare data for table
        table_data = []
        for ticker in filtered_tickers:
            # Calculate share percentage (USD/EUR always shows 0%)
            if ticker.symbol == "USD/EUR":
                share_pct = 0.0
                qty = f"{ticker.total_shares:.2f}"
            else:
                share_pct = (ticker.metrics.current_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                qty = int(ticker.total_shares)
            
            table_data.append({
                "Ticker": ticker.symbol,
                "Quantity": qty,
                "Entry Price": f"${ticker.metrics.average_buy_price:.2f}",
                "Price": f"${ticker.latest_price:.2f}",
                "Value": f"${ticker.metrics.current_value:.2f}",
                "Share": f"{share_pct:.2f}%",
                "Profit": f"${ticker.metrics.profit_absolute:.2f}",
                "Growth": f"{ticker.metrics.return_percentage:.2f}%",
                # Hidden columns for conditional formatting
                "_profit_num": ticker.metrics.profit_absolute,
                "_growth_num": ticker.metrics.return_percentage,
            })
        
        if not table_data:
            return html.Div(
                html.P(
                    "No tickers with trades found",
                    style={
                        "textAlign": "center",
                        "color": self.colors["text_secondary"],
                        "padding": "20px"
                    }
                ),
                style=self.card_style
            )
        
        # Define columns (exclude hidden columns from display)
        display_columns = ["Ticker", "Quantity", "Entry Price", "Price", "Value", "Share", "Profit", "Growth"]
        
        table = dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in display_columns],
            data=table_data,
            sort_action="native",
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": self.colors["card_bg"],
                "color": self.colors["text_primary"],
                "fontWeight": "bold",
                "textAlign": "center",
                "fontSize": "1rem",
                "padding": "15px"
            },
            style_cell={
                "backgroundColor": self.colors["background"],
                "color": self.colors["text_primary"],
                "textAlign": "center",
                "padding": "14px",
                "border": f"1px solid {self.colors['grid']}",
                "fontSize": "0.95rem"
            },
            style_data_conditional=[
                # Positive Profit - green text
                {
                    'if': {
                        'filter_query': '{_profit_num} > 0',
                        'column_id': 'Profit'
                    },
                    'color': self.colors["green"],
                    'fontWeight': 'bold'
                },
                # Negative Profit - red text
                {
                    'if': {
                        'filter_query': '{_profit_num} < 0',
                        'column_id': 'Profit'
                    },
                    'color': self.colors["red"],
                    'fontWeight': 'bold'
                },
                # Positive Growth - green text
                {
                    'if': {
                        'filter_query': '{_growth_num} > 0',
                        'column_id': 'Growth'
                    },
                    'color': self.colors["green"],
                    'fontWeight': 'bold'
                },
                # Negative Growth - red text
                {
                    'if': {
                        'filter_query': '{_growth_num} < 0',
                        'column_id': 'Growth'
                    },
                    'color': self.colors["red"],
                    'fontWeight': 'bold'
                },
                # Ticker column - accent color
                {
                    'if': {'column_id': 'Ticker'},
                    'color': self.colors["accent"],
                    'fontWeight': 'bold',
                    'fontSize': '1rem'
                }
            ]
        )
        
        return table
    
    def create_tickers_table_section(self, tickers: List[TickerData], total_portfolio_value: float) -> html.Div:
        """Create tickers table section with USD/EUR filter toggle.
        
        Args:
            tickers: List of TickerData objects with trade information
            total_portfolio_value: Total portfolio value for calculating share percentage
            
        Returns:
            html.Div containing the header, toggle button, and ticker table
        """
        return html.Div(
            [
                # Header and toggle button row
                html.Div([
                    html.H3(
                        "Portfolio Holdings",
                        style={
                            "color": self.colors["accent"],
                            "fontSize": "1.4rem",
                            "fontWeight": "600",
                            "margin": "0"
                        }
                    ),
                    html.Div([
                        html.Label(
                            "Include USD/EUR",
                            style={
                                "color": self.colors["text_secondary"],
                                "fontSize": "0.9rem",
                                "marginRight": "10px"
                            }
                        ),
                        dcc.Checklist(
                            id="include-usd-toggle",
                            options=[{"label": "", "value": "include"}],
                            value=[],
                            style={
                                "display": "inline-block"
                            },
                            inputStyle={
                                "marginRight": "0px",
                                "cursor": "pointer"
                            },
                            labelStyle={
                                "cursor": "pointer"
                            }
                        )
                    ], style={
                        "display": "flex",
                        "alignItems": "center"
                    })
                ], style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "marginBottom": "20px",
                    "flexWrap": "wrap",
                    "gap": "15px"
                }),
                # Table content (will be updated by callback)
                html.Div(
                    id="tickers-table-content",
                    children=self.create_tickers_table(tickers, total_portfolio_value, include_usd=False)
                ),
                # Store for portfolio data
                dcc.Store(id="portfolio-tickers-data", data={
                    "tickers": [
                        {
                            "symbol": t.symbol,
                            "has_trades": t.has_trades,
                            "total_shares": t.total_shares,
                            "average_buy_price": t.metrics.average_buy_price,
                            "latest_price": t.latest_price,
                            "current_value": t.metrics.current_value,
                            "profit_absolute": t.metrics.profit_absolute,
                            "return_percentage": t.metrics.return_percentage
                        } for t in tickers if t.has_trades 
                    ],
                    "total_portfolio_value": total_portfolio_value
                })
            ],
            style={
                **self.card_style,
                "padding": "25px",
                "marginBottom": "20px"
            }
        )
