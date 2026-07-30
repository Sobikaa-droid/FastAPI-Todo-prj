from . import ServiceException


class JWTException(ServiceException):
    """Base exception for JWT-related errors"""
    pass


class JWTEncodeError(JWTException):
    """Raised when JWT encoding fails"""
    pass


class JWTTypeError(JWTEncodeError):
    """Raised when JWT type is invalid"""
    pass


class JWTDecodeError(JWTException):
    """Raised when JWT decoding fails"""
    pass


class JWTExpiredError(JWTDecodeError):
    """Raised when JWT is expired"""
    def __init__(self):
        message = "Token is expired"
        super().__init__(message)


class JWTInvalidError(JWTDecodeError):
    """Raised when JWT is invalid/malformed"""
    def __init__(self, reason: str = None):
        message = "Invalid token" if not reason else f"Invalid token: {reason}"
        super().__init__(message)
        self.reason = reason


class JWTMissingError(JWTDecodeError):
    """Raised when JWT is missing"""
    def __init__(self):
        message = "Missing token"
        super().__init__(message)
