import os
from datetime import datetime, timedelta

import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
import dash_bootstrap_components as dbc
from dash import dash_table

from buys import buys
from Dollar_cost_average import DCA
from growth import growth, portfolio_growth
from extrema import max_data, min_data

"""
Dashboard – two overall views
=============================
* **Dropdown** με 2 επιλογές:
  1. **Tickers (VUAA, EQAC, USD)** → εμφανίζει το ένα κάτω απ' το άλλο:
     - κάρτες Invested/Current/Profit/Return για κάθε ticker
     - γράφημα Price + DCA + Buys
  2. **Portfolio** → εμφανίζει συνοπτικές κάρτες χαρτοφυλακίου και δύο διαγράμματα:
     - Profit curve (ETF + USD)
     - Yield % curve (Profit / Invested ETFs)

* Στις κάρτες portfolio: Invested = κεφάλαιο μόνο ETF, Profit = P/L ETF + USD.
"""

# ---------------------------------------------------------------------------
# CONFIG --------------------------------------------------------------------
# ---------------------------------------------------------------------------

TRADES_XLSX = os.getenv("DASH_FILE_PATH", "Trades.xlsx")
TRACKED = {
    "VUAA.L": "VUAA.EU",
    "EQAC.SW": "EQAC.EU",
    "EUR=X"  : "USD/EUR",
}
START_DATE = "2024-06-01"

# y‑axis tick spacing settings ---------------------------------------------
Y_DTICKS = {
    "VUAA.EU": 5,     # €5 steps
    "EQAC.EU": 20,    # €20 steps
    "USD/EUR": 0.02,  # $0.02 steps (pair quoted in €)
}
PORT_PROFIT_DTICK = 100  # €100 steps
PORT_YIELD_DTICK = 2     # 2 percentage‑point steps

# ---------------------------------------------------------------------------
# HELPERS -------------------------------------------------------------------
# ---------------------------------------------------------------------------

def load_trades(path: str) -> pd.DataFrame:
    trades = pd.read_excel(path)
    trades["Date"] = pd.to_datetime(trades["Date"])
    return trades.pivot(index="Date", columns="Ticker",
                        values=["Price", "Direction", "Quantity"]).fillna(0)


