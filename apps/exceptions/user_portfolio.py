""" Exceptions for User Portfolio """


class UserPortfolioNotFound(Exception):
    """
        Exception for user portfolio data Not found
    """

    def __init__(self, message=None):
        if message:
            self.message = message

    code = 106


class UserInstructionNotFound(Exception):
    """
        Exception for user rebalancing instruction data Not found
    """

    def __init__(self, message=None):
        if message:
            self.message = message

    code = 107
