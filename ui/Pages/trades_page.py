from dash import html, dash_table
import pandas as pd
import logging

from ui.Pages.base_page import BasePage
from services.portfolio_service import PortfolioService
from ui.Components import UIComponentFactory

logger = logging.getLogger(__name__)

class TradesPage(BasePage):
    """Trading history page."""
    
    def __init__(self, portfolio_service: PortfolioService, ui_factory: UIComponentFactory):
        super().__init__(ui_factory)
        self.portfolio_service = portfolio_service
    
    def render(self) -> html.Div:
        """Render trades history table."""
        try:
            # Load trades data for display
            df = pd.read_excel(self.config.database.trades_xlsx_path)
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.sort_values("Date", ascending=False)

            # Calculate P&L for each trade using the calculation service
            calculator = self.ui_factory.calculator
            df_with_pnl = calculator.calculate_trade_pnl(df, self.portfolio_service)
            
            # Clean up columns for display
            columns_to_remove = ["Number", "Settlement Date", "settlement date", "Fee", "Amount"]
            display_df = df_with_pnl.drop(columns=columns_to_remove, errors='ignore')
            display_df = display_df.copy()
            display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
            
            # Format P&L column to 2 decimal places
            if 'P&L' in display_df.columns:
                display_df['P&L'] = display_df['P&L'].round(2)
            
            # Remove original Profit column if it exists (we're replacing it with calculated P&L)
            if 'Profit' in display_df.columns:
                display_df = display_df.drop(columns=['Profit'])
                
            # Create data table with enhanced conditional formatting for P&L
            table = dash_table.DataTable(
                columns=[{"name": col, "id": col, "type": "numeric", "format": {"specifier": ".2f"}} if col == "P&L" 
                        else {"name": col, "id": col} for col in display_df.columns],
                data=display_df.to_dict("records"),
                sort_action="native",
                filter_action="native",
                page_size=25,
                style_table={"overflowX": "auto"},
                style_header={
                    "backgroundColor": self.colors["card_bg"],
                    "color": self.colors["text_primary"],
                    "fontWeight": "bold",
                    "textAlign": "center"
                },
                style_cell={
                    "backgroundColor": self.colors["background"],
                    "color": self.colors["text_primary"],
                    "textAlign": "left",
                    "padding": "12px",
                    "border": f"1px solid {self.colors['grid']}"
                },
                style_data_conditional=[
                    # Buy trades - light green background
                    {
                        'if': {'filter_query': '{Direction} = Buy'},
                        'backgroundColor': f'{self.colors["green"]}20',
                        'color': self.colors["green"],
                    },
                    # Sell trades - light red background
                    {
                        'if': {'filter_query': '{Direction} = Sell'},
                        'backgroundColor': f'{self.colors["red"]}20',
                        'color': self.colors["red"],
                    },
                    # Positive P&L - green text
                    {
                        'if': {
                            'filter_query': '{P&L} > 0',
                            'column_id': 'P&L'
                        },
                        'color': self.colors["green"],
                        'fontWeight': 'bold'
                    },
                    # Negative P&L - red text
                    {
                        'if': {
                            'filter_query': '{P&L} < 0',
                            'column_id': 'P&L'
                        },
                        'color': self.colors["red"],
                        'fontWeight': 'bold'
                    },
                    # Zero P&L - neutral color
                    {
                        'if': {
                            'filter_query': '{P&L} = 0',
                            'column_id': 'P&L'
                        },
                        'color': self.colors["text_secondary"],
                        'fontStyle': 'italic'
                    }
                ]
            )
            
            # Get portfolio data for summary statistics
            portfolio = self.portfolio_service.get_portfolio_snapshot()
            
            # Create summary statistics using portfolio data
            total_trades = len(df)
            unique_tickers = df['Ticker'].nunique()
            total_invested = portfolio.total_metrics.invested  # Use calculated value
            
            summary_cards = html.Div([
                self.ui_factory.create_metric_card("Total Trades", str(total_trades)),
                self.ui_factory.create_metric_card("Unique Tickers", str(unique_tickers)),
                self.ui_factory.create_metric_card("Total Invested", f"${total_invested:.2f}"),
                self.ui_factory.create_metric_card(
                    "Date Range", 
                    f"{df['Date'].min().strftime('%b %Y')} - {df['Date'].max().strftime('%b %Y')}"
                )
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "flexWrap": "wrap",
                "marginBottom": "30px"
            })
            
            return html.Div([
                html.H2("Trading History", style={
                    "textAlign": "center",
                    "color": self.colors["accent"],
                    "marginBottom": "30px"
                }),
                
                summary_cards,
                
                html.Div([
                    table
                ], style={
                    **self.config.ui.card_style,
                    "padding": "20px"
                })
            ])
            
        except Exception as e:
            logger.error(f"Error rendering trades page: {e}")
            return html.Div([
                html.H3("Error Loading Trades", style={
                    "color": self.colors["red"],
                    "textAlign": "center"
                }),
                html.P(f"Could not load trades data: {str(e)}", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style=self.config.ui.card_style)
