"""
    Module for User Portfolio Rebalance Transaction Exceptions
"""


class RebalanceTransactionPending(Exception):
    """
        Exception to be raised when User portfolio rebalance transaction is pending and can't start another
    """

    def __init__(self, message=""):
        self.message = ("Already a user portfolio rebalance transaction is in pending state, can't start another." +
                        message)

    code = 104
