from typing import Dict, List
import logging
from datetime import datetime

from models.portfolio import Trade, TickerData, PortfolioSnapshot, PerformanceMetrics
from services.data_service import DataServiceInterface
from services.calculation_service import StandardCalculationService
from config.settings import Config

logger = logging.getLogger(__name__)

class PortfolioService:
    """Main service orchestrating portfolio operations."""
    
    def __init__(self, data_service: DataServiceInterface, config: Config):
        self.data_service = data_service
        self.config = config
        self.calculator = StandardCalculationService()
        self._portfolio_cache: PortfolioSnapshot = None
    
    def get_portfolio_snapshot(self, force_refresh: bool = False) -> PortfolioSnapshot:
        """Get current portfolio snapshot with caching."""
        if self._portfolio_cache is None or force_refresh:
            self._portfolio_cache = self._build_portfolio_snapshot()
        
        return self._portfolio_cache
    
    def _build_portfolio_snapshot(self) -> PortfolioSnapshot:
        """Build complete portfolio snapshot."""
        try:
            logger.info("Building portfolio snapshot")
            
            # Validate data integrity first
            if not self.data_service.validate_data_integrity():
                raise ValueError("Data integrity validation failed")
            
            # Load data
            trades = self.data_service.load_trades()
            symbols = list(self.config.market.tracked_symbols.keys())
            price_history = self.data_service.get_price_history(symbols)
            
            # Group trades by ticker
            trades_by_ticker = self._group_trades_by_ticker(trades)
            
            # Process each ticker
            ticker_data_list = []
            for yf_symbol, excel_ticker in self.config.market.tracked_symbols.items():
                ticker_trades = trades_by_ticker.get(excel_ticker, [])
                price_df = price_history[yf_symbol]
                
                ticker_data = self._process_ticker(
                    excel_ticker, ticker_trades, price_df
                )
                ticker_data_list.append(ticker_data)
            
            # Calculate portfolio totals
            total_metrics = self._calculate_portfolio_metrics(ticker_data_list)
            
            snapshot = PortfolioSnapshot(
                timestamp=datetime.now(),
                tickers=ticker_data_list,
                total_metrics=total_metrics
            )
            
            logger.info(f"Portfolio snapshot built with {len(ticker_data_list)} tickers")
            return snapshot
            
        except Exception as e:
            logger.error(f"Error building portfolio snapshot: {e}")
            raise
    
    def _group_trades_by_ticker(self, trades: List[Trade]) -> Dict[str, List[Trade]]:
        """Group trades by ticker symbol."""
        trades_by_ticker = {}
        for trade in trades:
            if trade.ticker not in trades_by_ticker:
                trades_by_ticker[trade.ticker] = []
            trades_by_ticker[trade.ticker].append(trade)
        
        return trades_by_ticker
    
    def _process_ticker(self, ticker: str, trades: List[Trade], price_df) -> TickerData:
        """Process individual ticker data."""
        try:
            if trades:
                # Calculate DCA and shares progression
                dca, shares_per_day = self.calculator.calculate_dca(price_df, trades)
                
                # Calculate profit series
                profit_series = self.calculator.calculate_profit_series(
                    price_df, dca, shares_per_day
                )
                
                # Calculate performance metrics
                current_price = price_df['Close'].iloc[-1]
                metrics = self.calculator.calculate_performance_metrics(trades, current_price)
                
                # Extract trade data
                buy_trades = [t for t in trades if t.is_buy]
                buy_dates = [t.date for t in buy_trades]
                buy_prices = [t.price for t in buy_trades]
                buy_quantities = [t.quantity for t in buy_trades]
            else:
                # No trades for this ticker
                dca = [0.0] * len(price_df)
                shares_per_day = [0.0] * len(price_df)
                profit_series = [0.0] * len(price_df)
                metrics = PerformanceMetrics(0, 0, 0, 0, 0)
                buy_dates = buy_prices = buy_quantities = []
            
            return TickerData(
                symbol=ticker,
                price_history=price_df,
                dca_history=dca,
                shares_per_day=shares_per_day,
                profit_series=profit_series,
                buy_dates=buy_dates,
                buy_prices=buy_prices,
                buy_quantities=buy_quantities,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Error processing ticker {ticker}: {e}")
            raise
    
    def _calculate_portfolio_metrics(self, ticker_data_list: List[TickerData]) -> PerformanceMetrics:
        """Calculate overall portfolio metrics."""
        equity_tickers = [t for t in ticker_data_list if t.symbol != "USD/EUR"]
        
        total_invested = sum(t.metrics.invested for t in equity_tickers)
        total_current = sum(t.metrics.current_value for t in equity_tickers)
        total_profit = sum(t.metrics.profit_absolute for t in ticker_data_list)  # Include USD
        
        return_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0
        avg_price = 0  # Not applicable for portfolio
        
        return PerformanceMetrics(
            invested=total_invested,
            current_value=total_current,
            profit_absolute=total_profit,
            return_percentage=return_pct,
            average_buy_price=avg_price
        )
    
    def refresh_data(self):
        """Force refresh of all data."""
        logger.info("Refreshing portfolio data")
        self.data_service.clear_cache()
        self._portfolio_cache = None
    
    def get_ticker_data(self, ticker_symbol: str) -> TickerData:
        """Get data for specific ticker."""
        snapshot = self.get_portfolio_snapshot()
        for ticker in snapshot.tickers:
            if ticker.symbol == ticker_symbol:
                return ticker
        
        raise ValueError(f"Ticker {ticker_symbol} not found in portfolio")
    
    def get_trades_summary(self) -> Dict:
        """Get summary statistics about trades."""
        try:
            trades = self.data_service.load_trades()
            
            return {
                "total_trades": len(trades),
                "unique_tickers": len(set(trade.ticker for trade in trades)),
                "buy_trades": len([t for t in trades if t.is_buy]),
                "sell_trades": len([t for t in trades if not t.is_buy])
            }
        except Exception as e:
            logger.error(f"Error getting trades summary: {e}")
            return {"total_trades": 0, "unique_tickers": 0, "buy_trades": 0, "sell_trades": 0}
