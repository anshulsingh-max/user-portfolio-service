"""
    Module to define constants.
"""
from enum import Enum

HOLDINGS = 'holdings'


class TransactionStates(Enum):
    PENDING = 'pending'
    PARTIAL_COMPLETE = 'partial_complete'
    COMPLETE = 'complete'

    CHOICES = (
        (PENDING, PENDING),
        (PARTIAL_COMPLETE, PARTIAL_COMPLETE),
        (COMPLETE, COMPLETE),
    )


class TransactionParticipants(Enum):
    TARGET = 'target'
    SOURCE = 'source'

    USER = 'user'
    PORTFOLIO = 'portfolio'

    CHOICES = (
        (USER, USER),
        (PORTFOLIO, PORTFOLIO),
    )


class TransactionSide(Enum):
    DEBIT = 'debit'
    CREDIT = 'credit'
    CASH_REMOVAL = 'cash_removal'

    MAPPER = {
        CREDIT: {
            TransactionParticipants.TARGET.value: TransactionParticipants.PORTFOLIO.value,
            TransactionParticipants.SOURCE.value: TransactionParticipants.USER.value,
        },
        DEBIT: {
            TransactionParticipants.TARGET.value: TransactionParticipants.USER.value,
            TransactionParticipants.SOURCE.value: TransactionParticipants.PORTFOLIO.value,
        },
        CASH_REMOVAL: {
            TransactionParticipants.TARGET.value: TransactionParticipants.USER.value,
            TransactionParticipants.SOURCE.value: TransactionParticipants.PORTFOLIO.value,
        }
    }

    CHOICES = (
        (DEBIT, DEBIT),
        (CREDIT, CREDIT),
        (CASH_REMOVAL, CASH_REMOVAL)
    )


class TransactionTypes(Enum):
    CASH_INGESTED = 'cash_ingested'
    CASH_MISSING = 'cash_missing'
    UNINVESTED = 'uninvested'
    CASH_REMOVAL = 'cash_removal'

    CHOICES = (
        (CASH_INGESTED, CASH_INGESTED),
        (CASH_MISSING, CASH_MISSING),
        (UNINVESTED, UNINVESTED),
        (CASH_REMOVAL, CASH_REMOVAL),
    )
