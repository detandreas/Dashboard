from dash import html, dcc
import logging

from ui.Pages.base_page import BasePage
from ui.Components import UIComponentFactory
from config.settings import Config

logger = logging.getLogger(__name__)

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
