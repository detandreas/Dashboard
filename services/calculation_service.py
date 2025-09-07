import numpy as np
import pandas as pd
from typing import List, Tuple
import logging

from models.portfolio import Trade, PerformanceMetrics, PortfolioCalculator

logger = logging.getLogger(__name__)

class StandardCalculationService(PortfolioCalculator):
    """Standard implementation of portfolio calculations."""
    
    def calculate_dca(self, price_data: pd.DataFrame, trades: List[Trade]) -> tuple[List[float], List[float]]:
        """Calculate Dollar Cost Average and shares per day."""
        try:
            dca_history = []
            shares_history = []
            cumulative_cost = 0.0
            cumulative_shares = 0.0
            trade_idx = 0
            
            # Filter and sort buy trades
            buy_trades = [t for t in trades if t.is_buy]
            buy_trades.sort(key=lambda x: x.date)
            
            for current_date in price_data.index:
                # Process trades for current date
                while (trade_idx < len(buy_trades) and 
                       current_date.date() == buy_trades[trade_idx].date.date()):
                    trade = buy_trades[trade_idx]
                    cumulative_cost += trade.total_value
                    cumulative_shares += trade.quantity
                    trade_idx += 1
                
                # Calculate DCA
                if cumulative_shares > 0:
                    dca_history.append(cumulative_cost / cumulative_shares)
                else:
                    dca_history.append(np.nan)
                
                shares_history.append(cumulative_shares)
            
            logger.debug(f"Calculated DCA for {len(price_data)} data points")
            return dca_history, shares_history
            
        except Exception as e:
            logger.error(f"Error calculating DCA: {e}")
            raise
    
    def calculate_performance_metrics(self, trades: List[Trade], current_price: float) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        try:
            buy_trades = [t for t in trades if t.is_buy]
            
            if not buy_trades:
                return PerformanceMetrics(0, 0, 0, 0, 0)
            
            # Calculate base metrics - exclude EUR/USD from total invested
            buy_trades_excluding_eur_usd = [t for t in buy_trades ]
            total_invested = sum(trade.total_value for trade in buy_trades_excluding_eur_usd)
            total_shares = sum(trade.quantity for trade in buy_trades)
            avg_buy_price = total_invested / total_shares if total_shares > 0 else 0
            
            # Calculate current metrics
            current_value = total_shares * current_price
            profit_absolute = current_value - total_invested
            return_percentage = (profit_absolute / total_invested * 100) if total_invested > 0 else 0
            
            return PerformanceMetrics(
                invested=total_invested,
                current_value=current_value,
                profit_absolute=profit_absolute,
                return_percentage=return_percentage,
                average_buy_price=avg_buy_price
            )
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            raise
    
    def calculate_profit_series(self, price_data: pd.DataFrame, dca: List[float], shares: List[float]) -> np.ndarray:
        """Calculate daily profit progression."""
        try:
            profit_series = []
            
            for i, (_, row) in enumerate(price_data.iterrows()):
                close_price = row['Close']
                
                if (i < len(dca) and i < len(shares) and 
                    not np.isnan(dca[i]) and shares[i] > 0):
                    daily_profit = (close_price - dca[i]) * shares[i]
                    profit_series.append(daily_profit)
                else:
                    profit_series.append(0.0)
            
            return np.array(profit_series)
            
        except Exception as e:
            logger.error(f"Error calculating profit series: {e}")
            raise
    
    def find_extrema(self, data: np.ndarray, dates: pd.DatetimeIndex) -> tuple[tuple[float, pd.Timestamp], tuple[float, pd.Timestamp]]:
        """Find maximum and minimum values with their dates."""
        try:
            if len(data) == 0:
                return (0, dates[0]), (0, dates[0])
            
            max_val = np.nanmax(data)
            min_val = np.nanmin(data)
            max_idx = np.nanargmax(data)
            min_idx = np.nanargmin(data)
            
            return (max_val, dates[max_idx]), (min_val, dates[min_idx])
            
        except Exception as e:
            logger.error(f"Error finding extrema: {e}")
            raise
