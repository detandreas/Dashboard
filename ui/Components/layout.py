from dash import html, dcc
from typing import List


class LayoutComponentsMixin:
    """Layout-related components such as sidebar and footer."""
    
    def _create_svg_icon(self, icon_name: str) -> html.Div:
        """Create professional Unicode icon based on icon name."""
        # Using professional Unicode symbols instead of SVG
        unicode_icons = {
            "chart_line": "⟰",      # Trending up arrow
            "chart_bar": "⊞",       # Square with plus (representing bars)
            "list": "☰",            # Hamburger menu (list)
            "dollar": "$",          # Dollar sign
            "settings": "⚙"         # Gear symbol
        }
        
        return html.Div(
            unicode_icons.get(icon_name, "⟰"),
            className="nav-icon",
            style={
                "marginRight": "12px", 
                "display": "flex", 
                "alignItems": "center",
                "fontSize": "18px",
                "color": "white",
                "fontWeight": "bold"
            }
        )

    def create_sidebar(self, nav_items: List[dict]) -> html.Div:
        """Create the sidebar navigation component."""
        return html.Div(
            [
                html.Div(
                    [
                        html.H1(
                            "Portfolio Tracker",
                            style={
                                "color": "white",
                                "fontSize": "1.4rem",
                                "fontWeight": "600",
                                "margin": "0",
                                "textAlign": "center",
                            },
                        ),
                        html.P(
                            "Investment Analytics",
                            style={
                                "color": "rgba(255,255,255,0.8)",
                                "fontSize": "0.85rem",
                                "margin": "5px 0 0 0",
                                "textAlign": "center",
                            },
                        ),
                    ],
                    style={
                        "padding": "25px 20px",
                        "borderBottom": "1px solid #333",
                        "background": "#00008B",
                        "flexShrink": "0",
                    },
                ),
                html.Div(
                    [
                        html.Button(
                            [
                                self._create_svg_icon(item["icon"]),
                                html.Span(
                                    item["label"],
                                    style={"fontSize": "0.95rem"},
                                ),
                            ],
                            id=f"nav-{item['id']}",
                            className="nav-item nav-metric-card",
                            n_clicks=0,
                        )
                        for item in nav_items
                    ],
                    className="nav-menu",
                    style={
                        "flex": "1",
                        "overflow": "hidden",
                        "display": "flex",
                        "flexDirection": "column",
                        "padding": "10px 0",
                    },
                ),
                html.Div(
                    [
                        html.Button(
                            [
                                html.Div(
                                    [
                                        html.Img(
                                            src="/assets/PATRICK.png",
                                            style={
                                                "width": "32px",
                                                "height": "32px",
                                                "borderRadius": "50%",
                                                "marginRight": "10px",
                                                "border": "2px solid rgba(255,255,255,0.3)",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.Div(
                                                    "Andreas Papathanasiou",
                                                    style={
                                                        "fontSize": "0.85rem",
                                                        "fontWeight": "600",
                                                        "color": self.colors["text_primary"],
                                                        "lineHeight": "1.1",
                                                        "whiteSpace": "nowrap",
                                                        "overflow": "hidden",
                                                        "textOverflow": "ellipsis",
                                                    },
                                                ),
                                                html.Div(
                                                    "Settings",
                                                    style={
                                                        "fontSize": "0.7rem",
                                                        "color": self.colors["text_secondary"],
                                                        "lineHeight": "1.1",
                                                    },
                                                ),
                                            ],
                                            style={"flex": "1", "minWidth": "0"},
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "width": "100%",
                                        "minWidth": "0",
                                    },
                                ),
                                html.Div(
                                    self._create_svg_icon("settings"),
                                    style={"marginLeft": "5px", "flexShrink": "0", "marginRight": "0"},
                                ),
                            ],
                            id="nav-settings",
                            className="nav-item settings-button",
                            n_clicks=0,
                            style={
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "space-between",
                                "padding": "10px 12px",
                                "margin": "10px",
                                "backgroundColor": self.colors["card_bg"],
                                "border": f"1px solid {self.colors['grid']}",
                                "borderRadius": "8px",
                                "cursor": "pointer",
                                "transition": "all 0.2s ease",
                                "minHeight": "50px",
                                "width": "calc(100% - 20px)",
                            },
                        )
                    ],
                    style={
                        "padding": "10px 0 15px 0",
                        "borderTop": f"1px solid {self.colors['grid']}",
                        "flexShrink": "0",
                    },
                ),
                dcc.Store(id="active-page", data="tickers"),
            ],
            className="sidebar",
            style={
                "display": "flex",
                "flexDirection": "column",
                "height": "100vh",
                "overflow": "hidden",
                "width": "280px",
                "position": "fixed",
            },
        )

    def create_footer(self) -> html.Footer:
        """Create application footer component."""
        return html.Footer(
            [
                html.P(
                    "Data powered by Yahoo Finance • Real-time updates • Professional Analytics",
                    style={
                        "textAlign": "center",
                        "color": self.colors["text_secondary"],
                        "padding": "30px",
                        "fontSize": "0.9rem",
                    },
                )
            ]
        )

    def create_error_content(self, error_message: str) -> html.Div:
        """Create standardized error display component."""
        return html.Div(
            [
                html.H3(
                    "Application Error",
                    style={"color": self.colors["red"], "textAlign": "center"},
                ),
                html.P(
                    f"An error occurred: {error_message}",
                    style={"textAlign": "center", "color": self.colors["text_secondary"]},
                ),
                html.P(
                    "Please check the logs for more details.",
                    style={"textAlign": "center", "color": self.colors["text_secondary"]},
                ),
            ],
            style=self.config.ui.card_style,
        )
