from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

@dataclass
class Trade:
    """Represents a single trade transaction."""
    date: datetime
    ticker: str
    price: float
    quantity: float
    direction: str
    #αυτος ο decorator μετατρεπει την μεθοδο σε attribute
    @property
    def is_buy(self) -> bool:
        """Check if this is a buy trade."""
        return self.direction.strip().lower() == 'buy'
    
    @property
    def total_value(self) -> float:
        """Calculate total value of the trade."""
        return self.price * self.quantity

@dataclass
class PerformanceMetrics:
    """Performance metrics for investments."""
    invested: float
    current_value: float
    profit_absolute: float
    return_percentage: float
    average_buy_price: float
    
    @property
    def is_profitable(self) -> bool:
        """Check if investment is profitable."""
        return self.profit_absolute > 0
    
    @property
    def roi_ratio(self) -> float:
        """Return on investment as ratio."""
        return self.profit_absolute / self.invested if self.invested > 0 else 0.0

@dataclass
class TickerData:
    """Complete data for a single ticker."""
    symbol: str
    price_history: pd.DataFrame
    dca_history: List[float]
    shares_per_day: List[float]
    profit_series: np.ndarray
    
    # Trade data 
    buy_dates: List[datetime]
    buy_prices: List[float]
    buy_quantities: List[float]
    
    # Performance metrics
    metrics: PerformanceMetrics
    
    @property
    def has_trades(self) -> bool:
        """Check if ticker has any trades."""
        return len(self.buy_dates) > 0
    
    @property
    def latest_price(self) -> float:
        """Get latest closing price."""
        return self.price_history["Close"].iloc[-1] if not self.price_history.empty else 0.0
    
    @property
    def total_shares(self) -> float:
        """Get total shares owned."""
        return self.shares_per_day[-1] if self.shares_per_day else 0.0
    
    @property
    def current_dca(self) -> float:
        """Get current Dollar Cost Average."""
        return self.dca_history[-1] if self.dca_history else 0.0

@dataclass
class PortfolioSnapshot:
    """Complete portfolio state at a point in time."""
    timestamp: datetime
    tickers: List[TickerData]
    total_metrics: PerformanceMetrics

    # Προσθήκη: Cached series για απόδοση
    series: Dict[str, np.ndarray] = field(default_factory=dict)
    # χρησιμοποιουμε το field ωστε καθε αντικειμενο PortfolioSnapshot να έχει τα series του
    #και να μην μοιραζεται κοινα series μεταξυ των αντικειμενων
    #διαφορετικα η series θα ηταν static attribute
    
    @property
    def equity_tickers(self) -> List[TickerData]:
        """Get only equity tickers (excluding forex)."""
        return [ticker for ticker in self.tickers if ticker.symbol != "USD/EUR"]
    
    @property
    def forex_tickers(self) -> List[TickerData]:
        """Get only forex tickers."""
        return [ticker for ticker in self.tickers if ticker.symbol == "USD/EUR"]
    
    def get_series(self, series_name: str) -> Optional[np.ndarray]:
        """Get cached series by name."""
        return self.series.get(series_name)
    
    def set_series(self, series_name: str, data: np.ndarray):
        """Set cached series."""
        self.series[series_name] = data
    
    def get_ticker_by_symbol(self, symbol: str) -> Optional[TickerData]:
        """Get ticker data by symbol."""
        for ticker in self.tickers:
            if ticker.symbol == symbol:
                return ticker
        return None
    
    def clear_series_cache(self):
        """Clear all cached series."""
        self.series.clear()


class PortfolioCalculator(ABC):
    """Abstract base for portfolio calculations."""
    
    @abstractmethod
    def calculate_dca(self, price_data: pd.DataFrame, trades: List[Trade]) -> tuple[List[float], List[float]]:
        """Calculate Dollar Cost Average progression."""
        pass
    
    @abstractmethod
    def calculate_performance_metrics(self, trades: List[Trade], current_price: float) -> PerformanceMetrics:
        """Calculate performance metrics for trades."""
        pass

    @abstractmethod
    def calculate_yield_series(self, porfolio : PortfolioSnapshot, inculde_usd : bool) -> np.ndarray:
        """Calculate yield series with optional USD/EUR profit inclusion."""
        pass

    @abstractmethod
    def calculate_invested_series(self, portfolio: PortfolioSnapshot) -> np.ndarray:
        """Calculate invested capital series for equity tickers."""
        pass
    
    @abstractmethod
    def calculate_profit_series(self, price_data: pd.DataFrame, dca: List[float], shares: List[float]) -> np.ndarray:
        """Calculate daily profit progression using the same logic as current P&L.
        For an individual ticker"""
        pass
    
    @abstractmethod
    def calculate_portfolio_profit_series(self, portfolio: PortfolioSnapshot, include_usd: bool = False) -> np.ndarray:
        """Calculate total portfolio profit series using unified logic."""
        pass

    @abstractmethod
    def extract_trade_data(self, buy_trades: List[Trade]) -> tuple[List, List, List]:
        """Extract buy trade data for plotting."""
        pass

    @abstractmethod
    def process_ticker_data(self, ticker: str, trades: List[Trade], price_df) -> dict:
        """Process all ticker calculations in one place."""
        pass

    @abstractmethod
    def calculate_side_metrics(self, data: np.ndarray, dates: pd.DatetimeIndex, 
                                        timeframe: str = "All") -> dict:
        """Calculate side metrics with timeframe filtering."""
        pass

    @abstractmethod
    def calculate_portfolio_metrics(self, ticker_data_list: List) -> PerformanceMetrics:
        """Calculate overall portfolio performance metrics."""
        pass

    @abstractmethod
    def calculate_trade_pnl(self, trades_df: pd.DataFrame, portfolio_service) -> pd.DataFrame:
        """Calculate P&L for individual trades based on current market prices."""
        pass

    @abstractmethod
    def find_extrema(self, data: np.ndarray, dates: pd.DatetimeIndex) -> tuple[tuple[float, pd.Timestamp], tuple[float, pd.Timestamp]]:
        """Find maximum and minimum values with their dates."""
        pass
