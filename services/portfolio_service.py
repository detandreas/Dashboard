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
            
            # Calculate portfolio totals using calculation service
            total_metrics = self.calculator.calculate_portfolio_metrics(ticker_data_list)
            
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
        """Process individual ticker data using calculation service."""
        try:
            # Use calculation service to process all ticker data
            calc_results = self.calculator.process_ticker_data(ticker, trades, price_df)
            
            return TickerData(
                symbol=ticker,
                price_history=price_df,
                dca_history=calc_results['dca_history'],
                shares_per_day=calc_results['shares_per_day'],
                profit_series=calc_results['profit_series'],
                buy_dates=calc_results['buy_dates'],
                buy_prices=calc_results['buy_prices'],
                buy_quantities=calc_results['buy_quantities'],
                metrics=calc_results['metrics']
            )
            
        except Exception as e:
            logger.error(f"Error processing ticker {ticker}: {e}")
            raise
    
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
