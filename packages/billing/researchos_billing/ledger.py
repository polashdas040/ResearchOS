import asyncio
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class LedgerEntryType(StrEnum):
    PURCHASE = "PURCHASE"
    RESERVE = "RESERVE"
    USAGE = "USAGE"
    RELEASE = "RELEASE"
    REFUND = "REFUND"


class CreditLedgerEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    wallet_id: UUID
    entry_type: LedgerEntryType
    amount: int = Field(gt=0)
    reference: str = Field(min_length=1)
    reservation_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CreditBalance(BaseModel):
    model_config = ConfigDict(frozen=True)

    available: int = Field(ge=0)
    reserved: int = Field(ge=0)


class CreditLedger:
    def __init__(self) -> None:
        self._entries: dict[UUID, list[CreditLedgerEntry]] = {}
        self._reservations: dict[UUID, int] = {}
        self._used_reservations: set[UUID] = set()
        self._lock = asyncio.Lock()

    async def purchase(self, wallet_id: UUID, amount: int, reference: str) -> CreditLedgerEntry:
        return await self._append(wallet_id, LedgerEntryType.PURCHASE, amount, reference)

    async def reserve(self, wallet_id: UUID, amount: int, reference: str) -> CreditLedgerEntry:
        async with self._lock:
            _validate_amount(amount)
            balance = self._balance_unlocked(wallet_id)
            if balance.available < amount:
                raise ValueError("insufficient available credits")
            entry = self._entry(wallet_id, LedgerEntryType.RESERVE, amount, reference)
            self._entries.setdefault(wallet_id, []).append(entry)
            self._reservations[entry.id] = amount
            return entry

    async def record_usage(
        self,
        wallet_id: UUID,
        reservation_id: UUID,
        amount: int,
        reference: str,
    ) -> CreditLedgerEntry:
        async with self._lock:
            _validate_amount(amount)
            reserved = self._reservations.get(reservation_id)
            if reserved is None:
                raise ValueError("reservation not found")
            if reservation_id in self._used_reservations:
                raise ValueError("reservation already consumed")
            if amount > reserved:
                raise ValueError("usage exceeds reservation")
            entry = self._entry(
                wallet_id, LedgerEntryType.USAGE, amount, reference, reservation_id
            )
            self._entries.setdefault(wallet_id, []).append(entry)
            remaining = reserved - amount
            self._reservations[reservation_id] = remaining
            if remaining == 0:
                self._used_reservations.add(reservation_id)
            return entry

    async def release(
        self,
        wallet_id: UUID,
        reservation_id: UUID,
        amount: int,
        reference: str,
    ) -> CreditLedgerEntry:
        async with self._lock:
            _validate_amount(amount)
            reserved = self._reservations.get(reservation_id)
            if reserved is None or amount > reserved:
                raise ValueError("release exceeds reservation")
            entry = self._entry(
                wallet_id, LedgerEntryType.RELEASE, amount, reference, reservation_id
            )
            self._entries.setdefault(wallet_id, []).append(entry)
            remaining = reserved - amount
            self._reservations[reservation_id] = remaining
            if remaining == 0:
                self._used_reservations.add(reservation_id)
            return entry

    async def refund(self, wallet_id: UUID, amount: int, reference: str) -> CreditLedgerEntry:
        return await self._append(wallet_id, LedgerEntryType.REFUND, amount, reference)

    async def balance(self, wallet_id: UUID) -> CreditBalance:
        async with self._lock:
            return self._balance_unlocked(wallet_id)

    async def entries(self, wallet_id: UUID) -> list[CreditLedgerEntry]:
        async with self._lock:
            return list(self._entries.get(wallet_id, []))

    async def _append(
        self,
        wallet_id: UUID,
        entry_type: LedgerEntryType,
        amount: int,
        reference: str,
    ) -> CreditLedgerEntry:
        async with self._lock:
            _validate_amount(amount)
            entry = self._entry(wallet_id, entry_type, amount, reference)
            self._entries.setdefault(wallet_id, []).append(entry)
            return entry

    def _entry(
        self,
        wallet_id: UUID,
        entry_type: LedgerEntryType,
        amount: int,
        reference: str,
        reservation_id: UUID | None = None,
    ) -> CreditLedgerEntry:
        return CreditLedgerEntry(
            wallet_id=wallet_id,
            entry_type=entry_type,
            amount=amount,
            reference=reference,
            reservation_id=reservation_id,
        )

    def _balance_unlocked(self, wallet_id: UUID) -> CreditBalance:
        entries = self._entries.get(wallet_id, [])
        purchased = sum(
            entry.amount for entry in entries if entry.entry_type in {LedgerEntryType.PURCHASE}
        )
        refunded = sum(
            entry.amount for entry in entries if entry.entry_type == LedgerEntryType.REFUND
        )
        reserved = sum(
            self._reservations.get(entry.id, 0)
            for entry in entries
            if entry.entry_type == LedgerEntryType.RESERVE
        )
        used = sum(entry.amount for entry in entries if entry.entry_type == LedgerEntryType.USAGE)
        return CreditBalance(
            available=purchased + refunded - used - reserved,
            reserved=reserved,
        )


def _validate_amount(amount: int) -> None:
    if amount <= 0:
        raise ValueError("amount must be positive")
