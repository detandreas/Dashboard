from datetime import datetime
from dash import html, dcc
import plotly.graph_objects as go
import logging

from models.portfolio import PortfolioSnapshot

logger = logging.getLogger(__name__)


class PortfolioComponentsMixin:
    """Components specific to portfolio pages."""

    def create_portfolio_summary(self, portfolio: PortfolioSnapshot) -> html.Div:
        """Create dashboard summary section for the portfolio page."""
        return html.Div(
            [
                html.H2(
                    "Portfolio Dashboard",
                    style={
                        "textAlign": "center",
                        "color": self.colors["accent"],
                        "marginTop": "10px",
                        "marginBottom": "20px",
                    },
                ),
                html.Div(
                    [
                        self.create_metric_card(
                            "Last Updated", datetime.now().strftime("%d %b %Y, %H:%M")
                        ),
                        self.create_metric_card(
                            "Invested",
                            f"${portfolio.total_metrics.invested:.2f}",
                            self.colors["text_primary"],
                        ),
                        self.create_metric_card(
                            "Total Portfolio Value",
                            f"${portfolio.total_metrics.current_value:.2f}",
                            self.colors["accent"],
                        ),
                        self.create_metric_card(
                            "Total P&L",
                            f"${portfolio.total_metrics.profit_absolute:.2f}",
                            self.colors["green"]
                            if portfolio.total_metrics.is_profitable
                            else self.colors["red"],
                        ),
                        self.create_metric_card(
                            "Overall Return",
                            f"{portfolio.total_metrics.return_percentage:.2f}%",
                            self.colors["green"]
                            if portfolio.total_metrics.return_percentage >= 0
                            else self.colors["red"],
                        ),
                    ],
                    style={"display": "flex", "justifyContent": "center", "flexWrap": "wrap"},
                ),
            ]
        )

    def create_portfolio_composition(self, portfolio: PortfolioSnapshot) -> html.Div:
        """Create portfolio composition pie chart with breakdown."""
        try:
            invested_tickers = [
                ticker
                for ticker in portfolio.tickers
                if ticker.metrics.invested > 0 and ticker.symbol not in ["USD", "EUR", "USD/EUR"]
            ]

            if not invested_tickers:
                return html.Div(
                    [
                        html.H3(
                            "Portfolio Composition",
                            style={"textAlign": "center", "color": self.colors["text_secondary"]},
                        ),
                        html.P(
                            "No investment data available",
                            style={"textAlign": "center", "color": self.colors["text_secondary"]},
                        ),
                    ],
                    style=self.config.ui.card_style,
                )

            symbols = [ticker.symbol for ticker in invested_tickers]
            values = [ticker.metrics.invested for ticker in invested_tickers]
            percentages = [value / sum(values) * 100 for value in values]
            total_portfolio_value = sum(
                ticker.metrics.current_value for ticker in invested_tickers
            )

            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=symbols,
                        values=values,
                        hole=0.4,
                        textinfo="label+percent",
                        textposition="auto",
                        hovertemplate='<b>%{label}</b><br>'
                        + 'Invested: $%{value:,.2f}<br>'
                        + 'Percentage: %{percent}<br>'
                        + '<extra></extra>',
                        marker=dict(
                            colors=[
                                "#1f77b4",
                                "#ff7f0e",
                                "#2ca02c",
                                "#d62728",
                                "#9467bd",
                                "#8c564b",
                            ],
                            line=dict(color="#000000", width=2),
                        ),
                    )
                ]
            )

            fig.add_annotation(
                text=f"<br>${total_portfolio_value:,.2f}",
                x=0.5,
                y=0.5,
                font=dict(size=16, color=self.colors["text_primary"]),
                showarrow=False,
                align="center",
            )

            fig.update_layout(
                height=400,
                template="plotly_dark",
                title={
                    "text": "Portfolio Composition",
                    "font": {"size": 18, "color": self.colors["text_primary"]},
                    "y": 0.95,
                    "x": 0.5,
                    "xanchor": "center",
                    "yanchor": "top",
                },
                plot_bgcolor=self.colors["card_bg"],
                paper_bgcolor=self.colors["card_bg"],
                font=dict(color=self.colors["text_primary"]),
                showlegend=False,
                margin=dict(l=20, r=20, t=60, b=20),
            )

            breakdown_items = []
            for ticker, percentage, value in zip(symbols, percentages, values):
                breakdown_items.append(
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span(
                                        ticker,
                                        style={
                                            "fontWeight": "bold",
                                            "fontSize": "1.1rem",
                                            "color": self.colors["accent"],
                                        },
                                    ),
                                    html.Span(
                                        f"{percentage:.1f}%",
                                        style={
                                            "float": "right",
                                            "fontWeight": "bold",
                                            "color": self.colors["text_primary"],
                                        },
                                    ),
                                ],
                                style={"marginBottom": "5px"},
                            ),
                            html.Div(
                                f"${value:,.2f}",
                                style={
                                    "color": self.colors["text_secondary"],
                                    "fontSize": "0.9rem",
                                },
                            ),
                        ],
                        style={
                            "padding": "15px",
                            "marginBottom": "10px",
                            "backgroundColor": self.colors["background"],
                            "borderRadius": "8px",
                            "border": f"1px solid {self.colors['grid']}",
                        },
                    )
                )

            return html.Div(
                [
                    html.H3(
                        "Portfolio Composition",
                        style={
                            "textAlign": "center",
                            "color": self.colors["accent"],
                            "marginBottom": "20px",
                        },
                    ),
                    html.Div(
                        [
                            html.Div(
                                [dcc.Graph(figure=fig)],
                                style={
                                    "width": "60%",
                                    "display": "inline-block",
                                    "verticalAlign": "top",
                                },
                            ),
                            html.Div(
                                [
                                    html.H4(
                                        "Investment Breakdown",
                                        style={
                                            "color": self.colors["text_primary"],
                                            "marginBottom": "20px",
                                            "textAlign": "center",
                                        },
                                    ),
                                    html.Div(breakdown_items),
                                ],
                                style={
                                    "width": "38%",
                                    "display": "inline-block",
                                    "verticalAlign": "top",
                                    "paddingLeft": "20px",
                                },
                            ),
                        ],
                        style={"width": "100%"},
                    ),
                ],
                style={**self.config.ui.card_style, "marginBottom": "30px"},
            )

        except Exception as e:
            logger.error("Error creating portfolio composition: %s", e)
            return html.Div(
                [
                    html.H3(
                        "Portfolio Composition",
                        style={"color": self.colors["red"], "textAlign": "center"},
                    ),
                    html.P(
                        f"Error loading composition: {str(e)}",
                        style={"textAlign": "center", "color": self.colors["text_secondary"]},
                    ),
                ],
                style=self.config.ui.card_style,
            )


