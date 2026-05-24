"""
    Module to define constants.
"""
from enum import Enum

from django.conf import settings

USER_PORTFOLIO = 'user_portfolio'


class UserPortfolioStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'

    CHOICES = ((ACTIVE, ACTIVE),
               (INACTIVE, INACTIVE))


class RebalanceTypes(Enum):
    INITIAL = 'initial'
    REBALANCE = 'rebalance'
    RECONCILIATION = 'reconciliation'
    CASH_ALLOCATION = 'cash_allocation'
    INVESTED = 'invested'
    INVESTED_REBALANCE = 'invested_rebalance'
    CHOICES = (
        (INITIAL, INITIAL),
        (REBALANCE, REBALANCE),
        (RECONCILIATION, RECONCILIATION),
        (CASH_ALLOCATION, CASH_ALLOCATION),
    )


class CashTransaction(Enum):
    ADD = 'add'
    WITHDRAW = 'withdraw'
    REBALANCE = 'rebalance'

    CHOICES = (
        (ADD, ADD),
        (WITHDRAW, WITHDRAW),
        (REBALANCE, REBALANCE),
    )


class States(Enum):
    PENDING = 'pending'
    PARTIAL = 'partial'
    COMPLETE = 'complete'

    CHOICES = (
        (PENDING, PENDING),
        (PARTIAL, PARTIAL),
        (COMPLETE, COMPLETE),
    )

    BI_STEP_FLOW = (PENDING, COMPLETE)
    TRI_STEP_FLOW = (PENDING, PARTIAL, COMPLETE)

    REBALANCE_MAPPING = {
        RebalanceTypes.INITIAL.value: BI_STEP_FLOW,
        RebalanceTypes.RECONCILIATION.value: BI_STEP_FLOW,
        RebalanceTypes.REBALANCE.value: TRI_STEP_FLOW,
        RebalanceTypes.CASH_ALLOCATION.value: BI_STEP_FLOW,
    }


class Side(Enum):
    BUY = 'buy'
    SELL = 'sell'

    CHOICES = (
        (BUY, BUY),
        (SELL, SELL)
    )


class OrderStatus(Enum):
    WAITING = 'waiting'
    PARTIAL = 'partial'
    FILLED = 'filled'
    CANCEL = "cancel"
    FAILED = "failed"

    WAITING_STATES = [WAITING, PARTIAL]
    COMPLETED_STATES = [FILLED, CANCEL, FAILED]
    FAILURE_STATES = [CANCEL, FAILED]

    CHOICES = (
        (WAITING, WAITING),
        (PARTIAL, PARTIAL),
        (FILLED, FILLED),
        (CANCEL, CANCEL),
        (FAILED, FAILED),
    )


class Asset(Enum):
    CASH = 'cash'
    CASH_PRICE = 1


class RebalanceTransactionTypes(Enum):
    INITIAL = 'initial'
    T0 = 't0'
    T1 = 't1'
    CASH_ALLOCATION = 'cash_allocation'

    CHOICES = (
        (INITIAL, INITIAL),
        (T0, T0),
        (T1, T1),
        (CASH_ALLOCATION, CASH_ALLOCATION),
    )

    ALL = [INITIAL, T0, T1]


class RebalanceTransactionStates(Enum):
    PROCESSING = 'processing'
    PARTIALLY_COMPLETED = 'partially_completed'
    RETRY_ENABLED = 'retry_enabled'
    COMPLETED = 'completed'
    MANUALLY_COMPLETED = 'manually_completed'
    SKIPPED = 'skipped'
    COMPLETION_STATES = [PARTIALLY_COMPLETED, COMPLETED, MANUALLY_COMPLETED, SKIPPED]

    CHOICES = (
        (PROCESSING, PROCESSING),
        (PARTIALLY_COMPLETED, PARTIALLY_COMPLETED),
        (COMPLETED, COMPLETED),
        (RETRY_ENABLED, RETRY_ENABLED),
        (MANUALLY_COMPLETED, MANUALLY_COMPLETED),
        (SKIPPED, SKIPPED),
    )

    MANUALLY_COMPLETED_STATUS_CHOICES = (
        (MANUALLY_COMPLETED, MANUALLY_COMPLETED),
        (SKIPPED, SKIPPED)
    )

class InvestmentStatus(Enum):
    INVESTED = "invested"
    UNINVESTED = "uninvested"

    CHOICES = (
        (INVESTED, INVESTED),
        (UNINVESTED, UNINVESTED)
    )


class FailureMessage(Enum):
    DEFAULT = "Order failed, please contact your broker for more information"


SELL_CALLBACK_SLUG = "callback/trade/actions"
BUSINESS_REBALANCE_CALLBACK_URL = f"{settings.REBALANCING_BUSINESS_URL}/{SELL_CALLBACK_SLUG}"


