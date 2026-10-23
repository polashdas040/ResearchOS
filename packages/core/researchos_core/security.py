import ipaddress
from pathlib import PurePosixPath
from urllib.parse import urlparse
from uuid import UUID


class SecurityError(ValueError):
    """Raised when untrusted input crosses a protected trust boundary."""


class SecurityPolicy:
    _INJECTION_MARKERS = (
        "ignore previous instructions",
        "reveal system prompt",
        "disregard all instructions",
        "developer message",
    )
    _ACTIVE_HTML_MARKERS = (
        "<script",
        "javascript:",
        "onerror=",
        "onload=",
        "<iframe",
        "<object",
        "<embed",
    )

    @classmethod
    def validate_external_content(cls, content: str) -> str:
        normalized = content.casefold()
        if any(marker in normalized for marker in cls._INJECTION_MARKERS):
            raise SecurityError("untrusted instructions detected in external content")
        if any(marker in normalized for marker in cls._ACTIVE_HTML_MARKERS):
            raise SecurityError("active html detected in external content")
        return content

    @staticmethod
    def validate_tenant(resource_organization_id: UUID, principal_organization_id: UUID) -> bool:
        if resource_organization_id != principal_organization_id:
            raise SecurityError("tenant scope mismatch")
        return True

    @staticmethod
    def validate_object_path(path: str) -> str:
        candidate = PurePosixPath(path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise SecurityError("unsafe object path")
        return "/".join(candidate.parts)

    @staticmethod
    def validate_network_target(url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise SecurityError("invalid network target")
        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError:
            address = None
        if address is not None and (
            address.is_private or address.is_loopback or address.is_link_local
        ):
            raise SecurityError("private network target is blocked")
        return url

    @staticmethod
    def validate_tool_risk(risk_level: str, approved: bool) -> str:
        if risk_level in {"R3_EXTERNAL_WRITE", "R4_DESTRUCTIVE", "R5_FINANCIAL"} and not approved:
            raise SecurityError("tool risk requires explicit approval")
        return risk_level