def download_history(symbols: list[str]) -> dict[str, pd.DataFrame]:
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    frames = {}
    for sym in symbols:
        df = yf.download(sym, start=START_DATE, end=tomorrow, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        frames[sym] = df
    # keep dates common to all tickers so the curves align
    common = set.intersection(*(set(df.index) for df in frames.values()))
    for k in frames:
        frames[k] = frames[k].loc[sorted(common)]
    return frames


def prepare_ticker(yf_sym: str, excel_tic: str,
                   pivot: pd.DataFrame, prices: dict):
    price = prices[yf_sym]
    _, buy_dates, buy_prices, buy_qty, _, avg_buy = buys(pivot, excel_tic)
    dca, shares_day = DCA(price, buy_dates, buy_prices, buy_qty)
    profit_series = portfolio_growth(price, dca, shares_day)

    invested = sum(p * q for p, q in zip(buy_prices, buy_qty))
    last_close = price["Close"].iloc[-1]
    growth_pct = growth(last_close, avg_buy, buy_prices, buy_qty)
    current_val = invested * (1 + growth_pct)
    profit_abs = current_val - invested

    return {
        "price": price,
        "dca": dca,
        "buy_dates": buy_dates,
        "buy_prices": buy_prices,
        "shares": shares_day,
        "profit_series": profit_series,
        "invested": invested,
        "current": current_val,
        "profit_abs": profit_abs,
        "return_pct": growth_pct * 100,
    }

# ---------------------------------------------------------------------------
# LOAD DATA -----------------------------------------------------------------
# ---------------------------------------------------------------------------

pivot = load_trades(TRADES_XLSX)
prices = download_history(list(TRACKED.keys()))
ALL = {excel: prepare_ticker(yf_sym, excel, pivot, prices)
       for yf_sym, excel in TRACKED.items()}

idx = next(iter(prices.values())).index
EQUITY_TICKERS = [t for t in TRACKED.values() if t != "USD/EUR"]

# Portfolio series & snapshot
portfolio_profit = sum(ALL[t]["profit_series"] for t in ALL)
portfolio_invested_series = [
    sum(ALL[t]["dca"][i] * ALL[t]["shares"][i] for t in EQUITY_TICKERS)
    for i in range(len(idx))
]
portfolio_yield_series = [p / inv if inv else 0
                          for p, inv in zip(portfolio_profit,
                                            portfolio_invested_series)]

port_invested = sum(ALL[t]["invested"] for t in EQUITY_TICKERS)
port_profit_abs = portfolio_profit[-1]
port_current = port_invested + port_profit_abs
port_return_pct = port_profit_abs / port_invested * 100 if port_invested else 0

# ---------------------------------------------------------------------------
# FIGURES -------------------------------------------------------------------
# ---------------------------------------------------------------------------

def add_zero(fig):
    fig.add_shape(type="line", x0=idx[0], x1=idx[-1], y0=0, y1=0,
                  line=dict(color="white", width=2))
    return fig

# Portfolio figures ---------------------------------------------------------

p_max, p_max_dt = max_data(portfolio_profit, idx)
p_min, p_min_dt = min_data(portfolio_profit, idx)
fig_port_profit = go.Figure([
    go.Scatter(x=idx, y=portfolio_profit, name="Profit",
               line=dict(width=2), hovertemplate='%{y:.2f}€<extra></extra>'),
    go.Scatter(x=[p_max_dt], y=[p_max], mode="markers", name="Max",
               marker=dict(size=14, color="#00E676"), hovertemplate='%{y:.2f}€<extra></extra>'),
    go.Scatter(x=[p_min_dt], y=[p_min], mode="markers", name="Min",
               marker=dict(size=14, color="red"), hovertemplate='%{y:.2f}€<extra></extra>'),
]).update_layout(height=550, template="plotly_white", yaxis_title="€",
                 yaxis=dict(dtick=PORT_PROFIT_DTICK))
add_zero(fig_port_profit)

y_max, y_max_dt = max_data(portfolio_yield_series, idx)
y_min, y_min_dt = min_data(portfolio_yield_series, idx)
fig_port_yield = go.Figure([
    go.Scatter(x=idx, y=[y * 100 for y in portfolio_yield_series],
               name="Yield %", line=dict(width=2), hovertemplate='%{y:.2f}%<extra></extra>'),
    go.Scatter(x=[y_max_dt], y=[y_max * 100], mode="markers", name="Max",
               marker=dict(size=14, color="#00E676"), hovertemplate='%{y:.2f}%<extra></extra>'),
    go.Scatter(x=[y_min_dt], y=[y_min * 100], mode="markers", name="Min",
               marker=dict(size=14, color="red"), hovertemplate='%{y:.2f}%<extra></extra>'),
]).update_layout(height=550, template="plotly_white", yaxis_title="%",
                 yaxis=dict(dtick=PORT_YIELD_DTICK))
add_zero(fig_port_yield)

# ---------------------------------------------------------------------------
# DASH APP ------------------------------------------------------------------
# ---------------------------------------------------------------------------

app = dash.Dash(
    __name__,
    title="Andreas's Portfolio Tracker",
    meta_tags=[{"name": "viewport",
                "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
server = app.server

# Χρωματικό σχήμα
COLORS = {
    "primary": "#0D47A1",         # Πολύ σκούρο μπλε
    "secondary": "#00838F",       # Σκούρο τιρκουάζ
    "background": "#121212",      # Πολύ σκούρο γκρι φόντο (σχεδόν μαύρο)
    "card_bg": "#1E1E1E",         # Σκούρο γκρι για κάρτες
    "text_primary": "#FFFFFF",    # Λευκό για βασικό κείμενο
    "text_secondary": "#AAAAAA",  # Ανοιχτό γκρι για δευτερεύον κείμενο
    "green": "#00E676",           # Έντονο πράσινο για θετικές τιμές
    "red": "#F44336",             # Κόκκινο για αρνητικές τιμές
    "grid": "#333333",            # Σκούρο γκρι για το πλέγμα
    "accent": "#2979FF",          # Φωτεινό μπλε για έμφαση
    "header": "#1A237E",          # Βαθύ indigo για την επικεφαλίδα
}

CARD_STYLE = {
    "padding": "1.2rem",
    "borderRadius": "12px",
    "boxShadow": "0 4px 12px rgba(0,0,0,0.3)",
    "backgroundColor": COLORS["card_bg"],
    "margin": "0.7rem",
    "transition": "all 0.3s ease",
    "border": f"1px solid #333333",
}

HEADER_STYLE = {
    "backgroundColor": COLORS["header"],
    "color": COLORS["text_primary"],
    "padding": "1.5rem",
    "boxShadow": "0 4px 12px rgba(0,0,0,0.3)",
    "marginBottom": "30px",
    "borderRadius": "0 0 20px 20px",
    "borderBottom": f"1px solid {COLORS['accent']}",
}

# ---------------------------------------------------------------------------
# LAYOUT --------------------------------------------------------------------
# ---------------------------------------------------------------------------

app.layout = html.Div(
    [
        # Header ----------------------------------------------------------------
        html.Div(
            [
                html.H1("Andreas's Portfolio Tracker",
                        style={"fontWeight": "600", "margin": "0"}),
                html.P(
                    "Track your investments, analyze returns, and make informed decisions",
                    style={
                        "fontSize": "1.1rem",
                        "marginTop": "8px",
                        "opacity": "0.9",
                    },
                ),
            ],
            style=HEADER_STYLE,
        ),
        # Content Container ------------------------------------------------------
        html.Div(
            [
                # View Selector
                html.Div(
                    [
                        dcc.Dropdown(
                            id="view-dd",
                            options=[
                                {
                                    "label": "📉 Tickers (VUAA, EQAC, USD)",
                                    "value": "TICKERS",
                                },
                                {
                                    "label": "📊 Portfolio Overview",
                                    "value": "PORT",
                                },
                                {"label": "📜 Trades History",             
                                 "value": "TRADES"
                                
                                }
                            ],
                            value="TICKERS",
                            clearable=False,
                            className="dropdown-dark",
                            style={
                                "color": "#FFFFFF",
                                "backgroundColor": "#000000",
                                "fontWeight": "bold",
                            },
                        )
                    ],
                    style={"width": "300px", "margin": "20px auto"},
                ),
                # Summary Cards ---------------------------------------------------
                html.Div(
                    [
                        html.H2(
                            "Dashboard Summary",
                            style={
                                "textAlign": "center",
                                "color": COLORS["accent"],
                                "marginTop": "10px",
                            },
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H5(
                                                    "Last Updated",
                                                    style={
                                                        "color": COLORS[
                                                            "text_secondary"
                                                        ],
                                                        "margin": "0",
                                                    },
                                                ),
                                                html.H3(
                                                    datetime.now().strftime(
                                                        "%d %b %Y, %H:%M"
                                                    ),
                                                    style={
                                                        "margin": "5px 0",
                                                        "color": COLORS[
                                                            "text_primary"
                                                        ],
                                                    },
                                                ),
                                            ],
                                            style=CARD_STYLE,
                                        ),
                                        html.Div(
                                            [
                                                html.H5(
                                                    "Portfolio Value",
                                                    style={
                                                        "color": COLORS[
                                                            "text_secondary"
                                                        ],
                                                        "margin": "0",
                                                    },
                                                ),
                                                html.H3(
                                                    f"${port_current:.2f}",
                                                    style={
                                                        "margin": "5px 0",
                                                        "color": COLORS[
                                                            "accent"
                                                        ],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                            ],
                                            style=CARD_STYLE,
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "justifyContent": "center",
                                        "flexWrap": "wrap",
                                    },
                                )
                            ]
                        ),
                    ]
                ),
                # Main Content Area ----------------------------------------------
                html.Div(id="content", style={"marginTop": "20px"}),
                # Footer ----------------------------------------------------------
                html.Footer(
                    [
                        html.P(
                            "Data sourced from Yahoo Finance • Updated automatically",
                            style={
                                "textAlign": "center",
                                "color": COLORS["text_secondary"],
                                "padding": "20px",
                            },
                        )
                    ]
                ),
            ],
            style={
                "padding": "0 2rem",
                "maxWidth": "1400px",
                "margin": "0 auto",
            },
        ),
    ],
    style={
        "fontFamily": "'Roboto', 'Segoe UI', 'Helvetica Neue', sans-serif",
        "backgroundColor": COLORS["background"],
        "minHeight": "100vh",
        "padding": "0 0 20px 0",
        "color": COLORS["text_primary"],
    },
)

# ---------------------------------------------------------------------------
# CUSTOM HTML (index_string) -------------------------------------------------
# ---------------------------------------------------------------------------

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
                background-color: #0a1929;
                color: white;
                font-family: Arial, sans-serif;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            h1, h2, h3 {
                color: white;
            }
            .card {
                background-color: #132f4c;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            /* Dropdown styling */
            .dropdown-dark .Select-control {
                background-color: #000000;
                color: #FFFFFF;
                border-color: #FFFFFF;
            }
            .dropdown-dark .Select-value-label {
                color: #FFFFFF !important;
            }
            .dropdown-dark .Select-menu-outer {
                background-color: #000000;
                color: #FFFFFF;
                border: 1px solid #FFFFFF;
            }
            .dropdown-dark .Select-option {
                background-color: #000000;
                color: #FFFFFF;
            }
            .dropdown-dark .Select-option:hover {
                background-color: #222222;
                color: #FFFFFF;
            }
            .dropdown-dark .Select-option.is-selected {
                background-color: #333333;
                color: #FFFFFF;
            }
            .dropdown-dark .Select-arrow {
                border-color: #FFFFFF transparent transparent;
            }
            .dropdown-dark .Select-placeholder {
                color: #AAAAAA;
            }
            .dropdown-dark .Select--single > .Select-control .Select-value {
                color: #FFFFFF;
            }
            .dropdown-dark .Select-input > input {
                color: #FFFFFF;
            }
            .dropdown-dark .has-value.Select--single > .Select-control .Select-value .Select-value-label,
            .dropdown-dark .has-value.is-pseudo-focused.Select--single > .Select-control .Select-value .Select-value-label {
                color: #FFFFFF;
            }
            /* Button styling */
            .btn-primary {
                background-color: #1976d2;
                border-color: #1976d2;
            }
            .btn-primary:hover {
                background-color: #1565c0;
                border-color: #1565c0;
            }
            /* Upload styling */
            .upload-area {
                border: 2px dashed #1976d2;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                cursor: pointer;
            }
            .upload-area:hover {
                border-color: #1565c0;
                background-color: rgba(25, 118, 210, 0.1);
            }
        </style>
        {%scripts%}
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

# ---------------------------------------------------------------------------
# SECTION BUILDERS ----------------------------------------------------------
# ---------------------------------------------------------------------------

def format_value(value, is_percentage=False):
    """Return formatted string and color depending on sign."""
    formatted = f"{value:.2f}%" if is_percentage else f"${value:.2f}"
    color = COLORS["green"] if value >= 0 else COLORS["red"]
    return formatted, color


def build_cards(info: dict) -> html.Div:
    profit_formatted, profit_color = format_value(info["profit_abs"])
    return_formatted, return_color = format_value(info["return_pct"], True)

    return html.Div(
        [
            html.Div(
                [
                    html.H6(
                        "Entry Price",
                        style={
                            "color": COLORS["text_secondary"],
                            "marginBottom": "10px",
                        },
                    ),
                    html.H4(f"${info['dca'][-1]:.2f}", style={"margin": "0"}),
                ],
                style=CARD_STYLE,
            ),
            html.Div(
                [
                    html.H6(
                        "Invested",
                        style={
                            "color": COLORS["text_secondary"],
                            "marginBottom": "10px",
                        },
                    ),
                    html.H4(f"${info['invested']:.2f}", style={"margin": "0"}),
                ],
                style=CARD_STYLE,
            ),
            html.Div(
                [
                    html.H6(
                        "Current",
                        style={
                            "color": COLORS["text_secondary"],
                            "marginBottom": "10px",
                        },
                    ),
                    html.H4(
                        f"${info['current']:.2f}",
                        style={"margin": "0", "color": COLORS["accent"]},
                    ),
                ],
                style=CARD_STYLE,
            ),
            html.Div(
                [
                    html.H6(
                        "Profit",
                        style={
                            "color": COLORS["text_secondary"],
                            "marginBottom": "10px",
                        },
                    ),
                    html.H4(
                        profit_formatted,
                        style={"margin": "0", "color": profit_color},
                    ),
                ],
                style=CARD_STYLE,
            ),
            html.Div(
                [
                    html.H6(
                        "Return",
                        style={
                            "color": COLORS["text_secondary"],
                            "marginBottom": "10px",
                        },
                    ),
                    html.H4(
                        return_formatted,
                        style={"margin": "0", "color": return_color},
                    ),
                ],
                style=CARD_STYLE,
            ),
        ],
        style={"display": "flex", "justifyContent": "center", "flexWrap": "wrap"},
    )
    
def build_trades_section() -> html.Div:
    # Φορτώνουμε το αρχείο trades, το ταξινομούμε κατά Date
    df = pd.read_excel(TRADES_XLSX)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date" , ascending=False)
    
    # 2) Διώξε τις στήλες Number & Date
    df = df.drop(columns=["Number", "Date"])
    df.rename(columns={df.columns[0]: "Date"}, inplace=True)
    df['Date'] = df['Date'].dt.date


    

    # Χτίζουμε το DataTable
    table = dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in df.columns],
        data=df.to_dict("records"),
        sort_action="native",
        page_size=20,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": COLORS["card_bg"],
            "color": COLORS["text_primary"],
            "fontWeight": "bold"
        },
        style_cell={
            "backgroundColor": COLORS["background"],
            "color": COLORS["text_primary"],
            "textAlign": "left",
            "padding": "5px"
        },
    )

    return html.Div([
        html.H2("Trades History", 
                style={"textAlign": "center", "color": COLORS["accent"], "marginBottom": "20px"}),
        table
    ], style={"padding": "0 2rem", "maxWidth": "1400px", "margin": "0 auto"})



