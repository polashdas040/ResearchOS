import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Literal
from uuid import UUID, uuid4


class TokenError(Exception):
    """Raised when a signed token cannot be trusted."""


@dataclass(frozen=True)
class TokenClaims:
    subject: UUID
    organization_id: UUID
    token_id: UUID
    token_type: Literal["access", "refresh"]
    expires_at: int


class TokenService:
    def __init__(
        self,
        secret_key: str,
        access_token_ttl: timedelta = timedelta(minutes=15),
        refresh_token_ttl: timedelta = timedelta(days=30),
    ) -> None:
        self._secret_key = secret_key.encode()
        self._access_token_ttl = access_token_ttl
        self._refresh_token_ttl = refresh_token_ttl

    def create_access_token(self, user_id: UUID, organization_id: UUID) -> str:
        return self._encode(user_id, organization_id, "access", self._access_token_ttl)

    def create_refresh_token(self, user_id: UUID, organization_id: UUID) -> str:
        return self._encode(user_id, organization_id, "refresh", self._refresh_token_ttl)

    def decode(self, token: str, expected_type: Literal["access", "refresh"]) -> TokenClaims:
        try:
            header_text, payload_text, signature_text = token.split(".")
        except ValueError as exc:
            raise TokenError("Malformed token") from exc

        signed = f"{header_text}.{payload_text}".encode()
        expected_signature = self._sign(signed)
        provided_signature = self._decode_base64(signature_text)
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise TokenError("Invalid token signature")

        payload = json.loads(self._decode_base64(payload_text))
        if payload.get("typ") != expected_type:
            raise TokenError("Unexpected token type")
        if int(payload["exp"]) < int(time.time()):
            raise TokenError("Expired token")

        return TokenClaims(
            subject=UUID(payload["sub"]),
            organization_id=UUID(payload["org"]),
            token_id=UUID(payload["jti"]),
            token_type=expected_type,
            expires_at=int(payload["exp"]),
        )

    def fingerprint(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _encode(
        self,
        user_id: UUID,
        organization_id: UUID,
        token_type: Literal["access", "refresh"],
        ttl: timedelta,
    ) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "org": str(organization_id),
            "jti": str(uuid4()),
            "typ": token_type,
            "exp": int(time.time() + ttl.total_seconds()),
        }
        header_text = self._encode_base64(json.dumps(header, separators=(",", ":")).encode())
        payload_text = self._encode_base64(json.dumps(payload, separators=(",", ":")).encode())
        signature_text = self._encode_base64(self._sign(f"{header_text}.{payload_text}".encode()))
        return f"{header_text}.{payload_text}.{signature_text}"

    def _sign(self, payload: bytes) -> bytes:
        return hmac.new(self._secret_key, payload, hashlib.sha256).digest()

    @staticmethod
    def _encode_base64(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode()

    @staticmethod
    def _decode_base64(value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(value + padding)
