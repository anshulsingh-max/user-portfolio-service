"""
    Module for User Portfolio Rebalance
"""


class PortfolioRebalanceEndOfState(Exception):
    """
        Exception to be raised when User portfolio rebalance is already in it's last state
    """

    def __init__(self):
        self.message = "Portfolio rebalance is already at it's end of state and can't be updated now."

    code = 102


class PortfolioRebalancePending(Exception):
    """
        Exception to be raised when User portfolio rebalance is pending and can't start another
    """

    def __init__(self, message=""):
        self.message = "Already a user portfolio rebalance is in pending state, can't start another." + message

    code = 103
