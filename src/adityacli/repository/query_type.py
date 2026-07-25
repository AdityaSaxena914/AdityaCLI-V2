from enum import StrEnum


class RepositoryQueryType(StrEnum):
    SYMBOL = "symbol"
    CALLERS = "callers"