class BrokerEnum(Enum):
    """
        Brokers
    """
    LKP = "lkp"
    AXIS = "axis"
    ZERODHA = "zerodha"
    PAPER_TRADE = "paper_trade"
    PL = "pl"
    JM = 'jm'
    HDFC = 'hdfc'
    BNR = 'bnr'
    ALMONDZ = 'almondz'
    # adding demo broker
    DEMO_BROKER = 'demo'
    JM_PRO = "jm_pro"
    EMKAY = 'emkay'
    SYMPHONY = 'symphony'
    HDFCIR = "hdfcir"
    YSL = 'ysl'
    MANDOT = 'mandot'

    ALL = [AXIS, ZERODHA, LKP, PAPER_TRADE, PL, JM, HDFC, BNR, DEMO_BROKER, ALMONDZ, JM_PRO, EMKAY, SYMPHONY, HDFCIR, YSL, MANDOT]

    CHOICES = (
        (AXIS, AXIS),
        (ZERODHA, ZERODHA),
        (LKP, LKP),
        (PAPER_TRADE, PAPER_TRADE),
        (PL, PL),
        (JM, JM),
        (HDFC, HDFC),
        (BNR, BNR),
        (DEMO_BROKER, DEMO_BROKER),
        (EMKAY, EMKAY),
        (ALMONDZ, ALMONDZ),
        (JM_PRO, JM_PRO),
        (SYMPHONY, SYMPHONY),
        (HDFCIR, HDFCIR),
        (YSL, YSL),
        (MANDOT, MANDOT)
    )


class Proxy(Enum):
    """
    Enumeration for different proxy types.

    Attributes:
        DEALER (str): Represents a dealer proxy type with the value 'dealer'.
        USER (str): Represents a user proxy type with the value 'user'.

    CHOICES (tuple): A tuple of tuples containing the choices for proxy types,
                     useful for model field choices or form fields.
    """

    DEALER = 'dealer'
    USER = 'user'

    CHOICES = (
        (DEALER, DEALER),
        (USER, USER)
    )


class BasketStates(Enum):
    """
    Enumeration representing the various states of a user's basket.

    Attributes:
        UNINVESTED (str): The basket is uninvested when the payment has been done but no investments were done.
        WAITING (str): The basket is waiting for further action or confirmation.
        MONITORING (str): The basket is currently being monitored for performance.
        COMPLETE (str): The basket has completed its intended operations.

    Choices:
        A tuple of choices for use in database models and forms, providing a way
        to select one of the predefined states.
    """
    UNINVESTED = 'uninvested'
    WAITING = 'waiting'
    MONITORING = 'monitoring'
    COMPLETE = 'complete'

    CHOICES = (
        (UNINVESTED, UNINVESTED),
        (WAITING, WAITING),
        (MONITORING, MONITORING),
        (COMPLETE, COMPLETE)
    )


class OrderCurrentStatus(Enum):
    """
    Enum representing the possible states of an order.

    Attributes:
        WAITING (str): The order is created but not yet processed or executed.
        BUY_IN_PROGRESS (str): The order is in the process of being bought but not yet completed.
        SELL_IN_PROGRESS (str): The order is in the process of being sold but not yet completed.
        BUY (str): The order has been fully bought.
        SL_WAITING (str): A stop-loss order is pending or awaiting placement.
        SL_PLACED (str): A stop-loss order has been successfully placed.
        SELL (str): The order has been fully sold or is in the process of being sold.
        SKIP (str): The order has been skipped or disregarded.

    Additional Attributes:
        COMPLETE_STATES (list): A list of states that signify the order is complete, either by selling or skipping.
        STATES_WITHOUT_SL (list): A list of states that do not involve stop-loss processing.
        STATES_WITH_SL (list): A list of states that involve stop-loss processing.

    CHOICES (tuple): A tuple of tuples containing the possible state choices,
        where each inner tuple represents a state and its corresponding value.
        This is typically used in Django models to define a field with limited choices.

    Usage:
        This Enum can be used to standardize the states of an order in the system.
        The `CHOICES` attribute is particularly useful when defining Django model fields
        that limit the values to these predefined states.
    """

    WAITING = 'waiting'
    BUY_IN_PROGRESS = 'buy_in_progress'
    SELL_IN_PROGRESS = 'sell_in_progress'
    BUY = 'buy'
    SL_WAITING = 'sl_waiting'
    SL_PLACED = 'sl_placed'
    SELL = 'sell'
    SKIP = 'skip'

    COMPLETE_STATES = [SELL, SKIP]
    STATES_WITHOUT_SL = [WAITING, BUY_IN_PROGRESS, BUY, SELL_IN_PROGRESS, SELL, SKIP]
    STATES_WITH_SL = [WAITING, BUY_IN_PROGRESS, BUY, SL_WAITING, SL_PLACED, SELL, SKIP]

    CHOICES = (
        (WAITING, WAITING),
        (BUY_IN_PROGRESS, BUY_IN_PROGRESS),
        (SELL_IN_PROGRESS, SELL_IN_PROGRESS),
        (BUY, BUY),
        (SL_WAITING, SL_WAITING),
        (SL_PLACED, SL_PLACED),
        (SELL, SELL),
        (SKIP, SKIP)
    )

