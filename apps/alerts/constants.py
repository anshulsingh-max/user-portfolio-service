from enum import Enum

from django.db.models import TextChoices


class PortfolioThresholdTypes(TextChoices):
    """
    Enum representing different threshold types for a portfolio.
    """
    PROFIT_TARGET = "profit_target", "Profit Target"
    STOP_LOSS = "stop_loss", "Stop Loss"


class Status(TextChoices):
    """
    Enum representing the status of a portfolio threshold rule.
    """
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    PROCESSING = "processing", "Processing"


class ThresholdSource(TextChoices):
    USER = "user", "User"
    ADMIN = "admin", "Admin"
    DEALER = "dealer", "Dealer"


class PortfolioSides(TextChoices):
    LONG = "long", "Long"
    SHORT = "short", "Short"


ACTIVE_PORTFOLIOS_CACHE_KEY = "alerts:active_user_portfolios"
ACTIVE_HOLDINGS_THRESHOLD_CACHE_KEY = "alerts:active_holdings_threshold"
ACTIVE_PORTFOLIOS_CACHE_TIMEOUT = 25200

PORTFOLIO_THRESHOLDS_CACHE_PREFIX = "alerts:portfolio_thresholds:"
PORTFOLIO_THRESHOLDS_CACHE_TIMEOUT = ACTIVE_PORTFOLIOS_CACHE_TIMEOUT

HOLDINGS_CACHE_KEY = "alerts:all_holdings"
HOLDINGS_CACHE_TIMEOUT = ACTIVE_PORTFOLIOS_CACHE_TIMEOUT

class Asset(Enum):
    CASH = 'cash'
