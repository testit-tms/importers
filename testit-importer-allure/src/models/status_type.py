from enum import Enum


class StatusType(Enum):
    SUCCEEDED = 'Succeeded'
    FAILED = 'Failed'
    INCOMPLETE = 'Incomplete'
    INPROGRESS = 'InProgress'
    PENDING = 'Pending'
