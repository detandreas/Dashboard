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

    def create_goal_progress_bar(self, goal_data: dict) -> html.Div:
        """Δημιουργεί goal progress bar με milestones."""
        if not goal_data.get("has_goal"):
            return self._create_no_goal_section()
        
        return html.Div([
            # Header με τίτλο και κουμπιά
            html.Div([
                html.H3("Investment Goals", style={
                    "color": self.colors["accent"],
                    "marginBottom": "10px",
                    "display": "inline-block"
                }),
                html.Div([
                    html.Button(
                        "Next Milestone", 
                        id="goal-view-toggle",
                        className="goal-button",
                        style={
                            "backgroundColor": self.colors["secondary"],
                            "color": "white",
                            "border": "none",
                            "padding": "8px 16px",
                            "borderRadius": "6px",
                            "marginRight": "10px",
                            "cursor": "pointer",
                            "fontSize": "0.9rem"
                        }
                    ),
                    html.Button(
                        "Delete Goal", 
                        id="delete-goal-btn",
                        className="goal-button danger",
                        style={
                            "backgroundColor": self.colors["red"],
                            "color": "white",
                            "border": "none",
                            "padding": "8px 16px",
                            "borderRadius": "6px",
                            "cursor": "pointer",
                            "fontSize": "0.9rem"
                        }
                    )
                ], style={"float": "right"})
            ], style={"marginBottom": "20px", "overflow": "hidden"}),
            
            # Goal info και progress
            html.Div(id="goal-progress-content", children=self._create_goal_progress_content(goal_data))
            
        ], style={**self.config.ui.card_style, "marginBottom": "30px"})

    def _create_no_goal_section(self) -> html.Div:
        """Δημιουργεί section όταν δεν υπάρχει ενεργός στόχος."""
        return html.Div([
            html.H3("Investment Goals", style={
                "color": self.colors["accent"],
                "marginBottom": "20px",
                "textAlign": "center"
            }),
            html.Div([
                html.P("No active investment goal set.", style={
                    "color": self.colors["text_secondary"],
                    "textAlign": "center",
                    "marginBottom": "20px",
                    "fontSize": "1.1rem"
                }),
                html.Button(
                    "🎯 Set New Goal",
                    id="add-goal-btn",
                    className="goal-button primary",
                    style={
                        "backgroundColor": self.colors["accent"],
                        "color": "white",
                        "border": "none",
                        "padding": "12px 24px",
                        "borderRadius": "8px",
                        "fontSize": "1rem",
                        "fontWeight": "bold",
                        "cursor": "pointer",
                        "display": "block",
                        "margin": "0 auto"
                    }
                )
            ])
        ], style={**self.config.ui.card_style, "marginBottom": "30px"})

    def _create_goal_progress_content(self, goal_data: dict) -> html.Div:
        """Δημιουργεί το περιεχόμενο του goal progress."""
        show_all = goal_data.get("show_all_milestones", True)
        
        if show_all:
            return self._create_full_progress_view(goal_data)
        else:
            return self._create_next_milestone_view(goal_data)

    def _create_full_progress_view(self, goal_data: dict) -> html.Div:
        """Δημιουργεί την πλήρη προβολή με segmented progress bar."""
        milestones = goal_data.get("milestones", [])
        current_value = goal_data.get("current_value", 0)
        
        if not milestones:
            return html.Div([
                html.P("No milestones defined", style={
                    "color": self.colors["text_secondary"],
                    "textAlign": "center"
                })
            ])
        
        # Segmented progress bar
        segmented_progress = self._create_segmented_progress_bar(milestones, current_value)
        
        # Milestones summary cards
        milestone_cards = []
        for i, milestone in enumerate(milestones):
            is_completed = milestone.get("status") == "completed"
            progress_to_milestone = min((current_value / milestone["amount"]) * 100, 100) if milestone["amount"] > 0 else 0
            
            milestone_cards.append(
                html.Div([
                    html.Div([
                        html.Div([
                            html.Span("✅" if is_completed else f"{i+1}", style={
                                "fontSize": "1.1rem",
                                "fontWeight": "bold",
                                "color": self.colors["green"] if is_completed else self.colors["text_primary"],
                                "marginRight": "10px",
                                "display": "inline-block",
                                "width": "25px",
                                "textAlign": "center"
                            }),
                            html.Span(milestone["label"], style={
                                "color": self.colors["text_primary"],
                                "fontWeight": "bold",
                                "fontSize": "1rem"
                            }),
                            html.Span(f"${milestone['amount']:,}", style={
                                "color": self.colors["accent"],
                                "fontWeight": "bold",
                                "float": "right"
                            })
                        ], style={"marginBottom": "8px"}),
                        
                        html.Div([
                            html.Span(f"{progress_to_milestone:.1f}%", style={
                                "color": self.colors["green"] if is_completed else self.colors["text_secondary"],
                                "fontSize": "0.9rem"
                            })
                        ])
                    ])
                ], style={
                    "padding": "12px 15px",
                    "marginBottom": "8px",
                    "backgroundColor": self.colors["green"] + "15" if is_completed else self.colors["background"],
                    "borderRadius": "8px",
                    "border": f"2px solid {self.colors['green'] if is_completed else self.colors['grid']}",
                    "transition": "all 0.3s ease"
                })
            )
        
        return html.Div([
            segmented_progress
        ])
    
    def _create_segmented_progress_bar(self, milestones: list, current_value: float) -> html.Div:
        """Δημιουργεί segmented progress bar με markers."""
        if not milestones:
            return html.Div()
        
        # Υπολογισμός positions για τα markers
        max_amount = max(milestone["amount"] for milestone in milestones)
        current_progress = min((current_value / max_amount) * 100, 100)
        
        # Δημιουργία markers
        markers = []
        segments = []
        
        for i, milestone in enumerate(milestones):
            position = (milestone["amount"] / max_amount) * 100
            is_completed = milestone.get("status") == "completed"
            is_current = current_value >= milestone["amount"]
            
            # Marker
            marker_left = position if i != len(milestones) - 1 else (position if position <= 98 else 99)
            if i != len(milestones) - 1:
                label_left = marker_left
            else:
                amount_text = f"${milestone['amount']:,}"
                label_text = str(milestone.get("label", ""))
                label_chars = len(label_text) + len(amount_text)
                label_left = 96 if label_chars > 20 else 98
            markers.append(
                html.Div([
                    html.Span("✓", style={
                        "fontSize": "0.95rem",
                        "fontWeight": "bold",
                        "color": "white",
                        "lineHeight": "24px",
                        "textAlign": "center",
                        "display": "inline-block",
                        "width": "100%"
                    }) if is_completed else html.Div(style={
                        "width": "8px",
                        "height": "8px",
                        "backgroundColor": self.colors["text_secondary"],
                        "borderRadius": "50%",
                        "margin": "auto"
                    })
                ], style={
                    "position": "absolute",
                    "left": f"{marker_left}%",
                    "top": "50%",
                    "width": "24px",
                    "height": "24px",
                    "backgroundColor": self.colors["green"] if is_completed else "transparent",
                    "borderRadius": "50%",
                    "transform": "translate(-50%, -50%)",
                    "border": "2px solid white" if is_completed else f"2px solid {self.colors['text_secondary']}",
                    "boxShadow": "0 0 6px rgba(0,0,0,0.5)",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "zIndex": "10",
                    "transition": "all 0.3s ease"
                })
            )
            
            # Label κάτω από το marker
            label_top = 44
            markers.append(
                html.Div([
                    html.Div(milestone["label"], style={
                        "fontSize": "0.8rem",
                        "color": self.colors["green"] if is_completed else self.colors["text_secondary"],
                        "fontWeight": "bold" if is_completed else "normal",
                        "textAlign": "center",
                        "whiteSpace": "nowrap",
                        "padding": "2px 6px",
                        "backgroundColor": self.colors["card_bg"]
                    }),
                    html.Div(f"${milestone['amount']:,}", style={
                        "fontSize": "0.75rem",
                        "color": self.colors["accent"],
                        "textAlign": "center",
                        "marginTop": "2px"
                    })
                ], style={
                    "position": "absolute",
                    "left": f"{label_left}%",
                    "top": f"{label_top}px",
                    "transform": "translateX(-50%)",
                    "minWidth": "70px"
                })
            )
        
        # Progress bar segments
        prev_position = 0
        for i, milestone in enumerate(milestones):
            position = (milestone["amount"] / max_amount) * 100
            is_completed = milestone.get("status") == "completed"
            
            # Segment width
            segment_width = position - prev_position
            
            # Progress within this segment
            if current_value <= milestone["amount"]:
                if i == 0:
                    segment_progress = min((current_value / milestone["amount"]) * segment_width, segment_width)
                else:
                    prev_milestone_amount = milestones[i-1]["amount"] if i > 0 else 0
                    if current_value > prev_milestone_amount:
                        segment_progress = ((current_value - prev_milestone_amount) / (milestone["amount"] - prev_milestone_amount)) * segment_width
                    else:
                        segment_progress = 0
            else:
                segment_progress = segment_width
            
            segments.append(
                html.Div(style={
                    "position": "absolute",
                    "left": f"{prev_position}%",
                    "width": f"{segment_progress}%",
                    "height": "24px",
                    "backgroundColor": self.colors["green"] if is_completed else self.colors["accent"],
                    "transition": "all 0.3s ease"
                })
            )
            
            prev_position = position
        
        return html.Div([
            html.Div([
                html.Span("Overall Progress", style={
                    "color": self.colors["text_primary"],
                    "fontWeight": "bold",
                    "fontSize": "1.1rem"
                }),
                html.Span(f"${current_value:,.0f} / ${max_amount:,}", style={
                    "color": self.colors["accent"],
                    "fontWeight": "bold",
                    "float": "right"
                })
            ], style={"marginBottom": "15px"}),
            
            # Segmented progress bar container
            html.Div([
                # Background track
                html.Div(style={
                    "width": "100%",
                    "height": "24px",
                    "backgroundColor": self.colors["grid"],
                    "borderRadius": "12px",
                    "position": "relative"
                }),
                
                # Progress segments
                html.Div(segments, style={
                    "position": "absolute",
                    "top": "0",
                    "left": "0",
                    "width": "100%",
                    "height": "24px",
                    "borderRadius": "12px",
                    "overflow": "hidden"
                }),
                
                # Markers
                html.Div(markers)
                
            ], style={
                "position": "relative",
                "marginBottom": "80px"
            })
        ])

    def _create_next_milestone_view(self, goal_data: dict) -> html.Div:
        """Δημιουργεί προβολή μόνο του επόμενου milestone."""
        next_milestone = goal_data.get("next_milestone")
        current_value = goal_data.get("current_value", 0)
        completed_count = goal_data.get("completed_count", 0)
        total_count = goal_data.get("total_count", 0)
        
        if not next_milestone:
            return html.Div([
                html.Div("🎉", style={
                    "fontSize": "3rem",
                    "textAlign": "center",
                    "marginBottom": "20px"
                }),
                html.H4("Congratulations!", style={
                    "color": self.colors["green"],
                    "textAlign": "center",
                    "marginBottom": "10px"
                }),
                html.P("You've achieved all your investment goals!", style={
                    "color": self.colors["text_primary"],
                    "textAlign": "center",
                    "fontSize": "1.1rem"
                })
            ])
        
        remaining = next_milestone["amount"] - current_value
        progress = (current_value / next_milestone["amount"]) * 100
        
        return html.Div([
            # Current milestone info
            html.Div([
                html.H4(f"Next Goal: {next_milestone['label']}", style={
                    "color": self.colors["accent"],
                    "textAlign": "center",
                    "marginBottom": "10px"
                }),
                html.P(f"Completed: {progress:.1f}%", style={
                    "color": self.colors["text_primary"],
                    "textAlign": "center",
                    "fontSize": "1.2rem",
                    "fontWeight": "bold"
                })
            ], style={"marginBottom": "20px"}),
            
            # Progress bar
            html.Div([
                html.Div([
                    html.Span(f"${current_value:,.0f}", style={
                        "color": self.colors["text_primary"],
                        "fontWeight": "bold"
                    }),
                    html.Span(f"${next_milestone['amount']:,}", style={
                        "color": self.colors["text_secondary"],
                        "fontWeight": "bold",
                        "float": "right"
                    })
                ], style={"marginBottom": "10px"}),
                
                html.Div([
                    html.Div(style={
                        "width": f"{progress}%",
                        "height": "20px",
                        "backgroundColor": self.colors["accent"],
                        "borderRadius": "10px",
                        "transition": "width 0.3s ease"
                    })
                ], style={
                    "width": "100%",
                    "height": "20px",
                    "backgroundColor": self.colors["grid"],
                    "borderRadius": "10px",
                    "marginBottom": "15px"
                })
            ]),
            
            # Stats
            html.Div([
                html.Div([
                    html.Span("Remaining:", style={"color": self.colors["text_secondary"]}),
                    html.Span(f"${remaining:,.0f}", style={
                        "color": self.colors["text_primary"],
                        "fontWeight": "bold",
                        "marginLeft": "10px"
                    })
                ], style={"marginBottom": "10px"}),
                html.Div([
                    html.Span("Completed Milestones:", style={"color": self.colors["text_secondary"]}),
                    html.Span(f"{completed_count}/{total_count}", style={
                        "color": self.colors["green"],
                        "fontWeight": "bold",
                        "marginLeft": "10px"
                    })
                ])
            ])
        ])

    def create_goal_setup_modal(self, suggestions: list = None) -> html.Div:
        """Δημιουργεί modal για setup νέου goal."""
        if not suggestions:
            suggestions = []
        
        return html.Div([
            html.Div([
                html.Div([
                    # Modal Header
                    html.Div([
                        html.H3("Set Investment Goal", style={
                            "color": self.colors["text_primary"],
                            "margin": "0"
                        }),
                        html.Button("×", id="close-goal-modal", style={
                            "background": "none",
                            "border": "none",
                            "fontSize": "1.5rem",
                            "color": self.colors["text_secondary"],
                            "cursor": "pointer",
                            "float": "right"
                        })
                    ], style={
                        "borderBottom": f"1px solid {self.colors['grid']}",
                        "paddingBottom": "15px",
                        "marginBottom": "20px",
                        "overflow": "hidden"
                    }),
                    
                    # Modal Body
                    html.Div([
                        html.P("Select number of milestones (1-10):", style={
                            "color": self.colors["text_primary"],
                            "marginBottom": "10px"
                        }),
                        dcc.Slider(
                            id="milestone-count-slider",
                            min=1, max=10, value=3, step=1,
                            marks={i: str(i) for i in range(1, 11)},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                        
                        html.Div(id="milestone-inputs", style={"marginTop": "20px"}),
                        
                        html.Div([
                            html.Button("Cancel", id="cancel-goal-btn", style={
                                "backgroundColor": self.colors["grid"],
                                "color": self.colors["text_primary"],
                                "border": "none",
                                "padding": "10px 20px",
                                "borderRadius": "6px",
                                "marginRight": "10px",
                                "cursor": "pointer"
                            }),
                            html.Button("Save Goal", id="save-goal-btn", style={
                                "backgroundColor": self.colors["accent"],
                                "color": "white",
                                "border": "none",
                                "padding": "10px 20px",
                                "borderRadius": "6px",
                                "cursor": "pointer"
                            })
                        ], style={"textAlign": "right", "marginTop": "20px"})
                    ])
                ], style={
                    "backgroundColor": self.colors["card_bg"],
                    "padding": "20px",
                    "borderRadius": "12px",
                    "width": "500px",
                    "maxWidth": "90vw",
                    "position": "relative"
                })
            ], style={
                "position": "fixed",
                "top": "0",
                "left": "0",
                "width": "100%",
                "height": "100%",
                "backgroundColor": "rgba(0,0,0,0.7)",
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "zIndex": "9999"
            })
        ], id="goal-setup-modal", style={"display": "none"})