def build_ticker_section(ticker: str) -> html.Div:
    d = ALL[ticker]
    dtick = Y_DTICKS.get(ticker)

    fig = go.Figure(
        [
            go.Scatter(
                x=d["price"].index,
                y=d["price"]["Close"],
                name="Close",
                line=dict(width=3, color=COLORS["accent"]),
                hovertemplate='%{y:.2f}<extra></extra>',
            ),
            go.Scatter(
                x=d["price"].index,
                y=d["dca"],
                name="DCA",
                line=dict(width=2, dash="dash", color=COLORS["green"]),
                hovertemplate='%{y:.2f}<extra></extra>',
            ),
            go.Scatter(
                x=d["buy_dates"],
                y=d["buy_prices"],
                mode="markers",
                name="Buys",
                marker=dict(size=14, color=COLORS["red"]),
                hovertemplate='%{y:.2f}<extra></extra>',
            ),
        ]
    )

    fig.update_layout(
        height=450,
        template="plotly_dark",
        title={
            "text": f"{ticker} Performance",
            "font": {"size": 22, "color": COLORS["text_primary"]},
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        yaxis_title="Price",
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
            gridcolor=COLORS["grid"],
            zeroline=True,
            zerolinecolor=COLORS["text_secondary"],
            zerolinewidth=1,
        ),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        margin=dict(l=40, r=40, t=80, b=40),
        plot_bgcolor=COLORS["card_bg"],
        paper_bgcolor=COLORS["card_bg"],
        font=dict(color=COLORS["text_primary"]),
        hovermode="x unified",
    )

    return html.Div(
        [
            build_cards(d),
            html.Div(
                [dcc.Graph(figure=fig)],
                style={
                    "backgroundColor": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "boxShadow": "0 4px 12px rgba(0,0,0,0.3)",
                    "border": "1px solid #333333",
                },
            ),
        ],
        style={"marginBottom": "40px"},
    )


