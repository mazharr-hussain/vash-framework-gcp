"""VASH exceptions (C-02).

Exit codes:
    0   success
    1   check found failures
    2   usage error
    10  FreezeFileMissing
    11  FreezeInvalid
    12  AdapterNotInstalled
    13  ThresholdNotMet
    14  AdrNotAccepted
    15  RouteUnavailable
    16  NotAvailableYet
    17  WriteNotAllowed
"""


class VashError(Exception):
    """Base exception. Subclasses override exit_code."""
    exit_code: int = 1

    def __init__(self, message: str, fix: str):
        super().__init__(message)
        self.message = message
        self.fix = fix

    def __str__(self) -> str:
        return f"{self.message} Fix: {self.fix}"


class FreezeFileMissing(VashError):
    exit_code = 10


class FreezeInvalid(VashError):
    exit_code = 11


class AdapterNotInstalled(VashError):
    exit_code = 12


class ThresholdNotMet(VashError):
    exit_code = 13


class AdrNotAccepted(VashError):
    exit_code = 14


class RouteUnavailable(VashError):
    exit_code = 15


class NotAvailableYet(VashError):
    exit_code = 16


class WriteNotAllowed(VashError):
    exit_code = 17
