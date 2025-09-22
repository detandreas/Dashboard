import logging
from typing import List

from ui.Pages.base_page import BasePage
from ui.Pages.tickers_page import TickersPage
from ui.Pages.portfolio_page import PortfolioPage
from ui.Pages.trades_page import TradesPage
from ui.Pages.finance_page import FinancePage
from ui.Pages.settings_page import SettingsPage
from services.portfolio_service import PortfolioService
from ui.Components import UIComponentFactory
from config.settings import Config

logger = logging.getLogger(__name__)

class PageFactory:
    """Factory for creating dashboard pages with lazy loading."""
    
    def __init__(self, portfolio_service: PortfolioService, ui_factory: UIComponentFactory, config: Config, goal_service=None):
        self.portfolio_service = portfolio_service
        self.ui_factory = ui_factory
        self.config = config
        self.goal_service = goal_service
        
        # Page registry - lazy initialization to avoid circular imports
        self._page_registry = {
            "tickers": self._create_tickers_page,
            "portfolio": self._create_portfolio_page,
            "trades": self._create_trades_page,
            "finances": self._create_finances_page,
            "settings": self._create_settings_page
        }
        
        # Cache for instantiated pages
        self._page_cache = {}
        
        logger.info(f"PageFactory initialized with {len(self._page_registry)} page types")
    
    def create_page(self, page_name: str) -> BasePage:
        """Create page instance by name with caching."""
        if page_name not in self._page_registry:
            available_pages = list(self._page_registry.keys())
            raise ValueError(f"Unknown page: {page_name}. Available: {available_pages}")
        
        # Return cached page if exists
        if page_name in self._page_cache:
            logger.debug(f"Returning cached page: {page_name}")
            return self._page_cache[page_name]
        
        # Create new page instance
        logger.debug(f"Creating new page instance: {page_name}")
        page_instance = self._page_registry[page_name]()
        
        # Cache for future use
        self._page_cache[page_name] = page_instance
        
        return page_instance
    
    def _create_tickers_page(self) -> TickersPage:
        """Create tickers analysis page."""
        return TickersPage(self.portfolio_service, self.ui_factory)
    
    def _create_portfolio_page(self) -> PortfolioPage:
        """Create portfolio overview page."""
        return PortfolioPage(self.portfolio_service, self.ui_factory, self.goal_service)
    
    def _create_trades_page(self) -> TradesPage:
        """Create trades history page."""
        return TradesPage(self.portfolio_service, self.ui_factory)
    
    def _create_finances_page(self) -> FinancePage:
        """Create personal finances page."""
        return FinancePage(self.ui_factory, self.config)
    
    def _create_settings_page(self) -> SettingsPage:
        """Create application settings page."""
        return SettingsPage(self.ui_factory, self.config)
    
    def get_available_pages(self) -> List[str]:
        """Get list of available page names."""
        return list(self._page_registry.keys())
    
    def register_page(self, name: str, page_factory_func) -> None:
        """Register a new page type dynamically."""
        if name in self._page_registry:
            logger.warning(f"Overriding existing page registration: {name}")
        
        self._page_registry[name] = page_factory_func
        
        # Clear cache for this page if it exists
        if name in self._page_cache:
            del self._page_cache[name]
        
        logger.info(f"Registered new page type: {name}")
    
    def unregister_page(self, name: str) -> bool:
        """Unregister a page type."""
        if name not in self._page_registry:
            logger.warning(f"Attempted to unregister non-existent page: {name}")
            return False
        
        del self._page_registry[name]
        
        # Clear cache
        if name in self._page_cache:
            del self._page_cache[name]
        
        logger.info(f"Unregistered page type: {name}")
        return True
    
    def clear_cache(self) -> None:
        """Clear all cached page instances."""
        cleared_count = len(self._page_cache)
        self._page_cache.clear()
        logger.info(f"Cleared {cleared_count} cached page instances")
    
    def get_cache_status(self) -> dict:
        """Get cache status information."""
        return {
            "cached_pages": list(self._page_cache.keys()),
            "available_pages": list(self._page_registry.keys()),
            "cache_size": len(self._page_cache),
            "registry_size": len(self._page_registry)
        }
