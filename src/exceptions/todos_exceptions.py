from . import ServiceException


class TodoException(ServiceException):
    """Base exception for Tod0-related errors"""
    pass


class TodoAlreadyCompletedError(TodoException):
    pass


class TodoNotFoundError(TodoException):
    def __init__(self, message: str = "Todo not found"):
        self.message = message
        super().__init__(self.message)