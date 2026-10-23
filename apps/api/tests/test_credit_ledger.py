import asyncio
from uuid import uuid4

import pytest

from packages.billing.researchos_billing.ledger import (
    CreditLedger,
    LedgerEntryType,
)


@pytest.mark.asyncio
async def test_ledger_reserves_usage_releases_and_refunds_credits() -> None:
    ledger = CreditLedger()
    wallet_id = uuid4()

    await ledger.purchase(wallet_id, 100, reference="payment-1")
    reservation = await ledger.reserve(wallet_id, 40, reference="run-1")
    await ledger.record_usage(wallet_id, reservation.id, 25, reference="task-1")
    await ledger.release(wallet_id, reservation.id, 15, reference="run-1")
    await ledger.refund(wallet_id, 5, reference="payment-1")

    balance = await ledger.balance(wallet_id)
    assert balance.available == 80
    assert balance.reserved == 0
    entries = await ledger.entries(wallet_id)
    assert [entry.entry_type for entry in entries] == [
        LedgerEntryType.PURCHASE,
        LedgerEntryType.RESERVE,
        LedgerEntryType.USAGE,
        LedgerEntryType.RELEASE,
        LedgerEntryType.REFUND,
    ]


@pytest.mark.asyncio
async def test_ledger_prevents_negative_balance_and_double_spend_concurrently() -> None:
    ledger = CreditLedger()
    wallet_id = uuid4()
    await ledger.purchase(wallet_id, 50, reference="payment-1")

    results = await asyncio.gather(
        ledger.reserve(wallet_id, 40, reference="run-1"),
        ledger.reserve(wallet_id, 40, reference="run-2"),
        return_exceptions=True,
    )

    assert sum(not isinstance(result, Exception) for result in results) == 1
    balance = await ledger.balance(wallet_id)
    assert balance.available == 10
    assert balance.reserved == 40


@pytest.mark.asyncio
async def test_ledger_rejects_duplicate_usage_and_invalid_amounts() -> None:
    ledger = CreditLedger()
    wallet_id = uuid4()
    await ledger.purchase(wallet_id, 20, reference="payment-1")
    reservation = await ledger.reserve(wallet_id, 10, reference="run-1")
    await ledger.record_usage(wallet_id, reservation.id, 10, reference="task-1")

    with pytest.raises(ValueError, match="already consumed"):
        await ledger.record_usage(wallet_id, reservation.id, 1, reference="task-1")
    with pytest.raises(ValueError, match="positive"):
        await ledger.purchase(wallet_id, 0, reference="bad")
