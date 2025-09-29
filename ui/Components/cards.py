from datetime import datetime
from dash import html
from typing import Optional

from models.portfolio import PerformanceMetrics, PortfolioSnapshot


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

    def create_portfolio_summary(self, portfolio: PortfolioSnapshot) -> html.Div:
        """Create dashboard summary section for the portfolio page."""
        return html.Div(
            [
                html.Div(
                    [
                        self.create_enhanced_metric_card(
                            "Invested",
                            f"${portfolio.total_metrics.invested:.2f}",
                            self.colors["text_primary"],
                            "cash"
                        ),
                        self.create_enhanced_metric_card(
                            "Portfolio Value",
                            f"${portfolio.total_metrics.current_value:.2f}",
                            self.colors["accent"],
                            "portfolio"
                        ),
                        self.create_enhanced_metric_card(
                            "P&L",
                            f"${portfolio.total_metrics.profit_absolute:.2f}",
                            self.colors["green"]
                            if portfolio.total_metrics.is_profitable
                            else self.colors["red"],
                            "profit-loss",
                            portfolio.total_metrics.is_profitable
                        ),
                        self.create_enhanced_metric_card(
                            "Overall Return",
                            f"{portfolio.total_metrics.return_percentage:.2f}%",
                            self.colors["green"]
                            if portfolio.total_metrics.return_percentage >= 0
                            else self.colors["red"],
                            "percentage",
                            portfolio.total_metrics.return_percentage >= 0
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
                    "cash"
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
