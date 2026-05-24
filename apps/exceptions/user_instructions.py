"""
    Module for User Instruction Exceptions
"""


class OrderAlreadyExecuted(Exception):
    """
        Exception to be raised when Order is already filled/executed and can't be updated now
    """

    def __init__(self, message=""):
        self.message = ("Order already executed/filled, and can't be modified." + message)

    code = 105
