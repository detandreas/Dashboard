from dash import html, dcc
import logging

from ui.Pages.base_page import BasePage
from ui.Components.components import UIComponentFactory
from config.settings import Config

logger = logging.getLogger(__name__)

class SettingsPage(BasePage):
    """Application settings page."""
    
    def __init__(self, ui_factory: UIComponentFactory, config: Config):
        super().__init__(ui_factory)
        self.config = config
        # Initialize goals service
        from services.goals_service import GoalsService
        self.goals_service = GoalsService()
    
    def render(self) -> html.Div:
        """Render settings page."""
        try:
            return html.Div([
                # User Profile Section
                self._create_user_profile_section(),
                
                # Goals Management Section
                self._create_goals_section(),
                
                # Application Settings Section
                self._create_app_settings_section(),
                
                # Data Settings Section
                self._create_data_settings_section(),
                
                # About Section
                self._create_about_section(),
                
                # Goals Modal
                self._create_goals_modal()
            ])
            
        except Exception as e:
            logger.error(f"Error rendering settings page: {e}")
            return self._create_error_message(str(e))
    
    def _create_goals_section(self) -> html.Div:
        """Create goals management section."""
        current_goal = self.goals_service.get_current_goal()
        
        if current_goal:
            # Show current goal
            milestones_text = ", ".join([
                f"${m['amount']:,.0f} ({m['label']})" 
                for m in current_goal["milestones"]
            ])
            
            content = html.Div([
                html.Div([
                    html.H5("Current Goal", style={"color": self.colors["text_primary"]}),
                    html.P(f"Metric: {current_goal['metric'].replace('_', ' ').title()}", style={
                        "color": self.colors["text_secondary"],
                        "margin": "5px 0"
                    }),
                    html.P(f"Milestones: {milestones_text}", style={
                        "color": self.colors["text_secondary"],
                        "margin": "5px 0",
                        "fontSize": "0.9rem"
                    })
                ], style={"marginBottom": "15px"}),
                
                html.Div([
                    html.Button("Edit Goal", id="edit-goal-btn", className="btn-primary", 
                              style={"marginRight": "10px"}),
                    html.Button("Delete Goal", id="delete-goal-btn", className="btn-danger")
                ])
            ])
        else:
            # Show add goal option
            content = html.Div([
                html.P("No goals configured yet.", style={
                    "color": self.colors["text_secondary"],
                    "marginBottom": "15px"
                }),
                html.Button("Add Goal", id="add-goal-btn", className="btn-primary")
            ])
        
        return html.Div([
            html.H3("Portfolio Goals", style={
                "color": self.colors["accent"],
                "marginBottom": "20px"
            }),
            content
        ], style={
            **self.config.ui.card_style,
            "marginBottom": "30px"
        })
    
    def _create_goals_modal(self) -> html.Div:
        """Create goals configuration modal."""
        return html.Div([
            html.Div([
                html.Div([
                    # Modal header
                    html.Div([
                        html.H3("Configure Portfolio Goal", style={
                            "color": self.colors["text_primary"],
                            "margin": "0"
                        }),
                        html.Button("×", id="close-goals-modal", className="btn-close")
                    ], style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "marginBottom": "20px"
                    }),
                    
                    # Step indicator
                    html.Div(id="goals-step-indicator", children=[
                        self._create_step_indicator(1)
                    ]),
                    
                    # Modal content
                    html.Div(id="goals-modal-content", children=[
                        self._create_step_1_content()
                    ]),
                    
                    # Modal footer
                    html.Div([
                        html.Button("Cancel", id="goals-cancel-btn", className="btn-secondary",
                                  style={"marginRight": "10px"}),
                        html.Button("Next", id="goals-next-btn", className="btn-primary"),
                        html.Button("Save Goal", id="goals-save-btn", className="btn-primary", 
                                  style={"display": "none"})
                    ], style={
                        "display": "flex",
                        "justifyContent": "flex-end",
                        "marginTop": "30px"
                    })
                    
                ], className="modal-content")
            ], className="modal-overlay", id="goals-modal", style={"display": "none"}),
            
            # Store for modal state
            dcc.Store(id="goals-modal-step", data=1),
            dcc.Store(id="goals-modal-data", data={}),
            dcc.Store(id="goals-milestones-data", data=[])
        ])
    
    def _create_step_indicator(self, current_step: int) -> html.Div:
        """Create step indicator for goals modal."""
        steps = ["Metric", "Milestones", "Preview"]
        
        step_elements = []
        for i, step_name in enumerate(steps, 1):
            is_active = i == current_step
            is_completed = i < current_step
            
            if is_completed:
                color = self.colors["green"]
                bg_color = self.colors["green"]
            elif is_active:
                color = self.colors["accent"]
                bg_color = self.colors["accent"]
            else:
                color = self.colors["text_secondary"]
                bg_color = self.colors["grid"]
            
            step_elements.append(
                html.Div([
                    html.Div(str(i), style={
                        "width": "30px",
                        "height": "30px",
                        "borderRadius": "50%",
                        "backgroundColor": bg_color,
                        "color": "white",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontWeight": "bold",
                        "marginBottom": "5px"
                    }),
                    html.Div(step_name, style={
                        "fontSize": "0.8rem",
                        "color": color,
                        "textAlign": "center"
                    })
                ], style={"textAlign": "center"})
            )
        
        return html.Div(step_elements, style={
            "display": "flex",
            "justifyContent": "center",
            "gap": "40px",
            "marginBottom": "30px"
        })
    
    def _create_step_1_content(self) -> html.Div:
        """Create step 1 content - metric selection."""
        return html.Div([
            html.H4("Select Goal Metric", style={
                "color": self.colors["text_primary"],
                "marginBottom": "20px"
            }),
            html.P("Choose what you want to track:", style={
                "color": self.colors["text_secondary"],
                "marginBottom": "20px"
            }),
            dcc.RadioItems(
                id="goals-metric-selection",
                options=[
                    {"label": "Portfolio Value", "value": "portfolio_value"}
                ],
                value="portfolio_value",
                style={"color": self.colors["text_primary"]}
            )
        ])
    
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
