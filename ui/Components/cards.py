from datetime import datetime
from dash import html
from typing import Optional

from models.portfolio import PerformanceMetrics


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

    def create_performance_cards(
        self, metrics: PerformanceMetrics, show_entry_price: bool = True
    ) -> html.Div:
        """Create performance metric cards with invested amount."""
        profit_color = self.colors["green"] if metrics.is_profitable else self.colors["red"]
        return_color = (
            self.colors["green"] if metrics.return_percentage >= 0 else self.colors["red"]
        )

        cards = []
        cards.append(self.create_metric_card("Invested", f"${metrics.invested:.2f}"))

        if show_entry_price and metrics.average_buy_price > 0:
            cards.append(
                self.create_metric_card(
                    "Average Entry Price",
                    f"${metrics.average_buy_price:.2f}",
                )
            )

        cards.extend(
            [
                self.create_metric_card(
                    "Current Value",
                    f"${metrics.current_value:.2f}",
                    self.colors["accent"],
                ),
                self.create_metric_card(
                    "Profit/Loss",
                    f"${metrics.profit_absolute:.2f}",
                    profit_color,
                ),
                self.create_metric_card(
                    "Return",
                    f"{metrics.return_percentage:.2f}%",
                    return_color,
                ),
            ]
        )

        return html.Div(
            cards,
            style={
                "display": "flex",
                "justifyContent": "center",
                "flexWrap": "wrap",
                "marginBottom": "20px",
            },
        )

    def create_finance_metrics_cards(self, metrics: dict) -> html.Div:
        """Create metrics cards for finance dashboard."""
        return html.Div(
            [
                self.create_metric_card(
                    "Avg Monthly Income",
                    f"€{metrics['avg_income']:,.2f}",
                    self.colors["green"],
                ),
                self.create_metric_card(
                    "Avg Monthly Expenses",
                    f"€{metrics['avg_expenses']:,.2f}",
                    self.colors["red"],
                ),
                self.create_metric_card(
                    "Avg Monthly Investments",
                    f"€{metrics['avg_investments']:,.2f}",
                    self.colors["accent"],
                ),
                self.create_metric_card(
                    "Last Updated",
                    datetime.now().strftime("%d %b %Y"),
                    self.colors["text_primary"],
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "center",
                "flexWrap": "wrap",
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
