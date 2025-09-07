import logging
from datetime import datetime
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from config.settings import Config
from services.data_service import YahooFinanceDataService
from services.portfolio_service import PortfolioService
from ui.components import UIComponentFactory
from ui.pages import PageFactory
from utils.logging_config import setup_logging

class DashboardApplication:
    """Main dashboard application orchestrator."""
    
    def __init__(self):
        # Setup logging first
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration
        self.config = Config()
        
        # Initialize services with dependency injection
        self.data_service = YahooFinanceDataService(self.config)
        self.portfolio_service = PortfolioService(self.data_service, self.config)
        
        # Initialize UI components
        self.ui_factory = UIComponentFactory(self.config)
        self.page_factory = PageFactory(self.portfolio_service, self.ui_factory, self.config)
        
        # Create Dash app
        self.app = self._create_dash_app()
        self._register_callbacks()
        
        self.logger.info("Dashboard application initialized successfully")
    
    def _create_dash_app(self) -> dash.Dash:
        """Create and configure the Dash application."""
        app = dash.Dash(
            __name__,
            title="Andreas's Portfolio Tracker",
            meta_tags=[{
                "name": "viewport",
                "content": "width=device-width, initial-scale=1"
            }],
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )
        
        app.layout = self._create_main_layout()
        
        # Add custom CSS for dropdown styling
        app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
                <style>
                    /* Dropdown dark theme styling */
                    .Select-control {
                        background-color: #000000 !important;
                        border: 1px solid #333333 !important;
                        color: #FFFFFF !important;
                    }
                    .Select-value-label {
                        color: #FFFFFF !important;
                    }
                    .Select-placeholder {
                        color: #AAAAAA !important;
                    }
                    .Select-menu-outer {
                        background-color: #1E1E1E !important;
                        border: 1px solid #333333 !important;
                    }
                    .Select-option {
                        background-color: #1E1E1E !important;
                        color: #FFFFFF !important;
                    }
                    .Select-option:hover {
                        background-color: #333333 !important;
                        color: #FFFFFF !important;
                    }
                    .Select-option.is-selected {
                        background-color: #2979FF !important;
                        color: #FFFFFF !important;
                    }
                    .Select-arrow {
                        border-color: #FFFFFF transparent transparent !important;
                    }
                    .Select-input > input {
                        color: #FFFFFF !important;
                    }
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        '''
        
        return app
    
    def _create_main_layout(self) -> html.Div:
        """Create the main application layout."""
        return html.Div([
            # Application Header
            self._create_header(),
            
            # Main Content Container
            html.Div([
                # Navigation
                self._create_navigation(),
                
                # Dynamic Summary Cards
                html.Div(id="dashboard-summary"),
                
                # Main Content Area
                html.Div(id="main-content", style={"marginTop": "20px"}),
                
                # Footer
                self._create_footer()
                
            ], style={
                "padding": "0 2rem",
                "maxWidth": "1400px",
                "margin": "0 auto"
            })
            
        ], style={
            "fontFamily": "'Roboto', 'Segoe UI', 'Helvetica Neue', sans-serif",
            "backgroundColor": self.config.ui.colors["background"],
            "minHeight": "100vh",
            "color": self.config.ui.colors["text_primary"]
        })
    
    def _create_header(self) -> html.Div:
        """Create application header."""
        return html.Div([
            html.H1("Andreas's Portfolio Tracker", style={
                "fontWeight": "600",
                "margin": "0",
                "fontSize": "2.5rem"
            }),
            html.P(
                "Professional investment tracking with real-time analytics",
                style={
                    "fontSize": "1.2rem",
                    "marginTop": "8px",
                    "opacity": "0.9"
                }
            )
        ], style={
            "backgroundColor": self.config.ui.colors["header"],
            "color": self.config.ui.colors["text_primary"],
            "padding": "2rem",
            "boxShadow": "0 4px 12px rgba(0,0,0,0.3)",
            "marginBottom": "30px",
            "borderRadius": "0 0 20px 20px",
            "borderBottom": f"2px solid {self.config.ui.colors['accent']}"
        })
    
    def _create_navigation(self) -> html.Div:
        """Create navigation dropdown."""
        return html.Div([
            dcc.Dropdown(
                id="page-selector",
                options=[
                    {"label": "📈 Individual Tickers", "value": "tickers"},
                    {"label": "📊 Portfolio Overview", "value": "portfolio"},
                    {"label": "📋 Trading History", "value": "trades"},
                    {"label": "💰 Personal Finances", "value": "finances"}
                ],
                value="tickers",
                clearable=False,
                style={
                    "color": self.config.ui.colors["text_primary"],
                    "fontWeight": "bold"
                }
            )
        ], style={
            "width": "350px",
            "margin": "20px auto"
        })
    
    def _create_footer(self) -> html.Footer:
        """Create application footer."""
        return html.Footer([
            html.P(
                "Data powered by Yahoo Finance • Real-time updates • Professional Analytics",
                style={
                    "textAlign": "center",
                    "color": self.config.ui.colors["text_secondary"],
                    "padding": "30px",
                    "fontSize": "0.9rem"
                }
            )
        ])
    
    def _register_callbacks(self):
        """Register all Dash callbacks."""
        
        @self.app.callback(
            Output("main-content", "children"),
            Input("page-selector", "value")
        )
        def render_page_content(page_name: str):
            """Render the selected page content."""
            try:
                self.logger.info(f"Rendering page: {page_name}")
                return self.page_factory.create_page(page_name).render()
            except Exception as e:
                self.logger.error(f"Error rendering page {page_name}: {e}")
                return self._create_error_content(str(e))
        
        @self.app.callback(
            Output("dashboard-summary", "children"),
            Input("page-selector", "value")
        )
        def render_dashboard_summary(page_name: str):
            """Render dashboard summary cards."""
            # Only show summary for portfolio page
            if page_name != "portfolio":
                return html.Div()
            
            try:
                portfolio = self.portfolio_service.get_portfolio_snapshot()
                return self._create_summary_section(portfolio)
            except Exception as e:
                self.logger.error(f"Error creating summary: {e}")
                return html.Div()
    
    def _create_summary_section(self, portfolio) -> html.Div:
        """Create dashboard summary section with invested metric."""
        return html.Div([
            html.H2("Portfolio Dashboard", style={
                "textAlign": "center",
                "color": self.config.ui.colors["accent"],
                "marginTop": "10px",
                "marginBottom": "20px"
            }),
            
            html.Div([
                self.ui_factory.create_metric_card(
                    "Last Updated",
                    datetime.now().strftime("%d %b %Y, %H:%M")
                ),
                self.ui_factory.create_metric_card(
                    "Invested",
                    f"€{portfolio.total_metrics.invested:.2f}",
                    self.config.ui.colors["text_primary"]
                ),
                self.ui_factory.create_metric_card(
                    "Total Portfolio Value",
                    f"€{portfolio.total_metrics.current_value:.2f}",
                    self.config.ui.colors["accent"]
                ),
                self.ui_factory.create_metric_card(
                    "Total P&L",
                    f"€{portfolio.total_metrics.profit_absolute:.2f}",
                    self.config.ui.colors["green"] if portfolio.total_metrics.is_profitable else self.config.ui.colors["red"]
                ),
                self.ui_factory.create_metric_card(
                    "Overall Return",
                    f"{portfolio.total_metrics.return_percentage:.2f}%",
                    self.config.ui.colors["green"] if portfolio.total_metrics.return_percentage >= 0 else self.config.ui.colors["red"]
                )
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "flexWrap": "wrap"
            })
        ])
    
    def _create_error_content(self, error_message: str) -> html.Div:
        """Create error content display."""
        return html.Div([
            html.H3("Application Error", style={
                "color": self.config.ui.colors["red"],
                "textAlign": "center"
            }),
            html.P(f"An error occurred: {error_message}", style={
                "textAlign": "center",
                "color": self.config.ui.colors["text_secondary"]
            }),
            html.P("Please check the logs for more details.", style={
                "textAlign": "center",
                "color": self.config.ui.colors["text_secondary"]
            })
        ], style=self.config.ui.card_style)
    
    def run(self, debug: bool = True, host: str = "0.0.0.0", port: int = 8050):
        """Run the dashboard application."""
        self.logger.info(f"Starting dashboard server on {host}:{port}")
        self.app.run(
            debug=debug,
            host=host,
            port=port,
            use_reloader=False
        )

# --- expose Dash server for gunicorn ---
app_instance = DashboardApplication()
server = app_instance.app.server  # used by: gunicorn app:server

def main():
    """Application entry point."""
    app_instance.run()

if __name__ == "__main__":
    main()
