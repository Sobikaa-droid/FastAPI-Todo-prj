from . import ServiceException


class UserException(ServiceException):
    """Base exception for User-related errors"""
    pass


class UserAlreadyExistsError(UserException):
    def __init__(self, message: str = "User with such credentials already exists."):
        self.message = message
        super().__init__(self.message)


class InvalidUserCredentialsError(UserException):
    def __init__(self):
        self.message = "Invalid username/password."
        super().__init__(self.message)
