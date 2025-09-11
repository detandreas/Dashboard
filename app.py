import logging
import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from config.settings import Config
from services.data_service import YahooFinanceDataService
from services.portfolio_service import PortfolioService
from services.goal_service import GoalService
from ui.Components import UIComponentFactory
from ui.Pages.page_factory import PageFactory
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
        self.goal_service = GoalService(self.config)
        
        # Initialize UI components
        self.ui_factory = UIComponentFactory(self.config)
        self.page_factory = PageFactory(self.portfolio_service, self.ui_factory, self.config, self.goal_service)
        
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
            
            # Goal Setup Modal
            self.ui_factory.create_goal_setup_modal(),
            
            # Hidden store for active page
            dcc.Store(id="active-page", data="tickers"),
            
            # Hidden store for goal view mode
            dcc.Store(id="goal-view-mode", data=True)

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
        
        # Goal management callbacks
        @self.app.callback(
            Output("goal-setup-modal", "style"),
            [Input("add-goal-btn", "n_clicks"),
             Input("close-goal-modal", "n_clicks"),
             Input("cancel-goal-btn", "n_clicks"),
             Input("save-goal-btn", "n_clicks")],
            [State("active-page", "data")],
            prevent_initial_call=True
        )
        def handle_modal_visibility(add_clicks, close_clicks, cancel_clicks, save_clicks, active_page):
            """Διαχειρίζεται την εμφάνιση/κρύψιμο του modal."""
            ctx = dash.callback_context
            if not ctx.triggered:
                raise PreventUpdate
            
            # Επιτρέπουμε δράση μόνο στη σελίδα portfolio
            if active_page != "portfolio":
                raise PreventUpdate
            
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
            
            if trigger_id == "add-goal-btn":
                # Ανοίγει ΜΟΝΟ όταν υπάρχει πραγματικό κλικ (>0)
                if not add_clicks:
                    raise PreventUpdate
                return {"display": "block"}
            
            if trigger_id == "close-goal-modal" and close_clicks:
                return {"display": "none"}
            if trigger_id == "cancel-goal-btn" and cancel_clicks:
                return {"display": "none"}
            if trigger_id == "save-goal-btn" and save_clicks:
                return {"display": "none"}
            
            raise PreventUpdate
        
        @self.app.callback(
            Output("milestone-inputs", "children"),
            [Input("milestone-count-slider", "value"),
             Input("add-goal-btn", "n_clicks")],
            [State("goal-setup-modal", "style")],
            prevent_initial_call=True
        )
        def update_milestone_inputs(milestone_count, add_clicks, modal_style):
            """Ενημερώνει τα milestone inputs μόνο όταν το modal είναι ανοικτό ή όταν πατηθεί το add."""
            ctx = dash.callback_context
            if not ctx.triggered:
                raise PreventUpdate
            
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
            
            # Επιτρέπουμε τη δημιουργία inputs όταν πατηθεί το add-goal-btn
            if trigger_id == "add-goal-btn" and add_clicks:
                if milestone_count is None:
                    milestone_count = 3
                portfolio = self.portfolio_service.get_portfolio_snapshot()
                current_value = portfolio.total_metrics.current_value
                suggestions = self.goal_service.get_goal_suggestions(current_value)
                return self._create_milestone_inputs(int(milestone_count), suggestions[:int(milestone_count)])
            
            # Επιτρέπουμε αλλαγές slider μόνο όταν το modal είναι ορατό
            is_modal_open = isinstance(modal_style, dict) and modal_style.get("display") == "block"
            if trigger_id == "milestone-count-slider" and is_modal_open:
                if milestone_count is None:
                    milestone_count = 3
                portfolio = self.portfolio_service.get_portfolio_snapshot()
                current_value = portfolio.total_metrics.current_value
                suggestions = self.goal_service.get_goal_suggestions(current_value)
                return self._create_milestone_inputs(int(milestone_count), suggestions[:int(milestone_count)])
            
            raise PreventUpdate
        
        @self.app.callback(
            Output("main-content", "children", allow_duplicate=True),
            [Input("save-goal-btn", "n_clicks")],
            [State({"type": "milestone-label", "index": dash.dependencies.ALL}, "value"),
             State({"type": "milestone-amount", "index": dash.dependencies.ALL}, "value")],
            prevent_initial_call=True
        )
        def save_goal(save_clicks, labels, amounts):
            """Αποθηκεύει νέο goal."""
            if not save_clicks:
                raise PreventUpdate
            
            try:
                # Δημιουργία milestones από τα inputs
                milestones = []
                for i, (label, amount) in enumerate(zip(labels or [], amounts or [])):
                    if label and amount and amount > 0:
                        milestones.append({
                            "label": label,
                            "amount": float(amount),
                            "status": "upcoming"
                        })
                
                if milestones and self.goal_service.save_goal(milestones):
                    self.logger.info(f"Goal saved with {len(milestones)} milestones")
                    # Επιστροφή στο portfolio page με ενημερωμένο goal
                    return self.page_factory.create_page("portfolio").render()
                else:
                    self.logger.error("Failed to save goal")
                    
            except Exception as e:
                self.logger.error(f"Error saving goal: {e}")
            
            raise PreventUpdate
        
        @self.app.callback(
            Output("main-content", "children", allow_duplicate=True),
            [Input("delete-goal-btn", "n_clicks")],
            prevent_initial_call=True
        )
        def delete_goal(delete_clicks):
            """Διαγράφει το τρέχον goal."""
            if not delete_clicks:
                raise PreventUpdate
            
            try:
                if self.goal_service.delete_current_goal():
                    self.logger.info("Goal deleted successfully")
                    # Επιστροφή στο portfolio page χωρίς goal
                    return self.page_factory.create_page("portfolio").render()
                else:
                    self.logger.error("Failed to delete goal")
                    
            except Exception as e:
                self.logger.error(f"Error deleting goal: {e}")
            
            raise PreventUpdate
        
        @self.app.callback(
            [Output("goal-progress-content", "children"),
             Output("goal-view-mode", "data"),
             Output("goal-view-toggle", "children")],
            [Input("goal-view-toggle", "n_clicks")],
            [State("goal-view-mode", "data"),
             State("active-page", "data")],
            prevent_initial_call=True
        )
        def toggle_goal_view(toggle_clicks, current_mode, active_page):
            """Εναλλάσσει τον τρόπο προβολής του goal."""
            if not toggle_clicks or active_page != "portfolio":
                raise PreventUpdate
            
            try:
                portfolio = self.portfolio_service.get_portfolio_snapshot()
                current_value = portfolio.total_metrics.current_value
                goal_data = self.goal_service.update_milestone_status(current_value)
                
                # Toggle the view mode
                new_mode = not current_mode
                goal_data["show_all_milestones"] = new_mode
                
                # Update button text
                button_text = "Next Milestone" if new_mode else "Overall Progress"
                
                return (
                    self.ui_factory._create_goal_progress_content(goal_data),
                    new_mode,
                    button_text
                )
                
            except Exception as e:
                self.logger.error(f"Error toggling goal view: {e}")
                raise PreventUpdate
        
    def _create_milestone_inputs(self, count: int, suggestions: list = None) -> list:
        """Δημιουργεί input fields για milestones."""
        if not suggestions:
            suggestions = []
        
        inputs = []
        for i in range(count):
            suggestion = suggestions[i] if i < len(suggestions) else {"amount": 0, "label": f"Milestone {i+1}"}
            
            inputs.append(
                html.Div([
                    html.Label(f"Milestone {i+1}:", style={
                        "color": self.config.ui.colors["text_primary"],
                        "marginBottom": "5px",
                        "display": "block"
                    }),
                    html.Div([
                        dcc.Input(
                            id={"type": "milestone-label", "index": i},
                            type="text",
                            value=suggestion["label"],
                            placeholder="Label",
                            style={
                                "width": "48%",
                                "padding": "8px",
                                "marginRight": "4%",
                                "backgroundColor": self.config.ui.colors["background"],
                                "color": self.config.ui.colors["text_primary"],
                                "border": f"1px solid {self.config.ui.colors['grid']}",
                                "borderRadius": "4px"
                            }
                        ),
                        dcc.Input(
                            id={"type": "milestone-amount", "index": i},
                            type="number",
                            value=suggestion["amount"],
                            placeholder="Amount ($)",
                            style={
                                "width": "48%",
                                "padding": "8px",
                                "backgroundColor": self.config.ui.colors["background"],
                                "color": self.config.ui.colors["text_primary"],
                                "border": f"1px solid {self.config.ui.colors['grid']}",
                                "borderRadius": "4px"
                            }
                        )
                    ])
                ], style={"marginBottom": "15px"})
            )
        
        return inputs

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
