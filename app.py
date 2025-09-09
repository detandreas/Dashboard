import logging
import dash
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from config.settings import Config
from services.data_service import YahooFinanceDataService
from services.portfolio_service import PortfolioService
from ui.components import UIComponentFactory
from ui.page_factory import PageFactory
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

        return app
    
    def _create_main_layout(self) -> html.Div:
        """Create the main application layout with sidebar."""
        nav_items = [
            {"id": "tickers", "icon": "📈", "label": "Individual Tickers"},
            {"id": "portfolio", "icon": "📊", "label": "Portfolio Overview"},
            {"id": "trades", "icon": "📋", "label": "Trading History"},
            {"id": "finances", "icon": "💰", "label": "Personal Finances"},
        ]

        return html.Div([
            # Sidebar Navigation
            self.ui_factory.create_sidebar(nav_items),

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
                    self.ui_factory.create_footer(),
                ], className="content-body"),

            ], className="main-content"),

        ], className="app-container")

    def _register_callbacks(self):
        """Register all Dash callbacks."""
        
        # Navigation callback
        @self.app.callback(
            [Output("active-page", "data"),
             Output("nav-tickers", "className"),
             Output("nav-portfolio", "className"),
             Output("nav-trades", "className"),
             Output("nav-finances", "className"),
             Output("nav-settings", "className")],
            [Input("nav-tickers", "n_clicks"),
             Input("nav-portfolio", "n_clicks"),
             Input("nav-trades", "n_clicks"),
             Input("nav-finances", "n_clicks"),
             Input("nav-settings", "n_clicks")]
        )
        def handle_navigation(tickers_clicks, portfolio_clicks, trades_clicks, finances_clicks, settings_clicks):
            """Handle sidebar navigation clicks."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return "tickers", "nav-item active", "nav-item", "nav-item", "nav-item", "nav-item settings-button"
            
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            page_map = {
                "nav-tickers": "tickers",
                "nav-portfolio": "portfolio", 
                "nav-trades": "trades",
                "nav-finances": "finances",
                "nav-settings": "settings"
            }
            
            active_page = page_map.get(button_id, "tickers")
            
            # Set active classes
            classes = ["nav-item"] * 4 + ["nav-item settings-button"]
            page_index = list(page_map.values()).index(active_page)
            if page_index < 4:
                classes[page_index] = "nav-item active"
            else:
                classes[4] = "nav-item settings-button active"
            
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
                },
                "settings": {
                    "title": "Application Settings",
                    "subtitle": "Configure your dashboard preferences and profile"
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
                return self.ui_factory.create_error_content(str(e))
        
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
                return self.ui_factory.create_portfolio_summary(portfolio)
            except Exception as e:
                self.logger.error(f"Error creating summary: {e}")
                return html.Div()
    
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
