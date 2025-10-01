import numpy as np
import pandas as pd
from typing import List, Tuple
import logging

from models.portfolio import Trade, PerformanceMetrics, PortfolioCalculator

logger = logging.getLogger(__name__)

class StandardCalculationService(PortfolioCalculator):
    """Standard implementation of portfolio calculations."""
    
    def calculate_dca(self, price_data: pd.DataFrame, buy_trades: List[Trade]) -> tuple[List[float], List[float]]:
        """Calculate Dollar Cost Average and shares per day."""
        try:
            # Handle empty trades case
            if not buy_trades:
                return [0.0] * len(price_data), [0.0] * len(price_data)
            
            dca_history = []
            shares_history = []
            cumulative_cost = 0.0
            cumulative_shares = 0.0
            trade_idx = 0
            
            # Sort buy trades by date
            sorted_buy_trades = sorted(buy_trades, key=lambda x: x.date)
            
            for current_date in price_data.index:
                # Process trades for current date
                while (trade_idx < len(sorted_buy_trades) and 
                       current_date.date() == sorted_buy_trades[trade_idx].date.date()):
                    trade = sorted_buy_trades[trade_idx]
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
    
    def calculate_performance_metrics(self, buy_trades: List[Trade], current_price: float) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        try:
            if not buy_trades:
                return PerformanceMetrics(0, 0, 0, 0, 0)
            
            # Calculate base metrics using pre-filtered buy trades
            total_invested = sum(trade.total_value for trade in buy_trades)
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
    
    def calculate_profit_series(self, price_data: pd.DataFrame, dca: List[float], shares: List[float], buy_trades: List[Trade] = None) -> np.ndarray:
        """Calculate daily profit progression using the same logic as current P&L."""
        try:
            # Handle empty data case
            if not dca or not shares:
                return np.array([0.0] * len(price_data))
            
            # Find the first trade date to avoid calculating profit before any trades
            first_trade_date = None
            if buy_trades:
                first_trade_date = min(trade.date for trade in buy_trades)
            
            profit_series = []
            
            for i, (date, row) in enumerate(price_data.iterrows()):
                close_price = row['Close']
                
                # If we have a first trade date and current date is before it, profit should be 0
                if first_trade_date and date < first_trade_date:
                    profit_series.append(0.0)
                    continue
                
                if (i < len(dca) and i < len(shares) and 
                    not np.isnan(dca[i]) and shares[i] > 0):
                    # Use the same logic as current P&L: total_shares * current_price - total_invested
                    # where total_invested = dca[i] * shares[i] (cumulative cost up to this day)
                    total_invested = dca[i] * shares[i]  # This is the cumulative cost
                    total_shares = shares[i]  # This is the cumulative shares
                    current_value = total_shares * close_price
                    daily_profit = current_value - total_invested
                    profit_series.append(daily_profit)
                else:
                    profit_series.append(0.0)
            
            return np.array(profit_series)
            
        except Exception as e:
            logger.error(f"Error calculating profit series: {e}")
            raise
    
    def extract_trade_data(self, buy_trades: List[Trade]) -> tuple[List, List, List]:
        """Extract buy trade data for plotting."""
        try:
            if not buy_trades:
                return [], [], []
            
            buy_dates = [t.date for t in buy_trades]
            buy_prices = [t.price for t in buy_trades]
            buy_quantities = [t.quantity for t in buy_trades]
            
            return buy_dates, buy_prices, buy_quantities
            
        except Exception as e:
            logger.error(f"Error extracting trade data: {e}")
            raise
    
    def process_ticker_data(self, ticker: str, trades: List[Trade], price_df) -> dict:
        """Process all ticker calculations in one place."""
        try:
            # Filter buy trades once at the beginning
            buy_trades = [t for t in trades if t.is_buy]
            
            # Calculate DCA and shares progression
            dca, shares_per_day = self.calculate_dca(price_df, buy_trades)
            
            # Calculate profit series
            profit_series = self.calculate_profit_series(price_df, dca, shares_per_day, buy_trades)
            
            # Calculate performance metrics
            current_price = price_df['Close'].iloc[-1] if len(price_df) > 0 else 0
            metrics = self.calculate_performance_metrics(buy_trades, current_price)
            
            # Extract trade data
            buy_dates, buy_prices, buy_quantities = self.extract_trade_data(buy_trades)
            
            return {
                'dca_history': dca,
                'shares_per_day': shares_per_day,
                'profit_series': profit_series,
                'metrics': metrics,
                'buy_dates': buy_dates,
                'buy_prices': buy_prices,
                'buy_quantities': buy_quantities
            }
            
        except Exception as e:
            logger.error(f"Error processing ticker {ticker}: {e}")
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
    
    def calculate_profit_analysis_metrics(self, profit_series: np.ndarray, dates: pd.DatetimeIndex, 
                                        timeframe: str = "All") -> dict:
        """Calculate profit analysis metrics including max/min profit with timeframe filtering."""
        try:
            from datetime import timedelta
            
            # Apply timeframe filter if needed
            if timeframe != "All" and len(dates) > 0:
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
                    start_date = dates[0]
                
                # Filter data
                mask = dates >= start_date
                filtered_dates = dates[mask]
                filtered_profit = profit_series[mask]
            else:
                filtered_dates = dates
                filtered_profit = profit_series
            
            if len(filtered_profit) > 0:
                # Find extrema for the filtered data
                (max_profit, max_date), (min_profit, min_date) = self.find_extrema(
                    filtered_profit, filtered_dates
                )
            else:
                max_profit = min_profit = 0
                max_date = min_date = None
            
            return {
                'max_profit': max_profit,
                'min_profit': min_profit,
                'max_date': max_date,
                'min_date': min_date,
                'current_profit': profit_series[-1] if len(profit_series) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating profit analysis metrics: {e}")
            raise
    
    def calculate_portfolio_metrics(self, ticker_data_list: List) -> PerformanceMetrics:
        """Calculate overall portfolio performance metrics."""
        try:
            # Filter equity tickers (exclude USD/EUR for invested/current calculations)
            equity_tickers = [t for t in ticker_data_list if t.symbol != "USD/EUR"]
            
            # Calculate totals
            total_invested = sum(t.metrics.invested for t in equity_tickers)
            total_current = sum(t.metrics.current_value for t in equity_tickers)
            total_profit = sum(t.metrics.profit_absolute for t in equity_tickers)  # Include USD
            
            # Calculate return percentage
            return_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0
            avg_price = 0  # Not applicable for portfolio level
            
            return PerformanceMetrics(
                invested=total_invested,
                current_value=total_current,
                profit_absolute=total_profit,
                return_percentage=return_pct,
                average_buy_price=avg_price
            )
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            raise

    def calculate_trade_pnl(self, trades_df: pd.DataFrame, portfolio_service) -> pd.DataFrame:
        """Calculate P&L for individual trades based on current market prices."""
        try:
            trades_with_pnl = trades_df.copy()
            trades_with_pnl['P&L'] = 0.0
            
            # Get unique tickers from trades
            unique_tickers = trades_df['Ticker'].unique()
            
            # Get current prices for all tickers
            current_prices = {}
            for ticker in unique_tickers:
                try:
                    # Get current price from portfolio service
                    portfolio = portfolio_service.get_portfolio_snapshot()
                    ticker_data = portfolio.get_ticker_by_symbol(ticker)
                    if ticker_data:
                        current_prices[ticker] = ticker_data.latest_price
                    else:
                        logger.warning(f"No price data found for ticker {ticker}")
                        current_prices[ticker] = 0.0
                except Exception as e:
                    logger.error(f"Error getting current price for {ticker}: {e}")
                    current_prices[ticker] = 0.0
            
            # Calculate P&L for each trade
            for idx, row in trades_with_pnl.iterrows():
                ticker = row['Ticker']
                direction = row['Direction'].strip().lower()
                quantity = row.get('Quantity', 0)
                trade_price = row.get('Price', 0)
                current_price = current_prices.get(ticker, 0)
                
                if direction == 'buy' and current_price > 0 and quantity > 0:
                    # For buy trades: P&L = (current_price - trade_price) * quantity
                    pnl = (current_price - trade_price) * quantity
                    trades_with_pnl.at[idx, 'P&L'] = pnl
                elif direction == 'sell' and current_price > 0 and quantity > 0:
                    # For sell trades: P&L = (trade_price - current_price) * quantity
                    # Note: This represents the profit made from selling at trade_price vs current market
                    pnl = (trade_price - current_price) * quantity
                    trades_with_pnl.at[idx, 'P&L'] = pnl
                else:
                    trades_with_pnl.at[idx, 'P&L'] = 0.0
            
            logger.debug(f"Calculated P&L for {len(trades_with_pnl)} trades")
            return trades_with_pnl
            
        except Exception as e:
            logger.error(f"Error calculating trade P&L: {e}")
            # Return original dataframe with zero P&L on error
            trades_df_copy = trades_df.copy()
            trades_df_copy['P&L'] = 0.0
            return trades_df_copy
