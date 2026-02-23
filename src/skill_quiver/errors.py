"""Exception hierarchy for skill-quiver."""


class QuivError(Exception):
    """Base exception for all quiv errors."""

    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


class ManifestError(QuivError):
    """Error parsing or validating skills.kdl manifest."""


class SyncError(QuivError):
    """Error during sync operations (fetch, diff, update)."""


class ValidationError(QuivError):
    """Error during skill validation."""

    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(message, exit_code)


class PackageError(QuivError):
    """Error during skill packaging."""


class InitError(QuivError):
    """Error during skill initialization."""
