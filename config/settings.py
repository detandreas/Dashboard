import os
from datetime import datetime, timedelta
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    trades_xlsx_path: str
    finance_xlsx_path: str

@dataclass
class MarketConfig:
    """Market data configuration."""
    tracked_symbols: Dict[str, str]
    start_date: str
    y_axis_ticks: Dict[str, float]
    portfolio_profit_tick: float
    portfolio_yield_tick: float

@dataclass
class UIConfig:
    """UI styling configuration."""
    colors: Dict[str, str]
    card_style: Dict[str, Any]

class GoalsConfig:
    """Goals and milestones configuration."""
    
    def __init__(self):
        # Available goal metrics
        self.available_metrics = {
            "portfolio_value": {
                "label": "Portfolio Value",
                "unit": "$",
                "description": "Total portfolio market value"
            }
        }
        
        # Default goal configuration
        self.default_goal = {
            "metric": "portfolio_value",
            "milestones": [
                {"amount": 10000, "label": "First Milestone", "status": "upcoming"},
                {"amount": 25000, "label": "Second Milestone", "status": "upcoming"},
                {"amount": 50000, "label": "Major Target", "status": "upcoming"}
            ],
            "active": True,
            "created_date": None
        }
        
        # Current active goal (loaded from persistence)
        self.current_goal = None

class Config:
    """Centralized configuration management."""
    
    def __init__(self):
        self.database = DatabaseConfig(
            trades_xlsx_path=os.getenv("DASH_FILE_PATH", "assets/Trades.xlsx"),
            finance_xlsx_path="assets/Book3.xlsx"
        )
        
        self.market = MarketConfig(
            tracked_symbols={
                "VUAA.L": "VUAA.EU",
                "EQAC.SW": "EQAC.EU",
                "EUR=X": "USD/EUR",
                "AETF.AT": "AETF.GR"
            },
            start_date="2024-06-01",
            y_axis_ticks={
                "VUAA.EU": 5,
                "EQAC.EU": 20,
                "USD/EUR": 0.02,
                "AETF.GR": 5
            },
            portfolio_profit_tick=200,
            portfolio_yield_tick=3
        )
        
        self.ui = UIConfig(
            colors={
                "primary": "#0D47A1",
                "secondary": "#00838F",
                "background": "#121212",
                "card_bg": "#1E1E1E",
                "text_primary": "#FFFFFF",
                "text_secondary": "#AAAAAA",
                "green": "#00E676",
                "red": "#F44336",
                "grid": "#333333",
                "accent": "#2979FF",
                "header": "#1A237E",
            },
            card_style={
                "padding": "1.2rem",
                "borderRadius": "12px",
                "boxShadow": "0 4px 12px rgba(0,0,0,0.3)",
                "backgroundColor": "#1E1E1E",
                "margin": "0.7rem",
                "transition": "all 0.3s ease",
                "border": "1px solid #333333",
            }
        )
        self.goals = GoalsConfig()
    
    @staticmethod
    def get_tomorrow_date() -> str:
        """Get tomorrow's date for yfinance queries."""
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    def get_equity_tickers(self) -> list[str]:
        """Get list of equity tickers (excluding forex)."""
        return [ticker for ticker in self.market.tracked_symbols.values() if ticker != "USD/EUR"]
