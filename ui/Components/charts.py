from dash import html, dcc
import plotly.graph_objects as go
from typing import List, Dict, Callable, Any, Optional
import logging
from abc import abstractmethod

from models.portfolio import TickerData

logger = logging.getLogger(__name__)


class ChartComponentsMixin:
    """Chart creation helpers."""

    def create_price_chart(self, ticker_data: TickerData) -> go.Figure:
        """Create interactive price chart with DCA and buy signals."""
        try:
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=ticker_data.price_history.index,
                    y=ticker_data.price_history["Close"],
                    name="Close Price",
                    line=dict(width=3, color=self.colors["accent"]),
                    hovertemplate='<b>Close Price</b><br>'
                    + 'Date: %{x|%d %b %Y}<br>'
                    + 'Price: $%{y:.2f}<extra></extra>',
                )
            )

            if ticker_data.has_trades:
                fig.add_trace(
                    go.Scatter(
                        x=ticker_data.price_history.index,
                        y=ticker_data.dca_history,
                        name="DCA Price",
                        line=dict(width=2, dash="dash", color=self.colors["green"]),
                        hovertemplate='<b>Dollar Cost Average</b><br>'
                        + 'Date: %{x|%d %b %Y}<br>'
                        + 'DCA: $%{y:.2f}<extra></extra>',
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=ticker_data.buy_dates,
                        y=ticker_data.buy_prices,
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

            dtick = self.config.market.y_axis_ticks.get(ticker_data.symbol)

            fig.update_layout(
                height=500,
                template="plotly_dark",
                title={
                    "text": f"{ticker_data.symbol} Performance Analysis",
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
                xaxis=dict(showgrid=True, gridcolor=self.colors["grid"]),
                plot_bgcolor=self.colors["card_bg"],
                paper_bgcolor=self.colors["card_bg"],
                font=dict(color=self.colors["text_primary"]),
                hovermode="x unified",
                margin=dict(l=60, r=40, t=80, b=60),
            )

            return fig

        except Exception as e:
            logger.error(
                "Error creating price chart for %s: %s", ticker_data.symbol, e
            )
            return go.Figure().update_layout(
                title=f"Error loading chart for {ticker_data.symbol}",
                template="plotly_dark",
            )

    def create_profit_chart(
        self, ticker_data_list: List[TickerData], title: str = "Portfolio Profit History"
    ) -> go.Figure:
        """Create portfolio profit progression chart."""
        try:
            fig = go.Figure()

            if ticker_data_list and ticker_data_list[0].price_history is not None:
                dates = ticker_data_list[0].price_history.index
                total_profit = sum(
                    ticker.profit_series for ticker in ticker_data_list
                )

                (max_val, max_date), (min_val, min_date) = self.calculator.find_extrema(
                    total_profit, dates
                )

                fig.add_trace(
                    go.Scatter(
                        x=dates,
                        y=total_profit,
                        name="Portfolio Profit",
                        line=dict(width=3, color=self.colors["accent"]),
                        hovertemplate='<b>Portfolio Profit</b><br>'
                        + 'Date: %{x|%d %b %Y}<br>'
                        + 'Profit: $%{y:,.2f}<extra></extra>',
                    )
                )

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

                fig.add_shape(
                    type="line",
                    x0=dates[0],
                    x1=dates[-1],
                    y0=0,
                    y1=0,
                    line=dict(color="white", width=1, dash="dot"),
                )

            fig.update_layout(
                height=500,
                template="plotly_dark",
                title={
                    "text": title,
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
                    dtick=self.config.market.portfolio_profit_tick,
                    showgrid=True,
                    gridcolor=self.colors["grid"],
                ),
                xaxis=dict(showgrid=True, gridcolor=self.colors["grid"]),
                plot_bgcolor=self.colors["card_bg"],
                paper_bgcolor=self.colors["card_bg"],
                font=dict(color=self.colors["text_primary"]),
                hovermode="x unified",
            )

            return fig

        except Exception as e:
            logger.error("Error creating profit chart: %s", e)
            return go.Figure().update_layout(
                title="Error loading profit chart", template="plotly_dark"
            )

    def create_chart_container(self, figure: go.Figure) -> html.Div:
        """Wrap chart in styled container."""
        return html.Div(
            [dcc.Graph(
                figure=figure,
                config={
                    'displayModeBar': False,  # Remove Plotly toolbar
                    'staticPlot': False,      # Keep interactivity
                    'responsive': True        # Responsive sizing
                }
            )],
            style={
                "backgroundColor": self.colors["card_bg"],
                "borderRadius": "12px",
                "boxShadow": "0 4px 12px rgba(0,0,0,0.3)",
                "border": "1px solid #333333",
                "marginBottom": "20px",
            },
        )

    def create_professional_chart_section(
        self,
        chart_id_prefix: str,
        chart_options: List[Dict[str, str]],
        default_chart: str,
        chart_generators: Dict[str, Callable],
        metrics_generators: Dict[str, Callable],
        data_context: Any,
        enable_timeframe: bool = True,
        timeframe_options: Optional[List[str]] = None
    ) -> html.Div:
        """
        Δημιουργεί επαγγελματική δομή chart με dropdown επιλογές και δυναμικά metrics.
        
        Args:
            chart_id_prefix: Prefix για τα IDs των components
            chart_options: Λίστα με τις επιλογές του dropdown [{"label": "...", "value": "..."}]
            default_chart: Default επιλογή chart
            chart_generators: Dictionary με functions που δημιουργούν charts {chart_type: function}
            metrics_generators: Dictionary με functions που δημιουργούν metrics {chart_type: function}
            data_context: Τα δεδομένα που χρειάζονται οι generators
            enable_timeframe: Αν θα εμφανίζονται τα timeframe buttons
            timeframe_options: Custom timeframe επιλογές (default: ["1M", "3M", "6M", "1Y", "All"])
        
        Returns:
            html.Div: Η πλήρης επαγγελματική δομή του chart section
        """
        if timeframe_options is None:
            timeframe_options = ["1M", "3M", "6M", "1Y", "All"]
        
        # Chart selector dropdown
        chart_selector = html.Div([
            dcc.Dropdown(
                id=f"{chart_id_prefix}-chart-selector",
                options=chart_options,
                value=default_chart,
                className="custom-dropdown chart-selector",
                style={"width": "280px"}
            )
        ], style={
            "position": "absolute",
            "top": "10px",
            "left": "10px",
            "zIndex": "1000"
        })
        
        # Timeframe buttons (conditional)
        timeframe_buttons = html.Div()
        if enable_timeframe:
            buttons = []
            for i, timeframe in enumerate(timeframe_options):
                is_active = timeframe == "All"  # Default active
                buttons.append(
                    html.Button(
                        timeframe,
                        id=f"{chart_id_prefix}-timeframe-{timeframe}",
                        className=f"timeframe-btn{' active' if is_active else ''}",
                        style={"marginRight": "5px" if i < len(timeframe_options) - 1 else "0"}
                    )
                )
            
            timeframe_buttons = html.Div(buttons, style={
                "position": "absolute",
                "top": "10px",
                "right": "10px",
                "zIndex": "1000",
                "display": "flex",
                "gap": "5px"
            })
        
        # Hidden stores for state management
        stores = [
            dcc.Store(id=f"{chart_id_prefix}-active-timeframe", data="All"),
            dcc.Store(id=f"{chart_id_prefix}-data-context", data=data_context),
            dcc.Store(id=f"{chart_id_prefix}-chart-generators", data=list(chart_generators.keys())),
            dcc.Store(id=f"{chart_id_prefix}-metrics-generators", data=list(metrics_generators.keys()))
        ]
        
        # Generate initial chart and metrics
        default_chart_generator = chart_generators.get(default_chart)
        default_metrics_generator = metrics_generators.get(default_chart)
        
        initial_chart = html.Div()
        initial_metrics = html.Div()
        
        if default_chart_generator and default_metrics_generator:
            try:
                # Generate initial chart - handle both portfolio and ticker contexts
                if hasattr(data_context, 'tickers'):  # Portfolio context
                    chart_fig = default_chart_generator(data_context, "All")
                    initial_metrics = default_metrics_generator(data_context)
                elif hasattr(data_context, 'symbol'):  # Single ticker context
                    chart_fig = default_chart_generator(data_context, "All")
                    initial_metrics = default_metrics_generator(data_context)
                else:  # Generic context
                    chart_fig = default_chart_generator(data_context, "All")
                    initial_metrics = default_metrics_generator(data_context)
                
                initial_chart = self.create_chart_container(chart_fig)
                
            except Exception as e:
                logger.error(f"Error generating initial chart content: {e}")
                initial_chart = html.Div([
                    html.P("Error loading chart", style={
                        "textAlign": "center",
                        "color": self.colors["red"]
                    })
                ])
                initial_metrics = html.Div()

        return html.Div([
            # Chart and metrics container
            html.Div([
                # Chart container (left side, wider)
                html.Div([
                    chart_selector,
                    timeframe_buttons,
                    *stores,
                    html.Div(
                        initial_chart,
                        id=f"{chart_id_prefix}-dynamic-chart-container"
                    )
                ], style={
                    "flex": "1 1 85%",
                    "maxWidth": "85%",
                    "minWidth": "500px",
                    "boxSizing": "border-box",
                    "position": "relative"
                }),
                
                # Metrics container (right side, narrower)
                html.Div([
                    html.Div(
                        initial_metrics,
                        id=f"{chart_id_prefix}-dynamic-metrics-container"
                    )
                ], style={
                    "flex": "1 1 15%",
                    "maxWidth": "15%",
                    "minWidth": "200px",
                    "boxSizing": "border-box",
                    "paddingLeft": "20px"
                })
                
            ], style={
                "display": "flex",
                "gap": "20px",
                "alignItems": "stretch"
            })
        ])

    def create_side_metric_card(
    self, 
    title: str, 
    value: str, 
    color: str, 
    subtitle: str = ""
    ) -> html.Div:
        """Δημιουργεί side metric card για τα metrics containers με hover animations."""
        return html.Div([
            html.Div([
                html.H5(title, style={
                    "color": self.colors["text_primary"],
                    "margin": "0 0 8px 0",
                    "fontSize": "0.9rem",
                    "fontWeight": "normal",
                    "position": "relative",
                    "zIndex": "1",
                    "transition": "all 0.3s ease"
                }),
                html.Div(value, style={
                    "color": color,
                    "fontSize": "1.1rem",
                    "fontWeight": "bold",
                    "marginBottom": "4px",
                    "position": "relative",
                    "zIndex": "1",
                    "transition": "all 0.3s ease"
                }),
                html.Div(subtitle, style={
                    "color": self.colors["text_secondary"],
                    "fontSize": "0.8rem",
                    "lineHeight": "1.2",
                    "position": "relative",
                    "zIndex": "1",
                    "transition": "all 0.3s ease"
                }) if subtitle else html.Div()
            ])
        ], 
        className="side-metric-card",
        style={
            "backgroundColor": self.colors["background"],
            "padding": "12px 15px",
            "borderRadius": "8px",
            "border": f"1px solid {self.colors['grid']}",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
            "transition": "all 0.3s ease",
            "position": "relative",
            "overflow": "hidden",
            "cursor": "pointer"
        })
    @abstractmethod
    def get_chart_generators(self) -> Dict[str, Callable]:
        """
        Abstract method που πρέπει να υλοποιηθεί από κάθε σελίδα.
        Επιστρέφει dictionary με chart generators.
        
        Returns:
            Dict[str, Callable]: {chart_type: generator_function}
        """
        pass

    @abstractmethod  
    def get_metrics_generators(self) -> Dict[str, Callable]:
        """
        Abstract method που πρέπει να υλοποιηθεί από κάθε σελίδα.
        Επιστρέφει dictionary με metrics generators.
        
        Returns:
            Dict[str, Callable]: {chart_type: metrics_generator_function}
        """
        pass

    # === UTILITY FUNCTIONS ΓΙΑ ΥΒΡΙΔΙΚΟ ΤΡΟΠΟ ===
    
    def create_chart_dropdown(
        self,
        chart_id_prefix: str,
        chart_options: List[Dict[str, str]],
        default_chart: str,
        width: str = "280px",
        position: str = "absolute"
    ) -> html.Div:
        """Δημιουργεί standardized chart selector dropdown."""

        # Define position styles based on position parameter
        if position == "absolute":
            position_style = {
                "position": "absolute",
                "top": "10px",
                "left": "10px",
                "zIndex": "1000"
            }
        elif position == "top-right":
            position_style = {
                "position": "absolute",
                "top": "-10px",
                "right": "5px",
                "zIndex": "1000"
            }
        return html.Div([
            dcc.Dropdown(
                id=f"{chart_id_prefix}-chart-selector",
                options=chart_options,
                value=default_chart,
                className="custom-dropdown chart-selector",
                style={"width": width},
                clearable=False,

            )
        ], style=position_style

        )
    
    def create_timeframe_buttons(
        self,
        chart_id_prefix: str,
        timeframe_options: Optional[List[str]] = None,
        default_active: str = "All"
    ) -> html.Div:
        """Δημιουργεί standardized timeframe buttons."""
        if timeframe_options is None:
            timeframe_options = ["1M", "3M", "6M", "1Y", "All"]
        
        buttons = []
        for i, timeframe in enumerate(timeframe_options):
            is_active = timeframe == default_active
            buttons.append(
                html.Button(
                    timeframe,
                    id=f"{chart_id_prefix}-timeframe-{timeframe}",
                    className=f"timeframe-btn{' active' if is_active else ''}",
                    style={"marginRight": "5px" if i < len(timeframe_options) - 1 else "0"}
                )
            )
        
        return html.Div(buttons, style={
            "position": "absolute",
            "top": "10px",
            "right": "10px",
            "zIndex": "1000",
            "display": "flex",
            "gap": "5px"
        })
    
    def create_chart_layout(
        self,
        chart_id_prefix: str,
        chart_dropdown: html.Div,
        timeframe_buttons: html.Div,
        initial_chart: html.Div,
        initial_metrics: html.Div,
        stores: List[dcc.Store] = None
    ) -> html.Div:
        """Δημιουργεί standardized chart layout structure."""
        if stores is None:
            stores = []
        
        return html.Div([
            # Chart and metrics container
            html.Div([
                # Chart container (left side, wider)
                html.Div([
                    chart_dropdown,
                    timeframe_buttons,
                    *stores,
                    html.Div(
                        initial_chart,
                        id=f"{chart_id_prefix}-dynamic-chart-container"
                    )
                ], style={
                    "flex": "1 1 85%",
                    "maxWidth": "85%",
                    "minWidth": "500px",
                    "boxSizing": "border-box",
                    "position": "relative"
                }),
                
                # Metrics container (right side, narrower)
                html.Div([
                    html.Div(
                        initial_metrics,
                        id=f"{chart_id_prefix}-dynamic-metrics-container"
                    )
                ], style={
                    "flex": "1 1 15%",
                    "maxWidth": "15%",
                    "minWidth": "200px",
                    "boxSizing": "border-box",
                    "paddingLeft": "20px"
                })
                
            ], style={
                "display": "flex",
                "gap": "20px",
                "alignItems": "stretch"
            })
        ])
    
    def create_metrics_container(
        self,
        title: str,
        metrics_cards: List[html.Div],
        container_height: str = "525px"
    ) -> html.Div:
        """Δημιουργεί standardized metrics container."""
        return html.Div([
            html.H4(title, style={
                "color": self.colors["accent"],
                "marginBottom": "20px",
                "textAlign": "center",
                "fontSize": "1rem"
            }),
            *[html.Div([card], style={"marginBottom": "15px"}) 
              for card in metrics_cards[:-1]],
            html.Div([metrics_cards[-1]]) if metrics_cards else html.Div()
        ], style={
            "height": container_height,
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-evenly"
        })