class PhaseCallbackLogEnum(Enum):
    """
    Enum representing the possible states of a phase callback log.
    """
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

    CHOICES = (
        (PROCESSING, PROCESSING),
        (COMPLETED, COMPLETED),
        (FAILED, FAILED)
    )


class BasketTypes(Enum):
    """
    Enum representing the types of baskets that can be created.

    Attributes:
        NORMAL (str): A normal basket type.
        CO (str): A CO (Cover Order) basket type.

    CHOICES (tuple): A tuple of tuples containing the possible basket type choices,
        where each inner tuple represents a basket type and its corresponding value.
        This is typically used in Django models to define a field with limited choices.
    """

    NORMAL = 'normal'
    CO = 'co'

    CHOICES = (
        (NORMAL, NORMAL),
        (CO, CO)
    )


class ProductTypes(Enum):
    """
    Enum representing the types of products associated with baskets.

    Attributes:
        MTF (str): Margin Trading Facility (MTF) product type.
        INTRADAY (str): Intraday trading product type.

    CHOICES (tuple): A tuple of tuples containing the possible product type choices,
        where each inner tuple represents a product type and its corresponding value.
        This is typically used in Django models to define a field with limited choices.
    """

    MTF = 'mtf'
    INTRADAY = 'intraday'
    EQUITY = 'equity'

    CHOICES = (
        (MTF, MTF),
        (INTRADAY, INTRADAY),
        (EQUITY, EQUITY)
    )


class Exchange(Enum):
    """
        Constants data enum class
    """
    NSE = "NSE"
    BSE = "BSE"


SERVICE_NAME = 'User Portfolio'


class NotificationEventsMTF(Enum):
    """
    Enum class representing different notification events for MTF (Margin Trading Facility).

    Attributes:
    - PROFIT_TARGET_HIT_1_MTF (str): Notification event for when the first profit target is hit.
    - PROFIT_TARGET_HIT_2_MTF (str): Notification event for when the second profit target is hit.
    - STOP_LOSS_HIT_MTF (str): Notification event for when the stop loss is hit.
    """
    PROFIT_TARGET_HIT_1_MTF = 'profit_target_hit_1_mtf'
    PROFIT_TARGET_HIT_2_MTF = 'profit_target_hit_2_mtf'
    STOP_LOSS_HIT_MTF = 'stop_loss_hit_mtf'
    HOLDING_PROFIT_TARGET_HIT = "holding_profit_target_hit"
    HOLDING_STOP_LOSS_HIT = "holding_stop_loss_hit"


class RebalanceStrategy(Enum):
    """
    Enum represents rebalance strategy
    """
    COMPLETE = "complete"
    PARTIAL = "partial"

    @staticmethod
    def choices():
        return [(rebalance_strategy.value, rebalance_strategy.name) for rebalance_strategy in RebalanceStrategy]


class OrderInstructionSources(Enum):
    """
    Enum represents order instruction sources
    """
    MANUAL = "manual"
    RECONCILE = "reconcile"
    SQUARE_OFF = "square_off"
    MARGIN_CALL = "margin_call"
    RETRY = "retry"
    SKIP = "skip"

    CHOICES = (
        (MANUAL, MANUAL),
        (RECONCILE, RECONCILE),
        (SQUARE_OFF, SQUARE_OFF),
        (MARGIN_CALL, MARGIN_CALL),
        (RETRY, RETRY),
        (SKIP, SKIP),
    )


class Strategy(Enum):

    REBALANCE = "rebalance"
    ONE_TIME = "one_time"

    CHOICES = (
        (REBALANCE, REBALANCE),
        (ONE_TIME, ONE_TIME),
    )


class RebalanceCloseReason(Enum):
    MANUAL_NEW_REBALANCE = "Manually closed as new rebalance is present"

    CHOICES = (
        (MANUAL_NEW_REBALANCE, MANUAL_NEW_REBALANCE),
    )



class HoldingStatus(Enum):
    MULTI_ASSET = "multi-asset"
    CASH = "cash"
    HOLDINGS = "holdings"

    CHOICES = (
        (MULTI_ASSET, MULTI_ASSET),
        (CASH, CASH),
        (HOLDINGS, HOLDINGS),
    )
