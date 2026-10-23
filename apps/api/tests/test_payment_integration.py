import hashlib
import hmac
import json
from uuid import uuid4

import pytest

from packages.billing.researchos_billing.ledger import CreditLedger
from packages.billing.researchos_billing.payments import PaymentProcessor, PaymentWebhook


def signed(payload: dict[str, object], secret: str) -> tuple[bytes, str]:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return raw, signature


@pytest.mark.asyncio
async def test_verified_webhook_credits_ledger_and_is_idempotent() -> None:
    secret = "webhook-secret"
    ledger = CreditLedger()
    processor = PaymentProcessor(ledger, secret)
    payload = {
        "event_id": "evt-1",
        "wallet_id": str(uuid4()),
        "credits": 100,
        "payment_reference": "pay-1",
    }
    raw, signature = signed(payload, secret)

    first = await processor.handle_webhook(raw, signature)
    second = await processor.handle_webhook(raw, signature)

    assert first == PaymentWebhook.model_validate(payload)
    assert second == first
    assert (await ledger.balance(first.wallet_id)).available == 100


@pytest.mark.asyncio
async def test_invalid_signature_cannot_credit_wallet() -> None:
    secret = "webhook-secret"
    ledger = CreditLedger()
    processor = PaymentProcessor(ledger, secret)
    payload = {
        "event_id": "evt-2",
        "wallet_id": str(uuid4()),
        "credits": 50,
        "payment_reference": "pay-2",
    }
    raw, _ = signed(payload, secret)

    with pytest.raises(ValueError, match="signature"):
        await processor.handle_webhook(raw, "bad-signature")
    assert (await ledger.balance(PaymentWebhook.model_validate(payload).wallet_id)).available == 0


@pytest.mark.asyncio
async def test_duplicate_payment_reference_does_not_duplicate_credits() -> None:
    secret = "webhook-secret"
    wallet_id = uuid4()
    ledger = CreditLedger()
    processor = PaymentProcessor(ledger, secret)
    first_payload = {
        "event_id": "evt-3",
        "wallet_id": str(wallet_id),
        "credits": 75,
        "payment_reference": "pay-3",
    }
    duplicate_payload = {
        "event_id": "evt-4",
        "wallet_id": str(wallet_id),
        "credits": 75,
        "payment_reference": "pay-3",
    }

    await processor.handle_webhook(*signed(first_payload, secret))
    duplicate = await processor.handle_webhook(*signed(duplicate_payload, secret))

    assert duplicate.payment_reference == "pay-3"
    assert (await ledger.balance(wallet_id)).available == 75
