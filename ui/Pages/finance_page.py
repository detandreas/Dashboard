from dash import html
import logging

from ui.Pages.base_page import BasePage
from ui.Components import UIComponentFactory
from config.settings import Config

logger = logging.getLogger(__name__)

class FinancePage(BasePage):
    """Personal finances page."""
    
    def __init__(self, ui_factory: UIComponentFactory, config: Config):
        super().__init__(ui_factory)
        self.config = config
    
    def render(self) -> html.Div:
        """Render personal finance page."""
        try:
            from services.finance_service import FinanceAnalysisService
            
            finance_service = FinanceAnalysisService(self.config)
            
            # Load data once with error handling
            try:
                df, month_columns = finance_service.load_finance_data()
            except Exception as e:
                error_msg = f"Error loading finance file: {str(e)}"
                return self.ui_factory.create_finance_error_display(
                    error_msg, 
                    self.config.database.finance_xlsx_path
                )
            
            if len(month_columns) == 0:
                return self.ui_factory.create_finance_no_data_display()
            
            # Extract financial data
            income_data, expenses_data, investments_data = finance_service.extract_financial_data(
                df, month_columns
            )
            
            # Calculate metrics
            metrics = finance_service.calculate_financial_metrics(
                income_data, expenses_data, investments_data
            )
            
            # Create main dashboard
            main_dashboard = self._create_main_finance_dashboard(
                finance_service, df, month_columns, income_data, expenses_data, investments_data, metrics
            )
            
            # Add individual charts section
            individual_charts = self._create_individual_charts_consolidated(
                finance_service, income_data, expenses_data, investments_data, month_columns
            )
            
            return html.Div([
                main_dashboard,
                html.Hr(style={
                    "margin": "40px 0",
                    "border": f"1px solid {self.colors['grid']}"
                }),
                individual_charts
            ])
            
        except ImportError as e:
            logger.error(f"Could not import finance service: {e}")
            return self._create_import_error()
        except Exception as e:
            logger.error(f"Error rendering finance page: {e}")
            return self._create_general_error(str(e))
    
    def _create_main_finance_dashboard(self, finance_service, df, month_columns, 
                                     income_data, expenses_data, investments_data, metrics) -> html.Div:
        """Create main finance dashboard with overview chart."""
        # Create overview chart
        overview_chart = finance_service.create_overview_chart(
            income_data, expenses_data, investments_data, month_columns, self.colors
        )
        
        return html.Div([
            html.H2("📊 Personal Finances Dashboard", style={
                "textAlign": "center", 
                "color": self.colors["accent"], 
                "marginBottom": "30px"
            }),
            
            # Metrics cards
            self.ui_factory.create_finance_metrics_cards(metrics),
            
            # Overview chart
            html.Div([
                self.ui_factory.create_chart_container(overview_chart)
            ], style={"marginBottom": "20px"})
        ])
    
    def _create_individual_charts_consolidated(self, finance_service, income_data, 
                                             expenses_data, investments_data, month_columns) -> html.Div:
        """Create individual charts using consolidated service."""
        try:
            # Create charts using service
            income_chart = finance_service.create_income_chart(income_data, month_columns, self.colors)
            expenses_chart = finance_service.create_expenses_chart(expenses_data, month_columns, self.colors)
            investments_chart = finance_service.create_investments_chart(investments_data, month_columns, self.colors)
            
            return html.Div([
                html.H3("Detailed Analysis", style={
                    "textAlign": "center",
                    "color": self.colors["accent"],
                    "marginBottom": "30px"
                }),
                
                # Income Chart
                html.Div([
                    self.ui_factory.create_chart_container(income_chart)
                ], style={"marginBottom": "30px"}),
                
                # Expenses Chart
                html.Div([
                    self.ui_factory.create_chart_container(expenses_chart)
                ], style={"marginBottom": "30px"}),
                
                # Investments Chart
                html.Div([
                    self.ui_factory.create_chart_container(investments_chart)
                ], style={"marginBottom": "30px"})
            ])
            
        except Exception as e:
            logger.error(f"Error creating individual charts: {e}")
            return html.Div([
                html.H3("Individual Charts Error", style={
                    "color": self.colors["red"],
                    "textAlign": "center"
                }),
                html.P(f"Could not load individual charts: {str(e)}", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style=self.config.ui.card_style)
    
    def _create_import_error(self) -> html.Div:
        """Create import error message."""
        return html.Div([
            html.H2("📊 Personal Finances Dashboard", style={
                "textAlign": "center", 
                "color": self.colors["accent"], 
                "marginBottom": "30px"
            }),
            html.Div([
                html.H4("Finance Module Not Available", style={"color": self.colors["red"]}),
                html.P("The finance page module could not be loaded.", style={
                    "color": self.colors["text_secondary"]
                }),
                html.P("Please ensure services/finance_service.py exists and is properly configured.", style={
                    "color": self.colors["text_secondary"]
                })
            ], style=self.config.ui.card_style)
        ])
    
    def _create_general_error(self, error_msg: str) -> html.Div:
        """Create general error message."""
        return html.Div([
            html.H2("📊 Personal Finances Dashboard", style={
                "textAlign": "center", 
                "color": self.colors["accent"], 
                "marginBottom": "30px"
            }),
            html.Div([
                html.H4("Error Loading Finance Data", style={"color": self.colors["red"]}),
                html.P(f"An error occurred: {error_msg}", style={
                    "color": self.colors["text_secondary"]
                })
            ], style=self.config.ui.card_style)
        ])
