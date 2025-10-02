from dataclasses import dataclass
from typing import List, Optional
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
    
    @property
    def equity_tickers(self) -> List[TickerData]:
        """Get only equity tickers (excluding forex)."""
        return [ticker for ticker in self.tickers if ticker.symbol != "USD/EUR"]
    
    @property
    def forex_tickers(self) -> List[TickerData]:
        """Get only forex tickers."""
        return [ticker for ticker in self.tickers if ticker.symbol == "USD/EUR"]
    
    
    def total_profit_series(self, include_usd: bool = False) -> np.ndarray:
        """Calculate total portfolio profit series, considering only tickers with trades on each day.
        Optionally include USD/EUR tickers."""
        if not self.tickers:
            return np.array([])
        
        # Get the date range from the first ticker that has price history
        dates = None
        for ticker in self.tickers:
            if ticker.has_trades and len(ticker.price_history) > 0:
                dates = ticker.price_history.index
                break
        
        if dates is None:
            return np.array([])
        
        total_series = np.zeros(len(dates))
        
        for ticker in self.tickers:
            if not ticker.has_trades or len(ticker.price_history) == 0:
                continue
                
            is_usd_ticker = ticker.symbol == "USD/EUR"
            if is_usd_ticker and not include_usd:
                continue

            if not is_usd_ticker and not ticker.has_trades:
                continue

            profit_series = ticker.profit_series
            if len(profit_series) == 0:
                continue

            if is_usd_ticker:
                for i in range(min(len(dates), len(profit_series))):
                    total_series[i] += profit_series[i]
                continue

            trade_dates = sorted(ticker.buy_dates)
            if not trade_dates:
                continue

            cumulative_trade_index = 0
            has_position = False

            for i, date in enumerate(dates):
                if i >= len(profit_series):
                    break

                while (cumulative_trade_index < len(trade_dates)
                       and trade_dates[cumulative_trade_index] <= date):
                    has_position = True
                    cumulative_trade_index += 1

                if has_position:
                    total_series[i] += profit_series[i]

        return total_series
    @property
    def portfolio_yield_series(self) -> np.ndarray:
        """Calculate portfolio yield percentage series."""
        if not self.equity_tickers:
            return np.array([])
        
        profit_series = self.total_profit_series
        invested_series = self._calculate_invested_series()
        
        yield_series = []
        for i, (profit, invested) in enumerate(zip(profit_series, invested_series)):
            if invested > 0:
                yield_series.append(profit / invested * 100)
            else:
                yield_series.append(0.0)
        
        return np.array(yield_series)
    
    def _calculate_invested_series(self) -> List[float]:
        """Calculate daily invested amount series for equity tickers."""
        if not self.equity_tickers:
            return []
        
        # Use the first ticker's date range
        dates = self.equity_tickers[0].price_history.index
        invested_series = []
        
        for i in range(len(dates)):
            daily_invested = sum(
                ticker.dca_history[i] * ticker.shares_per_day[i]
                for ticker in self.equity_tickers
                if i < len(ticker.dca_history) and i < len(ticker.shares_per_day)
                and not np.isnan(ticker.dca_history[i])
            )
            invested_series.append(daily_invested)
        
        return invested_series
    
    def get_ticker_by_symbol(self, symbol: str) -> Optional[TickerData]:
        """Get ticker data by symbol."""
        for ticker in self.tickers:
            if ticker.symbol == symbol:
                return ticker
        return None

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
    def calculate_profit_series(self, price_data: pd.DataFrame, dca: List[float], shares: List[float]) -> np.ndarray:
        """Calculate profit progression over time."""
        pass
    
    @abstractmethod
    def find_extrema(self, data: np.ndarray, dates: pd.DatetimeIndex) -> tuple[tuple[float, pd.Timestamp], tuple[float, pd.Timestamp]]:
        """Find maximum and minimum values with their dates."""
        pass
