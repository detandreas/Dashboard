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
            {"id": "tickers", "icon": "chart_line", "label": "Individual Tickers"},
            {"id": "portfolio", "icon": "chart_bar", "label": "Portfolio Overview"},
            {"id": "trades", "icon": "list", "label": "Trading History"},
            {"id": "finances", "icon": "dollar", "label": "Personal Finances"},
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
            
            # Hidden store for goal view mode
            dcc.Store(id="goal-view-mode", data=True),
            
            # Hidden store for USD/EUR toggle state
            dcc.Store(id="usd-toggle-state", data=False)
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
            ctx = dash.ctx
            #Για το πρωτο render
            if ctx.triggered_id is None:
                return "tickers", "nav-item active", "nav-item", "nav-item", "nav-item", "nav-item settings-button"
                
            page_map = {
                "nav-tickers": "tickers",
                "nav-portfolio": "portfolio", 
                "nav-trades": "trades",
                "nav-finances": "finances",
                "nav-settings": "settings"
            }
            
            active_page = page_map.get(ctx.triggered_id, "tickers")
            
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
                    "subtitle": "Complete transaction log"
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
            [Input("active-page", "data"),
             Input("usd-toggle-state", "data")]
        )
        def render_dashboard_summary(page_name: str, include_usd: bool):
            """Render dashboard summary cards."""
            # Only show summary for portfolio page
            if page_name != "portfolio":
                return html.Div()
            
            try:
                portfolio = self.portfolio_service.get_portfolio_snapshot()
                return self.ui_factory.create_portfolio_summary(portfolio, include_usd=include_usd)
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
            """Διαχειρίζεται την εμφάνιση/κρύψιμο του modal για το Goals section."""
            ctx = dash.ctx
            if ctx.triggered_id is None:
                raise PreventUpdate
            
            # Επιτρέπουμε δράση μόνο στη σελίδα portfolio
            if active_page != "portfolio":
                raise PreventUpdate
            
            trigger_id = ctx.triggered_id
            
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
            State("goal-setup-modal", "style"),
            prevent_initial_call=True
        )
        def update_milestone_inputs(milestone_count, add_clicks, modal_style):
            """Ενημερώνει τα milestone inputs μόνο όταν το modal είναι ανοικτό ή όταν πατηθεί το add."""
            ctx = dash.ctx
            if ctx.triggered_id is None:
                raise PreventUpdate
            
            trigger_id = ctx.triggered_id
            
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
            """Εναλλάσσει τον τρόπο προβολής του goal
            Overall progress <--> Next milestone."""
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
        
        # Professional chart system callbacks for portfolio
        @self.app.callback(
            [Output("portfolio-active-timeframe", "data"),
            Output("portfolio-timeframe-1M", "className"),
            Output("portfolio-timeframe-3M", "className"),
            Output("portfolio-timeframe-6M", "className"),
            Output("portfolio-timeframe-1Y", "className"),
            Output("portfolio-timeframe-All", "className")],
            [Input("portfolio-timeframe-1M", "n_clicks"),
            Input("portfolio-timeframe-3M", "n_clicks"),
            Input("portfolio-timeframe-6M", "n_clicks"),
            Input("portfolio-timeframe-1Y", "n_clicks"),
            Input("portfolio-timeframe-All", "n_clicks")],
            [State("active-page", "data")],
            prevent_initial_call=True
        )
        def update_portfolio_timeframe(btn_1m, btn_3m, btn_6m, btn_1y, btn_all, active_page):
            """Update active timeframe based on button clicks for portfolio charts."""
            if active_page != "portfolio":
                raise PreventUpdate
                
            ctx = dash.ctx
            if ctx.triggered_id is None:
                raise PreventUpdate
            
            button_id = ctx.triggered_id
            timeframe_map = {
                "portfolio-timeframe-1M": "1M",
                "portfolio-timeframe-3M": "3M", 
                "portfolio-timeframe-6M": "6M",
                "portfolio-timeframe-1Y": "1Y",
                "portfolio-timeframe-All": "All"
            }
            
            active_timeframe = timeframe_map.get(button_id, "All")
            
            # Set active classes
            classes = ["timeframe-btn"] * 5
            active_index = list(timeframe_map.values()).index(active_timeframe)
            classes[active_index] = "timeframe-btn active"
            
            return active_timeframe, *classes
        # Enhanced chart switching callback for portfolio page
        @self.app.callback(
            [Output("portfolio-dynamic-chart-container", "children"),
            Output("portfolio-dynamic-metrics-container", "children")],
            [Input("portfolio-chart-selector", "value"),
            Input("portfolio-active-timeframe", "data"),
            Input("include-usd-toggle", "value")],
            [State("active-page", "data")],
            prevent_initial_call=True
        )
        def update_portfolio_chart_and_metrics(chart_type, timeframe, include_values, active_page):
            """Update portfolio chart and metrics based on selections."""
            if active_page != "portfolio":
                raise PreventUpdate

            try:
                portfolio = self.portfolio_service.get_portfolio_snapshot()
                portfolio_page = self.page_factory.create_page("portfolio")
                include_usd = "include" in (include_values or [])

                if chart_type == "profit":
                    # Use enhanced profit chart with timeframe
                    enhanced_fig = portfolio_page._create_enhanced_profit_chart(
                        portfolio.tickers,
                        "Portfolio Profit History",
                        timeframe,
                        include_usd=include_usd
                    )
                    chart = self.ui_factory.create_chart_container(enhanced_fig)
                    metrics = portfolio_page._get_profit_metrics(portfolio, include_usd)

                elif chart_type == "yield":
                    # Use enhanced yield chart with timeframe
                    enhanced_fig = portfolio_page._create_enhanced_yield_chart(
                        portfolio,
                        timeframe,
                        include_usd=include_usd
                    )
                    chart = self.ui_factory.create_chart_container(enhanced_fig)
                    metrics = portfolio_page._get_yield_metrics(portfolio, include_usd)

                else:
                    raise PreventUpdate
                
                return chart, metrics
                
            except Exception as e:
                self.logger.error(f"Error updating portfolio chart: {e}")
                error_content = html.Div([
                    html.P("Error loading chart data", style={
                        "textAlign": "center",
                        "color": self.config.ui.colors["red"]
                    })
                ])
                return error_content, html.Div()
        
        # USD/EUR toggle state callback
        @self.app.callback(
            Output("usd-toggle-state", "data"),
            Input("include-usd-toggle", "value"),
            prevent_initial_call=True
        )
        def update_usd_toggle_state(include_values):
            """Update USD/EUR toggle state in global store."""
            return "include" in (include_values or [])
        
        # Portfolio tickers table callback
        @self.app.callback(
            Output("tickers-table-content", "children"),
            [Input("usd-toggle-state", "data"),
             Input("portfolio-tickers-data", "data")],
            [State("active-page", "data")],
            prevent_initial_call=True
        )
        def update_portfolio_tickers_table(include_usd: bool, portfolio_data, active_page):
            """Update portfolio tickers table based on USD/EUR toggle state."""
            if active_page != "portfolio" or portfolio_data is None:
                raise PreventUpdate
            
            # Reconstruct tickers from stored data
            from models.portfolio import TickerData, PerformanceMetrics
            import pandas as pd
            import numpy as np
            from datetime import datetime
            
            tickers = []
            for ticker_data in portfolio_data["tickers"]:
                # Create price history with latest price
                price_df = pd.DataFrame({
                    'Close': [ticker_data["latest_price"]]
                }, index=[datetime.now()])
                
                # Create minimal TickerData for table display
                ticker = TickerData(
                    symbol=ticker_data["symbol"],
                    price_history=price_df,
                    dca_history=[ticker_data["average_buy_price"]],
                    shares_per_day=[ticker_data["total_shares"]],
                    profit_series=np.array([ticker_data["profit_absolute"]]),
                    buy_dates=[datetime.now()],  # Dummy date
                    buy_prices=[ticker_data["average_buy_price"]],
                    buy_quantities=[ticker_data["total_shares"]],
                    metrics=PerformanceMetrics(
                        invested=0,
                        current_value=ticker_data["current_value"],
                        profit_absolute=ticker_data["profit_absolute"],
                        return_percentage=ticker_data["return_percentage"],
                        average_buy_price=ticker_data["average_buy_price"]
                    )
                )
                tickers.append(ticker)
            
            return self.ui_factory.create_tickers_table(
                tickers=tickers,
                total_portfolio_value=portfolio_data["total_portfolio_value"],
                include_usd=include_usd
            )
        
        # Tickers page callbacks
        @self.app.callback(
            [Output("tickers-active-timeframe", "data"),
            Output("tickers-timeframe-1M", "className"),
            Output("tickers-timeframe-3M", "className"),
            Output("tickers-timeframe-6M", "className"),
            Output("tickers-timeframe-1Y", "className"),
            Output("tickers-timeframe-All", "className")],
            [Input("tickers-timeframe-1M", "n_clicks"),
            Input("tickers-timeframe-3M", "n_clicks"),
            Input("tickers-timeframe-6M", "n_clicks"),
            Input("tickers-timeframe-1Y", "n_clicks"),
            Input("tickers-timeframe-All", "n_clicks")],
            [State("active-page", "data")],
            prevent_initial_call=True
        )
        def update_tickers_timeframe(btn_1m, btn_3m, btn_6m, btn_1y, btn_all, active_page):
            """Update active timeframe for tickers charts."""
            if active_page != "tickers":
                raise PreventUpdate
                
            ctx = dash.ctx
            if ctx.triggered_id is None:
                raise PreventUpdate
            
            button_id = ctx.triggered_id
            timeframe_map = {
                "tickers-timeframe-1M": "1M",
                "tickers-timeframe-3M": "3M", 
                "tickers-timeframe-6M": "6M",
                "tickers-timeframe-1Y": "1Y",
                "tickers-timeframe-All": "All"
            }
            
            active_timeframe = timeframe_map.get(button_id, "All")
            
            # Set active classes
            classes = ["timeframe-btn"] * 5
            active_index = list(timeframe_map.values()).index(active_timeframe)
            classes[active_index] = "timeframe-btn active"
            
            return active_timeframe, *classes
        
        @self.app.callback(
            Output("tickers-active-ticker", "data"),
            [Input("ticker-selector", "value")],
            [State("active-page", "data")],
            prevent_initial_call=True
        )
        def update_active_ticker(selected_ticker, active_page):
            """Update active ticker selection."""
            if active_page != "tickers":
                raise PreventUpdate
            return selected_ticker
        
        @self.app.callback(
            Output("ticker-performance-cards", "children"),
            [Input("ticker-selector", "value")],
            [State("active-page", "data")],
            prevent_initial_call=True
        )
        def update_ticker_performance_cards(selected_ticker, active_page):
            """Update performance cards based on selected ticker."""
            if active_page != "tickers" or not selected_ticker:
                raise PreventUpdate
            
            try:
                portfolio = self.portfolio_service.get_portfolio_snapshot()
                ticker_data = next((t for t in portfolio.tickers if t.symbol == selected_ticker), None)
                
                if ticker_data:
                    return self.ui_factory.create_enhanced_performance_cards(ticker_data.metrics)
                else:
                    return html.Div("Ticker not found")
                    
            except Exception as e:
                self.logger.error(f"Error updating ticker performance cards: {e}")
                return html.Div("Error loading ticker data")
        
        @self.app.callback(
            Output("ticker-trade-details", "children"),
            [Input("ticker-selector", "value")],
            [State("active-page", "data")],
            prevent_initial_call=True
        )
        def update_ticker_trade_details(selected_ticker, active_page):
            """Update trade details card based on selected ticker."""
            if active_page != "tickers" or not selected_ticker:
                raise PreventUpdate
            
            try:
                portfolio = self.portfolio_service.get_portfolio_snapshot()
                ticker_data = next((t for t in portfolio.tickers if t.symbol == selected_ticker), None)
                
                if ticker_data:
                    return self.ui_factory.create_ticker_trade_details(
                        len(ticker_data.buy_dates),
                        int(sum(ticker_data.buy_quantities))
                    )
                else:
                    return html.Div("Ticker not found")
                    
            except Exception as e:
                self.logger.error(f"Error updating ticker trade details: {e}")
                return html.Div("Error loading ticker trade details")
        
        @self.app.callback(
            Output("ticker-recent-trade", "children"),
            [Input("ticker-selector", "value")],
            [State("active-page", "data")],
            prevent_initial_call=True
        )
        def update_ticker_recent_trade(selected_ticker, active_page):
            """Update recent trade card based on selected ticker."""
            if active_page != "tickers" or not selected_ticker:
                raise PreventUpdate
            
            try:
                portfolio = self.portfolio_service.get_portfolio_snapshot()
                ticker_data = next((t for t in portfolio.tickers if t.symbol == selected_ticker), None)
                
                if ticker_data and ticker_data.has_trades:
                    recent_date = ticker_data.buy_dates[0]
                    recent_price = ticker_data.buy_prices[0]
                    recent_quantity = ticker_data.buy_quantities[0]
                    
                    return self.ui_factory.create_recent_trade_card(
                        date=recent_date.strftime("%Y-%m-%d"),
                        trade_type="Buy",
                        quantity=recent_quantity,
                        price=recent_price
                    )
                else:
                    return html.Div([
                        html.H3("Recent Trade", style={
                            "color": self.ui_factory.colors["accent"],
                            "textAlign": "center"
                        }),
                        html.P("No trades available", style={
                            "textAlign": "center",
                            "color": self.ui_factory.colors["text_secondary"]
                        })
                    ], style=self.ui_factory.config.ui.card_style)
                    
            except Exception as e:
                self.logger.error(f"Error updating ticker recent trade: {e}")
                return html.Div("Error loading recent trade")
        
        @self.app.callback(
            [Output("tickers-dynamic-chart-container", "children"),
            Output("tickers-dynamic-metrics-container", "children")],
            [Input("tickers-chart-selector", "value"),
            Input("tickers-active-timeframe", "data"),
            Input("tickers-active-ticker", "data")],
            [State("active-page", "data")],
            prevent_initial_call=True
        )
        def update_tickers_chart_and_metrics(chart_type, timeframe, selected_ticker, active_page):
            """Update tickers chart and metrics based on selections."""
            if active_page != "tickers" or not selected_ticker:
                raise PreventUpdate
            
            try:
                portfolio = self.portfolio_service.get_portfolio_snapshot()
                ticker_data = next((t for t in portfolio.tickers if t.symbol == selected_ticker), None)
                
                if not ticker_data:
                    error_content = html.Div([
                        html.P("Ticker not found", style={
                            "textAlign": "center",
                            "color": self.config.ui.colors["red"]
                        })
                    ])
                    return error_content, html.Div()
                
                tickers_page = self.page_factory.create_page("tickers")
                
                if chart_type == "price":
                    chart_fig = tickers_page._create_price_chart(ticker_data, timeframe)
                    chart = self.ui_factory.create_chart_container(chart_fig)
                    metrics = tickers_page._get_price_metrics(ticker_data, timeframe)
                    
                elif chart_type == "profit":
                    chart_fig = tickers_page._create_profit_chart(ticker_data, timeframe)
                    chart = self.ui_factory.create_chart_container(chart_fig)
                    metrics = tickers_page._get_profit_metrics(ticker_data, timeframe)
                    
                elif chart_type == "volume":
                    chart_fig = tickers_page._create_volume_chart(ticker_data, timeframe)
                    chart = self.ui_factory.create_chart_container(chart_fig)
                    metrics = tickers_page._get_volume_metrics(ticker_data, timeframe)
                    
                else:
                    raise PreventUpdate
                
                return chart, metrics
                
            except Exception as e:
                self.logger.error(f"Error updating tickers chart: {e}")
                error_content = html.Div([
                    html.P("Error loading chart data", style={
                        "textAlign": "center",
                        "color": self.config.ui.colors["red"]
                    })
                ])
                return error_content, html.Div()
        
        
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
    def run(self, debug: bool = True, host: str = "0.0.0.0", port: int = 8051):
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
