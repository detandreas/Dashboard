from datetime import datetime
from dash import html, dcc
import plotly.graph_objects as go
from typing import Optional, List, Dict
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

    def create_goal_card(
        self, goals_service, portfolio_value: float
    ) -> Optional[html.Div]:
        """Create goal progress card for portfolio page."""
        if not goals_service.has_active_goal():
            return None

        try:
            progress_data = goals_service.calculate_progress(portfolio_value)
            if not progress_data:
                return None

            return html.Div(
                [
                    html.Div(
                        [
                            html.H4(
                                "Portfolio Value Goal",
                                style={"color": self.colors["accent"], "margin": "0", "flex": "1"},
                            ),
                            html.Div(
                                [
                                    html.Button(
                                        "Overall",
                                        id="goal-view-overall",
                                        className="goal-view-btn active",
                                        n_clicks=0,
                                    ),
                                    html.Button(
                                        "Next",
                                        id="goal-view-next",
                                        className="goal-view-btn",
                                        n_clicks=0,
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "backgroundColor": self.colors["background"],
                                    "borderRadius": "6px",
                                    "padding": "2px",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                            "marginBottom": "20px",
                        },
                    ),
                    html.Div(
                        id="goal-progress-container",
                        children=[
                            self._create_progress_visualization(progress_data, "overall")
                        ],
                    ),
                    dcc.Store(id="goal-view-mode", data="overall"),
                    dcc.Store(id="goal-progress-data", data=progress_data),
                ],
                style={**self.config.ui.card_style, "marginBottom": "30px"},
            )

        except Exception as e:
            logger.error("Error creating goal card: %s", e)
            return None

    def _create_progress_visualization(
        self, progress_data: Dict, view_mode: str
    ) -> html.Div:
        """Create progress bar visualization."""
        milestones = progress_data["milestones"]
        current_value = progress_data["current_value"]

        if view_mode == "overall":
            return self._create_overall_progress(progress_data, milestones, current_value)
        return self._create_next_milestone_progress(progress_data)

    def _create_overall_progress(
        self, progress_data: Dict, milestones: List[Dict], current_value: float
    ) -> html.Div:
        """Create overall progress visualization with milestone markers."""
        total_target = milestones[-1]["amount"]
        progress_percent = progress_data["overall"]["progress_percent"]

        markers = []
        for milestone in milestones:
            position = (milestone["amount"] / total_target) * 100
            is_reached = milestone["status"] == "reached"
            marker_color = (
                self.colors["green"] if is_reached else self.colors["text_secondary"]
            )
            markers.append(
                html.Div(
                    [
                        html.Div(
                            style={
                                "width": "12px",
                                "height": "12px",
                                "borderRadius": "50%",
                                "backgroundColor": marker_color,
                                "border": f"2px solid {self.colors['card_bg']}",
                                "position": "absolute",
                                "top": "-6px",
                                "left": "-6px",
                                "zIndex": "10",
                            }
                        ),
                        html.Div(
                            [
                                html.Div(
                                    f"${milestone['amount']:,.0f}",
                                    style={
                                        "fontSize": "0.8rem",
                                        "fontWeight": "bold",
                                        "color": marker_color,
                                    },
                                ),
                                html.Div(
                                    milestone["label"],
                                    style={
                                        "fontSize": "0.7rem",
                                        "color": self.colors["text_secondary"],
                                        "whiteSpace": "nowrap",
                                    },
                                ),
                            ],
                            style={
                                "position": "absolute",
                                "top": "20px",
                                "left": "50%",
                                "transform": "translateX(-50%)",
                                "textAlign": "center",
                                "minWidth": "60px",
                            },
                        ),
                    ],
                    style={
                        "position": "absolute",
                        "left": f"{position}%",
                        "transform": "translateX(-50%)",
                    },
                )
            )

        return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            style={
                                "width": "100%",
                                "height": "8px",
                                "backgroundColor": self.colors["grid"],
                                "borderRadius": "4px",
                                "position": "relative",
                            }
                        ),
                        html.Div(
                            style={
                                "width": f"{progress_percent}%",
                                "height": "8px",
                                "backgroundColor": self.colors["accent"],
                                "borderRadius": "4px",
                                "position": "absolute",
                                "top": "0",
                                "left": "0",
                                "transition": "width 0.3s ease",
                            }
                        ),
                        *markers,
                    ],
                    style={"position": "relative", "margin": "30px 0 50px 0"},
                ),
                html.Div(
                    progress_data["overall"]["text"],
                    style={
                        "textAlign": "center",
                        "color": self.colors["text_primary"],
                        "fontSize": "1.1rem",
                        "fontWeight": "500",
                    },
                ),
            ]
        )

    def _create_next_milestone_progress(self, progress_data: Dict) -> html.Div:
        """Create next milestone progress visualization."""
        next_data = progress_data["next_milestone"]
        progress_percent = next_data["progress_percent"]

        return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            style={
                                "width": "100%",
                                "height": "12px",
                                "backgroundColor": self.colors["grid"],
                                "borderRadius": "6px",
                                "position": "relative",
                            }
                        ),
                        html.Div(
                            style={
                                "width": f"{progress_percent}%",
                                "height": "12px",
                                "backgroundColor": self.colors["green"],
                                "borderRadius": "6px",
                                "position": "absolute",
                                "top": "0",
                                "left": "0",
                                "transition": "width 0.3s ease",
                            }
                        ),
                    ],
                    style={"position": "relative", "margin": "20px 0"},
                ),
                html.Div(
                    next_data["text"],
                    style={
                        "textAlign": "center",
                        "color": self.colors["text_primary"],
                        "fontSize": "1.1rem",
                        "fontWeight": "500",
                    },
                ),
            ]
        )
