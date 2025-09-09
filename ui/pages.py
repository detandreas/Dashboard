"""
Dashboard pages module - refactored for better organization.
This file maintains backward compatibility by re-exporting all page classes.
"""

# Import all page classes from their new locations
from ui.base_page import BasePage
from ui.tickers_page import TickersPage
from ui.portfolio_page import PortfolioPage
from ui.trades_page import TradesPage
from ui.finance_page import FinancePage
from ui.settings_page import SettingsPage
from ui.page_factory import PageFactory

# Re-export all classes for backward compatibility
__all__ = [
    'BasePage',
    'TickersPage', 
    'PortfolioPage',
    'TradesPage',
    'FinancePage',
    'SettingsPage',
    'PageFactory'
]
