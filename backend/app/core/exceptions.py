class AppException(Exception):
    """Base exception for application."""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = 400,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, resource: str, id: int | str):
        super().__init__(
            message=f"{resource} with id {id} not found",
            status_code=404,
        )


class InvalidCredentialsError(AppException):
    """Invalid authentication credentials."""

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(
            message=message,
            status_code=401,
        )


class PermissionDeniedError(AppException):
    """User does not have permission."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            status_code=403,
        )


class ConflictError(AppException):
    """Resource already exists."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            message=message,
            status_code=409,
        )


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(
            message=message,
            status_code=422,
        )
