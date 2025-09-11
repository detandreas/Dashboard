from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
import yfinance as yf
import logging
from datetime import datetime

from models.portfolio import Trade
from config.settings import Config

logger = logging.getLogger(__name__)

class DataServiceInterface(ABC):
    """Abstract interface for data services."""
    
    @abstractmethod
    def load_trades(self) -> List[Trade]:
        """Load trades from data source."""
        pass
    
    @abstractmethod
    def get_price_history(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Get historical price data for symbols."""
        pass
    
    @abstractmethod
    def validate_data_integrity(self) -> bool:
        """Validate data integrity."""
        pass

class YahooFinanceDataService(DataServiceInterface):
    """Yahoo Finance implementation of data service."""
    
    def __init__(self, config: Config):
        self.config = config
        self._price_cache: Optional[Dict[str, pd.DataFrame]] = None
    
    def load_trades(self) -> List[Trade]:
        """Load trades from Excel file."""
        try:
            df = pd.read_excel(self.config.database.trades_xlsx_path)
            df["Date"] = pd.to_datetime(df["Date"])
            
            trades = []
            for _, row in df.iterrows():
                trade = Trade(
                    date=row["Date"],
                    ticker=row["Ticker"],
                    price=float(row["Price"]),
                    quantity=float(row["Quantity"]),
                    direction=str(row["Direction"]).strip()
                )
                trades.append(trade)
            
            logger.info(f"Successfully loaded {len(trades)} trades")
            return trades
            
        except FileNotFoundError:
            logger.error(f"Trades file not found: {self.config.database.trades_xlsx_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading trades: {e}")
            raise
    
    def get_price_history(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Download and cache historical price data."""
        if self._price_cache is not None:
            return self._price_cache
        
        try:
            tomorrow = self.config.get_tomorrow_date()
            frames = {}
            
            for symbol in symbols:
                logger.info(f"Downloading data for {symbol}")
                df = yf.download(
                    symbol,
                    start=self.config.market.start_date,
                    end=tomorrow,
                    progress=False
                )
                
                # Handle MultiIndex columns
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                
                frames[symbol] = df
                logger.debug(f"Downloaded {len(df)} records for {symbol}")
            
            # Align dates across all symbols
            if frames:
                common_dates = set.intersection(*(set(df.index) for df in frames.values()))
                for symbol in frames:
                    frames[symbol] = frames[symbol].loc[sorted(common_dates)]
                
                logger.info(f"Aligned data to {len(common_dates)} common dates")
            
            self._price_cache = frames
            return frames
            
        except Exception as e:
            logger.error(f"Error downloading price history: {e}")
            raise
    
    def validate_data_integrity(self) -> bool:
        """Validate that all required data is available."""
        try:
            # Check if trades file exists and is readable
            trades = self.load_trades()
            if not trades:
                logger.warning("No trades found in data file")
                return False
            
            # Check if price data is available
            symbols = list(self.config.market.tracked_symbols.keys())
            price_data = self.get_price_history(symbols)
            
            for symbol in symbols:
                if symbol not in price_data or price_data[symbol].empty:
                    logger.error(f"No price data available for {symbol}")
                    return False
            
            logger.info("Data integrity validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            return False
    
    def clear_cache(self):
        """Clear cached price data."""
        self._price_cache = None
        logger.debug("Price cache cleared")
