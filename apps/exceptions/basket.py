

class BasketNotFound(Exception):
    """
        Exception for basket data Not found
    """

    def __init__(self, message=None):
        if message:
            self.message = message

    code = 108
