from enum import Enum


class Status(Enum):
    PASSED = 'Passed'
    FAILED = 'Failed'
    SKIPPED = 'Skipped'
