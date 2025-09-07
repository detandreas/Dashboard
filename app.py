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

"""
Dashboard – four overall views
=============================
* **Dropdown** με 4 επιλογές:
  1. **Tickers (VUAA, EQAC, USD)** → εμφανίζει το ένα κάτω απ' το άλλο:
     - κάρτες Invested/Current/Profit/Return για κάθε ticker
     - γράφημα Price + DCA + Buys
  2. **Portfolio** → εμφανίζει συνοπτικές κάρτες χαρτοφυλακίου και δύο διαγράμματα:
     - Profit curve (ETF + USD)
     - Yield % curve (Profit / Invested ETFs)
  3. **Trades History** --> εμφανιζει εναν καταλογο με ολα τα trades 
        που εχουν πραγματοποιηθει
  4. **Personal Finances** --> Εμφανιζει διαγραμματα που αφορουν¨
      - Το Εισοδημα σου
      - Τα εξοδα σου
      - Τις επενδυσεις σου
      - Συνολικο διαγραμμα


* Στις κάρτες portfolio: Invested = κεφάλαιο μόνο ETF, Profit = P/L ETF + USD.
"""

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
        
        # Add custom CSS for sidebar styling
        app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
                <style>
                    body {
                        margin: 0;
                        padding: 0;
                        font-family: 'Roboto', 'Segoe UI', 'Helvetica Neue', sans-serif;
                    }
                    
                    .app-container {
                        display: flex;
                        min-height: 100vh;
                        background-color: #0A0A0A;
                    }
                    
                    .sidebar {
                        width: 220px;
                        background: linear-gradient(180deg, #1a1a1a 0%, #0f0f0f 100%);
                        border-right: 2px solid #333;
                        position: fixed;
                        height: 100vh;
                        overflow-y: auto;
                        box-shadow: 4px 0 12px rgba(0,0,0,0.3);
                    }
                    
                    .sidebar-header {
                        padding: 25px 20px;
                        border-bottom: 1px solid #333;
                        background: linear-gradient(135deg, #2979FF 0%, #1976D2 100%);
                    }
                    
                    .sidebar-title {
                        color: white;
                        font-size: 1.4rem;
                        font-weight: 600;
                        margin: 0;
                        text-align: center;
                    }
                    
                    .sidebar-subtitle {
                        color: rgba(255,255,255,0.8);
                        font-size: 0.85rem;
                        margin: 5px 0 0 0;
                        text-align: center;
                    }
                    
                    .nav-menu {
                        padding: 20px 0;
                    }
                    
                    .nav-item {
                        display: flex;
                        align-items: center;
                        padding: 12px 20px;
                        color: #CCCCCC;
                        text-decoration: none;
                        font-size: 0.95rem;
                        font-weight: 500;
                        border: none;
                        background: none;
                        width: 100%;
                        text-align: left;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        border-left: 3px solid transparent;
                    }
                    
                    .nav-item:hover {
                        background-color: #252525;
                        color: #2979FF;
                        border-left-color: #2979FF;
                    }
                    
                    .nav-item.active {
                        background-color: #2979FF20;
                        color: #2979FF;
                        border-left-color: #2979FF;
                        font-weight: 600;
                    }
                    
                    .main-content {
                        margin-left: 220px;
                        flex: 1;
                        background-color: #0A0A0A;
                        min-height: 100vh;
                    }
                    
                    .content-header {
                        background: linear-gradient(135deg, #1E1E1E 0%, #121212 100%);
                        color: white;
                        padding: 30px 40px;
                        border-bottom: 2px solid #2979FF;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    }
                    
                    .content-body {
                        padding: 30px 40px;
                        max-width: 1400px;
                        margin: 0 auto;
                    }
                    
                    .page-title {
                        font-size: 2.2rem;
                        font-weight: 600;
                        margin: 0;
                        color: white;
                    }
                    
                    .page-subtitle {
                        font-size: 1.1rem;
                        margin: 8px 0 0 0;
                        opacity: 0.9;
                        color: #CCCCCC;
                    }
                    
                    @media (max-width: 768px) {
                        .sidebar {
                            width: 200px;
                        }
                        .main-content {
                            margin-left: 200px;
                        }
                        .content-body {
                            padding: 20px;
                        }
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
        """Create the main application layout with sidebar."""
        return html.Div([
            # Sidebar Navigation
            self._create_sidebar(),
            
            # Main Content Area
            html.Div([
                # Page Header
                html.Div(id="page-header"),
                
                # Content Body
                html.Div([
                    # Dynamic Summary Cards
                    html.Div(id="dashboard-summary"),
                    
                    # Main Content
                    html.Div(id="main-content", style={"marginTop": "20px"}),
                    
                    # Footer
                    self._create_footer()
                ], className="content-body")
                
            ], className="main-content")
            
        ], className="app-container")
    
    def _create_sidebar(self) -> html.Div:
        """Create fixed sidebar navigation."""
        nav_items = [
            {"id": "tickers", "icon": "📈", "label": "Individual Tickers"},
            {"id": "portfolio", "icon": "📊", "label": "Portfolio Overview"},
            {"id": "trades", "icon": "📋", "label": "Trading History"},
            {"id": "finances", "icon": "💰", "label": "Personal Finances"}
        ]
        
        return html.Div([
            # Sidebar Header
            html.Div([
                html.H1("Portfolio Tracker", className="sidebar-title"),
                html.P("Investment Analytics", className="sidebar-subtitle")
            ], className="sidebar-header"),
            
            # Navigation Menu
            html.Div([
                html.Button([
                    html.Span(f"{item['icon']}", style={"marginRight": "10px", "fontSize": "1.1rem"}),
                    html.Span(item['label'], style={"fontSize": "0.95rem"})
                ], 
                id=f"nav-{item['id']}", 
                className="nav-item",
                n_clicks=0
                ) for item in nav_items
            ], className="nav-menu"),
            
            # Store for active page
            dcc.Store(id="active-page", data="tickers")
            
        ], className="sidebar")
    
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
        
        # Navigation callback
        @self.app.callback(
            [Output("active-page", "data"),
             Output("nav-tickers", "className"),
             Output("nav-portfolio", "className"),
             Output("nav-trades", "className"),
             Output("nav-finances", "className")],
            [Input("nav-tickers", "n_clicks"),
             Input("nav-portfolio", "n_clicks"),
             Input("nav-trades", "n_clicks"),
             Input("nav-finances", "n_clicks")]
        )
        def handle_navigation(tickers_clicks, portfolio_clicks, trades_clicks, finances_clicks):
            """Handle sidebar navigation clicks."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return "tickers", "nav-item active", "nav-item", "nav-item", "nav-item"
            
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            page_map = {
                "nav-tickers": "tickers",
                "nav-portfolio": "portfolio", 
                "nav-trades": "trades",
                "nav-finances": "finances"
            }
            
            active_page = page_map.get(button_id, "tickers")
            
            # Set active classes
            classes = ["nav-item"] * 4
            page_index = list(page_map.values()).index(active_page)
            classes[page_index] = "nav-item active"
            
            return active_page, *classes
        
        @self.app.callback(
            Output("page-header", "children"),
            Input("active-page", "data")
        )
        def update_page_header(active_page: str):
            """Update page header based on active page."""
            headers = {
                "tickers": {
                    "title": "Individual Tickers Analysis",
                    "subtitle": "Detailed performance tracking for each investment"
                },
                "portfolio": {
                    "title": "Portfolio Overview", 
                    "subtitle": "Comprehensive portfolio analytics and metrics"
                },
                "trades": {
                    "title": "Trading History",
                    "subtitle": "Complete transaction log with filtering and sorting"
                },
                "finances": {
                    "title": "Personal Finances",
                    "subtitle": "Income, expenses, and investment tracking"
                }
            }
            
            header_info = headers.get(active_page, headers["tickers"])
            
            return html.Div([
                html.H1(header_info["title"], className="page-title"),
                html.P(header_info["subtitle"], className="page-subtitle")
            ], className="content-header")
        
        @self.app.callback(
            Output("main-content", "children"),
            Input("active-page", "data")
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
            Input("active-page", "data")
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
