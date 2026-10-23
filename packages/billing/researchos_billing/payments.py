import hashlib
import hmac
import json
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.billing.researchos_billing.ledger import CreditLedger


class PaymentWebhook(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(min_length=1)
    wallet_id: UUID
    credits: int = Field(gt=0)
    payment_reference: str = Field(min_length=1)


class PaymentProcessor:
    def __init__(self, ledger: CreditLedger, webhook_secret: str) -> None:
        if not webhook_secret:
            raise ValueError("webhook secret is required")
        self._ledger = ledger
        self._secret = webhook_secret.encode()
        self._processed: dict[str, PaymentWebhook] = {}
        self._processed_references: dict[str, PaymentWebhook] = {}

    async def handle_webhook(self, raw_payload: bytes, signature: str) -> PaymentWebhook:
        expected = hmac.new(self._secret, raw_payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise ValueError("invalid webhook signature")
        try:
            payload = PaymentWebhook.model_validate(json.loads(raw_payload))
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError("invalid webhook payload") from exc
        existing = self._processed.get(payload.event_id)
        if existing is not None:
            if existing != payload:
                raise ValueError("payment event payload mismatch")
            return existing
        existing_reference = self._processed_references.get(payload.payment_reference)
        if existing_reference is not None:
            if (
                existing_reference.wallet_id != payload.wallet_id
                or existing_reference.credits != payload.credits
            ):
                raise ValueError("payment reference payload mismatch")
            self._processed[payload.event_id] = existing_reference
            return existing_reference
        await self._ledger.purchase(
            payload.wallet_id,
            payload.credits,
            reference=payload.payment_reference,
        )
        self._processed[payload.event_id] = payload
        self._processed_references[payload.payment_reference] = payload
        return payload