def build_portfolio_section() -> html.Div:
    profit_formatted, profit_color = format_value(port_profit_abs)
    return_formatted, return_color = format_value(port_return_pct, True)

    cards = html.Div(
        [
            html.Div(
                [
                    html.H6(
                        "Invested",
                        style={
                            "color": COLORS["text_secondary"],
                            "marginBottom": "10px",
                        },
                    ),
                    html.H4(f"${port_invested:.2f}", style={"margin": "0"}),
                ],
                style=CARD_STYLE,
            ),
            html.Div(
                [
                    html.H6(
                        "Current",
                        style={
                            "color": COLORS["text_secondary"],
                            "marginBottom": "10px",
                        },
                    ),
                    html.H4(
                        f"${port_current:.2f}",
                        style={"margin": "0", "color": COLORS["accent"]},
                    ),
                ],
                style=CARD_STYLE,
            ),
            html.Div(
                [
                    html.H6(
                        "Profit",
                        style={
                            "color": COLORS["text_secondary"],
                            "marginBottom": "10px",
                        },
                    ),
                    html.H4(
                        profit_formatted,
                        style={"margin": "0", "color": profit_color},
                    ),
                ],
                style=CARD_STYLE,
            ),
        ],
        style={"display": "flex", "justifyContent": "center", "flexWrap": "wrap"},
    )

    # Apply dark template & grid to portfolio figs
    fig_port_profit.update_layout(
        template="plotly_dark",
        title={
            "text": "Portfolio Profit History",
            "font": {"size": 22, "color": COLORS["text_primary"]},
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
        },
        yaxis=dict(
            dtick=PORT_PROFIT_DTICK,
            showgrid=True,
            gridcolor=COLORS["grid"],
            zeroline=True,
            zerolinecolor=COLORS["text_secondary"],
            zerolinewidth=1,
        ),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        margin=dict(l=40, r=40, t=80, b=40),
        plot_bgcolor=COLORS["card_bg"],
        paper_bgcolor=COLORS["card_bg"],
        font=dict(color=COLORS["text_primary"]),
        hovermode="x unified",
    )

    fig_port_yield.update_layout(
        template="plotly_dark",
        title={
            "text": "Portfolio Yield Percentage",
            "font": {"size": 22, "color": COLORS["text_primary"]},
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
        },
        yaxis=dict(
            dtick=PORT_YIELD_DTICK,
            showgrid=True,
            gridcolor=COLORS["grid"],
            zeroline=True,
            zerolinecolor=COLORS["text_secondary"],
            zerolinewidth=1,
        ),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        margin=dict(l=40, r=40, t=80, b=40),
        plot_bgcolor=COLORS["card_bg"],
        paper_bgcolor=COLORS["card_bg"],
        font=dict(color=COLORS["text_primary"]),
        hovermode="x unified",
    )
    
    # Ετικέτες απόδοσης
    yield_metrics = html.Div(
        [
            html.Div(
                [
                    html.H6(
                        "Μέγιστη Απόδοση",
                        style={
                            "color": COLORS["text_secondary"],
                            "marginBottom": "10px",
                        },
                    ),
                    html.H4(
                        f"{y_max * 100:.2f}%",
                        style={"margin": "0", "color": COLORS["green"]},
                    ),
                ],
                style=CARD_STYLE,
            ),
            html.Div(
                [
                    html.H6(
                        "Ελάχιστη Απόδοση",
                        style={
                            "color": COLORS["text_secondary"],
                            "marginBottom": "10px",
                        },
                    ),
                    html.H4(
                        f"{y_min * 100:.2f}%",
                        style={"margin": "0", "color": "red"},
                    ),
                ],
                style=CARD_STYLE,
            ),
            html.Div(
                [
                    html.H6(
                        "Τρέχουσα Απόδοση",
                        style={
                            "color": COLORS["text_secondary"],
                            "marginBottom": "10px",
                        },
                    ),
                    html.H4(
                        return_formatted,
                        style={"margin": "0", "color": return_color},
                    ),
                ],
                style=CARD_STYLE,
            ),
        ],
        style={"display": "flex", "justifyContent": "center", "flexWrap": "wrap", "marginBottom": "20px"},
    )

    return html.Div(
        [
            html.H2(
                "Portfolio Overview",
                style={
                    "textAlign": "center",
                    "color": COLORS["accent"],
                    "marginBottom": "20px",
                },
            ),
            cards,
            html.Div(
                [dcc.Graph(figure=fig_port_profit)],
                style={
                    "backgroundColor": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "boxShadow": "0 4px 12px rgba(0,0,0,0.3)",
                    "marginBottom": "30px",
                    "border": "1px solid #333333",
                },
            ),
            yield_metrics,
            html.Div(
                [dcc.Graph(figure=fig_port_yield)],
                style={
                    "backgroundColor": COLORS["card_bg"],
                    "borderRadius": "12px",
                    "boxShadow": "0 4px 12px rgba(0,0,0,0.3)",
                    "border": "1px solid #333333",
                },
            ),
        ]
    )

# ---------------------------------------------------------------------------
# CALLBACK ------------------------------------------------------------------
# ---------------------------------------------------------------------------

@app.callback(Output("content", "children"), Input("view-dd", "value"))
def render_content(view):
    if view == "PORT":
        return build_portfolio_section()
    elif view == "TRADES":
        return build_trades_section()
    # Default: TICKERS
    return html.Div(
        [
            build_ticker_section("VUAA.EU"),
            build_ticker_section("EQAC.EU"),
            build_ticker_section("USD/EUR"),
        ]
    )

# ---------------------------------------------------------------------------
# MAIN ----------------------------------------------------------------------
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
