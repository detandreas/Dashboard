from dash import html, dcc
import logging
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

from ui.Pages.base_page import BasePage
from models.portfolio import TickerData, PortfolioSnapshot
from services.portfolio_service import PortfolioService
from ui.Components import UIComponentFactory

logger = logging.getLogger(__name__)

class TickersPage(BasePage):
    """Individual ticker analysis page."""
    
    def __init__(self, portfolio_service: PortfolioService, ui_factory: UIComponentFactory):
        super().__init__(ui_factory)
        self.portfolio_service = portfolio_service
    
    def render(self) -> html.Div:
        """Render tickers analysis with professional chart structure."""
        try:
            portfolio = self.portfolio_service.get_portfolio_snapshot()
            
            # Filter tickers with trades
            traded_tickers = [ticker for ticker in portfolio.tickers if ticker.has_trades]
            
            if not traded_tickers:
                return self._create_no_data_message("No ticker data available")
            
            sections = [
                # Ticker selector and overview cards
                self._create_ticker_overview_section(traded_tickers),
                # Combined chart section with dropdown
                self._create_combined_chart_section(portfolio, traded_tickers)
            ]
            
            return html.Div(sections)
            
        except Exception as e:
            logger.error(f"Error rendering tickers page: {e}")
            return self._create_error_message(str(e))
    
    def _create_ticker_overview_section(self, traded_tickers) -> html.Div:
        """Create ticker overview section with selector and cards."""
        # Create ticker selector dropdown
        ticker_options = [
            {"label": f"{ticker.symbol}", "value": ticker.symbol}
            for ticker in traded_tickers
        ]
        
        # Default to first ticker
        default_ticker = traded_tickers[0]
        
        return html.Div([
            # Ticker selector - aligned with main content layout
            html.Div([
                html.H3("Select Ticker", style={
                    "color": self.colors["accent"],
                    "marginBottom": "20px",
                    "fontSize": "1.3rem",
                    "fontWeight": "600"
                }),
                dcc.Dropdown(
                    id="ticker-selector",
                    options=ticker_options,
                    value=default_ticker.symbol,
                    className="custom-dropdown",
                    style={
                        "marginBottom": "10px",
                        "fontSize": "1rem"
                    }
                )
            ], style={
                **self.config.ui.card_style,
                "margin": "0",
                "marginBottom": "20px",
                "padding": "20px",
            }),
            
            # Performance cards for selected ticker
            html.Div(
                self.ui_factory.create_enhanced_performance_cards(default_ticker.metrics),
                id="ticker-performance-cards"
            )
        ])
    
    def _create_combined_chart_section(self, portfolio: PortfolioSnapshot, traded_tickers) -> html.Div:
        """Create combined chart section using utility functions."""
        default_ticker = traded_tickers[0]
        
        # Generate initial content
        try:
            initial_chart_fig = self._create_price_chart(default_ticker, "All")
            initial_chart = self.ui_factory.create_chart_container(initial_chart_fig)
            initial_metrics = self._get_price_metrics(default_ticker, "All")
        except Exception as e:
            logger.error(f"Error creating initial ticker chart: {e}")
            initial_chart = html.Div([
                html.P("Error loading chart", style={
                    "textAlign": "center",
                    "color": self.colors["red"]
                })
            ])
            initial_metrics = html.Div()
        
        # Use utility functions
        chart_dropdown = self.ui_factory.create_chart_dropdown(
            chart_id_prefix="tickers",
            chart_options=[
                {"label": "Price Analysis", "value": "price"},
                {"label": "Profit History", "value": "profit"},
                {"label": "Volume Analysis", "value": "volume"}
            ],
            default_chart="price"
        )
        
        timeframe_buttons = self.ui_factory.create_timeframe_buttons("tickers")
        
        stores = [
            dcc.Store(id="tickers-active-timeframe", data="All"),
            dcc.Store(id="tickers-active-ticker", data=default_ticker.symbol)
        ]
        
        return self.ui_factory.create_chart_layout(
            chart_id_prefix="tickers",
            chart_dropdown=chart_dropdown,
            timeframe_buttons=timeframe_buttons,
            initial_chart=initial_chart,
            initial_metrics=initial_metrics,
            stores=stores
        )
    
    def _create_price_chart(self, ticker_data: TickerData, timeframe: str = "All") -> go.Figure:
        """Create enhanced price chart with timeframe filtering."""
        try:
            # Apply timeframe filter
            if timeframe != "All" and ticker_data.price_history is not None:
                dates, filtered_prices = self._filter_data_by_timeframe(
                    ticker_data.price_history.index, 
                    ticker_data.price_history["Close"], 
                    timeframe
                )
                
                # Filter other data accordingly
                if ticker_data.has_trades and len(ticker_data.dca_history) > 0:
                    _, filtered_dca = self._filter_data_by_timeframe(
                        ticker_data.price_history.index,
                        ticker_data.dca_history,
                        timeframe
                    )
                else:
                    filtered_dca = []
            else:
                dates = ticker_data.price_history.index if ticker_data.price_history is not None else []
                filtered_prices = ticker_data.price_history["Close"] if ticker_data.price_history is not None else []
                filtered_dca = ticker_data.dca_history if ticker_data.has_trades else []
            
            fig = go.Figure()
            
            # Add price line
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=filtered_prices,
                    name="Close Price",
                    line=dict(width=3, color=self.colors["accent"]),
                    hovertemplate='<b>Close Price</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Price: $%{y:.2f}<extra></extra>',
                )
            )
            
            # Add DCA line if available
            if ticker_data.has_trades and len(filtered_dca) > 0:
                # Filter out NaN values for DCA line display
                valid_dca_mask = ~np.isnan(filtered_dca)
                if np.any(valid_dca_mask):
                    valid_dates = np.array(dates)[valid_dca_mask]
                    valid_dca = np.array(filtered_dca)[valid_dca_mask]
                    
                    fig.add_trace(
                        go.Scatter(
                            x=valid_dates,
                            y=valid_dca,
                            name="DCA Price",
                            line=dict(width=2, dash="dash", color=self.colors["green"]),
                            hovertemplate='<b>Dollar Cost Average</b><br>'
                            + 'Date: %{x|%d %b %Y}<br>'
                            + 'DCA: $%{y:.2f}<extra></extra>',
                        )
                    )
                
                # Filter buy orders for timeframe
                if len(ticker_data.buy_dates) > 0:
                    # Use the same timeframe filtering logic as the price data
                    if timeframe != "All":
                        end_date = ticker_data.price_history.index[-1]
                        # Use end of day for end_date to include all trades on the last day
                        end_date = end_date.replace(hour=23, minute=59, second=59)
                        
                        if timeframe == "1M":
                            start_date = end_date - timedelta(days=30)
                        elif timeframe == "3M":
                            start_date = end_date - timedelta(days=90)
                        elif timeframe == "6M":
                            start_date = end_date - timedelta(days=180)
                        elif timeframe == "1Y":
                            start_date = end_date - timedelta(days=365)
                        else:
                            start_date = ticker_data.price_history.index[0]
                        
                        buy_mask = [date >= start_date and date <= end_date for date in ticker_data.buy_dates]
                    else:
                        buy_mask = [True] * len(ticker_data.buy_dates)
                    
                    filtered_buy_dates = [date for i, date in enumerate(ticker_data.buy_dates) if buy_mask[i]]
                    filtered_buy_prices = [price for i, price in enumerate(ticker_data.buy_prices) if buy_mask[i]]
                    
                    if filtered_buy_dates:
                        fig.add_trace(
                            go.Scatter(
                                x=filtered_buy_dates,
                                y=filtered_buy_prices,
                                mode="markers",
                                name="Buy Orders",
                                marker=dict(
                                    size=12, color=self.colors["red"], symbol="triangle-up"
                                ),
                                hovertemplate='<b>Buy Order</b><br>'
                                + 'Date: %{x|%d %b %Y}<br>'
                                + 'Price: $%{y:.2f}<extra></extra>',
                            )
                        )
            
            dtick = self.config.market.y_axis_ticks.get(ticker_data.symbol, 1)
            
            fig.update_layout(
                height=500,
                template="plotly_dark",
                title={
                    "text": f"{ticker_data.symbol} Price Analysis",
                    "font": {"size": 20, "color": self.colors["text_primary"]},
                    "y": 0.95,
                    "x": 0.5,
                    "xanchor": "center",
                    "yanchor": "top",
                },
                xaxis_title="Date",
                yaxis_title="Price ($)",
                legend={
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "center",
                    "x": 0.5,
                },
                yaxis=dict(
                    dtick=dtick,
                    showgrid=True,
                    gridcolor=self.colors["grid"],
                    zeroline=True,
                    zerolinecolor=self.colors["text_secondary"],
                ),
                xaxis=dict(
                    showgrid=True, 
                    gridcolor=self.colors["grid"],
                    type="date"
                ),
                plot_bgcolor=self.colors["card_bg"],
                paper_bgcolor=self.colors["card_bg"],
                font=dict(color=self.colors["text_primary"]),
                hovermode="x unified",
                margin=dict(l=60, r=40, t=80, b=60),
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating price chart for {ticker_data.symbol}: {e}")
            return go.Figure().update_layout(
                title=f"Error loading chart for {ticker_data.symbol}",
                template="plotly_dark"
            )
    
    def _create_profit_chart(self, ticker_data: TickerData, timeframe: str = "All") -> go.Figure:
        """Create profit history chart for individual ticker."""
        try:
            if not ticker_data.has_trades or ticker_data.price_history is None:
                return go.Figure().update_layout(
                    title=f"No trade data available for {ticker_data.symbol}",
                    template="plotly_dark"
                )
            
            dates = ticker_data.price_history.index
            profit_series = ticker_data.profit_series
            
            # Apply timeframe filter
            if timeframe != "All":
                dates, profit_series = self._filter_data_by_timeframe(dates, profit_series, timeframe)
            
            # Find extrema for the filtered data
            (max_val, max_date), (min_val, min_date) = self.ui_factory.calculator.find_extrema(
                profit_series, dates
            )
            
            fig = go.Figure()
            
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=profit_series,
                    name=f"{ticker_data.symbol} Profit",
                    fill='tonexty' if min(profit_series) < 0 else 'tozeroy',
                    fillcolor='rgba(99, 102, 241, 0.2)',
                    line=dict(width=3, color=self.colors["accent"]),
                    hovertemplate='<b>Profit</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Profit: $%{y:,.2f}<extra></extra>',
                )
            )
            
            # Add max profit marker
            fig.add_trace(
                go.Scatter(
                    x=[max_date],
                    y=[max_val],
                    mode="markers",
                    name="Maximum Profit",
                    marker=dict(size=14, color=self.colors["green"]),
                    hovertemplate='<b>Maximum Profit</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Profit: $%{y:,.2f}<extra></extra>',
                )
            )
            
            # Add min profit marker
            fig.add_trace(
                go.Scatter(
                    x=[min_date],
                    y=[min_val],
                    mode="markers",
                    name="Minimum Profit",
                    marker=dict(size=14, color=self.colors["red"]),
                    hovertemplate='<b>Minimum Profit</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Profit: $%{y:,.2f}<extra></extra>',
                )
            )
            
            # Add zero line
            fig.add_shape(
                type="line",
                x0=dates[0], x1=dates[-1],
                y0=0, y1=0,
                line=dict(color="rgba(255,255,255,0.3)", width=1, dash="dot")
            )
            
            fig.update_layout(
                height=500,
                template="plotly_dark",
                title={
                    "text": f"{ticker_data.symbol} Profit History",
                    "font": {"size": 20, "color": self.colors["text_primary"]},
                    "y": 0.95,
                    "x": 0.5,
                    "xanchor": "center",
                    "yanchor": "top",
                },
                xaxis_title="Date",
                yaxis_title="Profit ($)",
                legend={
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "center",
                    "x": 0.5,
                },
                yaxis=dict(
                    showgrid=True,
                    gridcolor=self.colors["grid"],
                    zeroline=True,
                    zerolinecolor="rgba(255,255,255,0.3)",
                    zerolinewidth=1,
                ),
                xaxis=dict(
                    showgrid=True, 
                    gridcolor=self.colors["grid"],
                    type="date"
                ),
                plot_bgcolor=self.colors["card_bg"],
                paper_bgcolor=self.colors["card_bg"],
                font=dict(color=self.colors["text_primary"]),
                hovermode="x unified",
                margin=dict(l=60, r=40, t=80, b=60),
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating profit chart for {ticker_data.symbol}: {e}")
            return go.Figure().update_layout(
                title=f"Error loading profit chart for {ticker_data.symbol}",
                template="plotly_dark"
            )
    
    def _create_volume_chart(self, ticker_data: TickerData, timeframe: str = "All") -> go.Figure:
        """Create volume analysis chart."""
        try:
            if ticker_data.price_history is None or "Volume" not in ticker_data.price_history.columns:
                return go.Figure().update_layout(
                    title=f"No volume data available for {ticker_data.symbol}",
                    template="plotly_dark"
                )
            
            dates = ticker_data.price_history.index
            volume_series = ticker_data.price_history["Volume"]
            
            # Apply timeframe filter
            if timeframe != "All":
                dates, volume_series = self._filter_data_by_timeframe(dates, volume_series, timeframe)
            
            fig = go.Figure()
            
            fig.add_trace(
                go.Bar(
                    x=dates,
                    y=volume_series,
                    name="Volume",
                    marker_color=self.colors["accent"],
                    opacity=0.7,
                    hovertemplate='<b>Volume</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Volume: %{y:,.0f}<extra></extra>',
                )
            )
            
            fig.update_layout(
                height=500,
                template="plotly_dark",
                title={
                    "text": f"{ticker_data.symbol} Volume Analysis",
                    "font": {"size": 20, "color": self.colors["text_primary"]},
                    "y": 0.95,
                    "x": 0.5,
                    "xanchor": "center",
                    "yanchor": "top",
                },
                xaxis_title="Date",
                yaxis_title="Volume",
                yaxis=dict(
                    showgrid=True,
                    gridcolor=self.colors["grid"],
                ),
                xaxis=dict(
                    showgrid=True, 
                    gridcolor=self.colors["grid"],
                    type="date"
                ),
                plot_bgcolor=self.colors["card_bg"],
                paper_bgcolor=self.colors["card_bg"],
                font=dict(color=self.colors["text_primary"]),
                hovermode="x unified",
                margin=dict(l=60, r=40, t=80, b=60),
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating volume chart for {ticker_data.symbol}: {e}")
            return go.Figure().update_layout(
                title=f"Error loading volume chart for {ticker_data.symbol}",
                template="plotly_dark"
            )
    
    def _get_price_metrics(self, ticker_data: TickerData, timeframe: str = "All") -> html.Div:
        """Get price metrics for the side panel."""
        if ticker_data.price_history is None:
            return html.Div([
                html.P("No price data available", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style={
                "height": "525px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
        
        current_price = ticker_data.price_history["Close"][-1]
        price_series = ticker_data.price_history["Close"]
        max_price = price_series.max()
        min_price = price_series.min()
        
        # Calculate price change
        if len(price_series) > 1:
            price_change = ((current_price - price_series[-2]) / price_series[-2]) * 100
            price_change_color = self.colors["green"] if price_change >= 0 else self.colors["red"]
        else:
            price_change = 0
            price_change_color = self.colors["text_secondary"]
        
        return html.Div([
            html.H4("Price Analysis", style={
                "color": self.colors["accent"],
                "marginBottom": "20px",
                "textAlign": "center",
                "fontSize": "1rem"
            }),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Current Price",
                    f"${current_price:.2f}",
                    self.colors["accent"],
                    f"Change: {price_change:+.2f}%"
                )
            ], style={"marginBottom": "15px"}),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "52W High",
                    f"${max_price:.2f}",
                    self.colors["green"]
                )
            ], style={"marginBottom": "15px"}),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "52W Low",
                    f"${min_price:.2f}",
                    self.colors["red"]
                )
            ])
        ], style={
            "height": "525px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-evenly"
        })
    
    def _get_profit_metrics(self, ticker_data: TickerData, timeframe: str = "All") -> html.Div:
        """Get profit metrics for the side panel."""
        if not ticker_data.has_trades:
            return html.Div([
                html.P("No trade data available", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style={
                "height": "525px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
        
        metrics = ticker_data.metrics
        profit_color = self.colors["green"] if metrics.profit_absolute >= 0 else self.colors["red"]
        
        # Calculate profit analysis metrics using calculation service
        dates = ticker_data.price_history.index
        profit_series = ticker_data.profit_series
        
        profit_analysis = self.ui_factory.calculator.calculate_profit_analysis_metrics(
            profit_series, dates, timeframe
        )
        
        max_profit = profit_analysis['max_profit']
        min_profit = profit_analysis['min_profit']
        max_date = profit_analysis['max_date']
        min_date = profit_analysis['min_date']
        
        return html.Div([
            html.H4("Profit Analysis", style={
                "color": self.colors["accent"],
                "marginBottom": "20px",
                "textAlign": "center",
                "fontSize": "1rem"
            }),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Current Profit",
                    f"${metrics.profit_absolute:.2f}",
                    profit_color,
                    f"Return: {metrics.return_percentage:.2f}%"
                )
            ], style={"marginBottom": "15px"}),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Maximum Profit",
                    f"${max_profit:.2f}",
                    self.colors["green"],
                    f"Date: {max_date.strftime('%d %b %Y') if max_date else 'N/A'}"
                )
            ], style={"marginBottom": "15px"}),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Minimum Profit",
                    f"${min_profit:.2f}",
                    self.colors["red"],
                    f"Date: {min_date.strftime('%d %b %Y') if min_date else 'N/A'}"
                )
            ])
        ], style={
            "height": "525px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-evenly"
        })
    
    def _get_volume_metrics(self, ticker_data: TickerData, timeframe: str = "All") -> html.Div:
        """Get volume metrics for the side panel."""
        if ticker_data.price_history is None or "Volume" not in ticker_data.price_history.columns:
            return html.Div([
                html.P("No volume data available", style={
                    "textAlign": "center",
                    "color": self.colors["text_secondary"]
                })
            ], style={
                "height": "525px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
        
        volume_series = ticker_data.price_history["Volume"]
        current_volume = volume_series[-1]
        avg_volume = volume_series.mean()
        max_volume = volume_series.max()
        
        return html.Div([
            html.H4("Volume Analysis", style={
                "color": self.colors["accent"],
                "marginBottom": "20px",
                "textAlign": "center",
                "fontSize": "1rem"
            }),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Current Volume",
                    f"{current_volume:,.0f}",
                    self.colors["accent"]
                )
            ], style={"marginBottom": "15px"}),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Average Volume",
                    f"{avg_volume:,.0f}",
                    self.colors["text_primary"]
                )
            ], style={"marginBottom": "15px"}),
            html.Div([
                self.ui_factory.create_side_metric_card(
                    "Max Volume",
                    f"{max_volume:,.0f}",
                    self.colors["green"]
                )
            ])
        ], style={
            "height": "525px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-evenly"
        })
    
    def _filter_data_by_timeframe(self, dates, data_series, timeframe: str):
        """Filter data based on selected timeframe."""
        if timeframe == "All" or len(dates) == 0:
            return dates, data_series
        
        end_date = dates[-1]
        
        if timeframe == "1M":
            start_date = end_date - timedelta(days=30)
        elif timeframe == "3M":
            start_date = end_date - timedelta(days=90)
        elif timeframe == "6M":
            start_date = end_date - timedelta(days=180)
        elif timeframe == "1Y":
            start_date = end_date - timedelta(days=365)
        else:
            return dates, data_series
        
        # Filter dates and corresponding data
        mask = dates >= start_date
        filtered_dates = dates[mask]
        
        if isinstance(data_series, (list, np.ndarray)):
            filtered_data = np.array(data_series)[mask]
        else:
            filtered_data = data_series[mask]
        
        return filtered_dates, filtered_data
    
    def _create_no_data_message(self, message: str) -> html.Div:
        """Create no data available message."""
        return html.Div([
            html.H3("No Data Available", style={
                "textAlign": "center",
                "color": self.colors["text_secondary"]
            }),
            html.P(message, style={
                "textAlign": "center",
                "color": self.colors["text_secondary"]
            })
        ], style=self.config.ui.card_style)
    
    def _create_error_message(self, error: str) -> html.Div:
        """Create error message display."""
        return html.Div([
            html.H3("Error Loading Tickers", style={
                "color": self.colors["red"],
                "textAlign": "center"
            }),
            html.P(f"An error occurred: {error}", style={
                "textAlign": "center",
                "color": self.colors["text_secondary"]
            })
        ], style=self.config.ui.card_style)
