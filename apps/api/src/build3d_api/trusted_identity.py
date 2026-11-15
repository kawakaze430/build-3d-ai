"""Fail-closed external JWT/JWKS validation for mapped product identities.

This module trusts only operators' static provider configuration. It performs no
OIDC discovery, follows no redirects, accepts no symmetric JWT algorithms and
never uses email/name claims for ownership.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

import httpx
import jwt
from jwt import PyJWKSet
from jwt.exceptions import PyJWTError

from .store import Store, StoreError, normalize_external_issuer, normalize_external_subject


MAX_JWT_BYTES = 16 * 1024
MAX_JWKS_BYTES = 256 * 1024
ALLOWED_ALGORITHMS = frozenset({"RS256", "ES256", "EdDSA"})
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


class TrustedIdentityError(ValueError):
    """An external assertion/configuration cannot be trusted."""


@dataclass(frozen=True)
class Provider:
    issuer: str
    mapping_issuer: str
    audiences: tuple[str, ...]
    jwks_url: str
    algorithms: tuple[str, ...]
    max_token_lifetime_seconds: int
    leeway_seconds: int
    jwks_cache_seconds: int
    refresh_cooldown_seconds: int
    timeout_seconds: float


@dataclass
class _CacheEntry:
    jwks: PyJWKSet
    expires_at: float
    refreshed_at: float


JWKSFetcher = Callable[[str, float], dict]


def _clean_https_url(value: object, label: str, *, preserve_trailing_slash: bool) -> str:
    if not isinstance(value, str) or value != value.strip() or not 1 <= len(value) <= 1024:
        raise TrustedIdentityError(f"{label} must be a clean URL")
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"https", "http"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise TrustedIdentityError(f"{label} must be a clean http(s) URL")
    if parsed.scheme == "http" and parsed.hostname not in LOCAL_HOSTS:
        raise TrustedIdentityError(f"{label} must use HTTPS outside local development")
    if not preserve_trailing_slash and parsed.path.endswith("/") and parsed.path != "/":
        return value.rstrip("/")
    return value


def _bounded_int(value: object, *, default: int, low: int, high: int, label: str) -> int:
    if value is None:
        return default
    if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
        raise TrustedIdentityError(f"{label} must be between {low} and {high}")
    return value


def _parse_provider(raw: object) -> Provider:
    if not isinstance(raw, dict):
        raise TrustedIdentityError("Identity provider entry must be an object")
    allowed_keys = {
        "issuer", "audiences", "jwks_url", "algorithms",
        "max_token_lifetime_seconds", "leeway_seconds",
        "jwks_cache_seconds", "refresh_cooldown_seconds", "timeout_seconds",
    }
    if set(raw) - allowed_keys:
        raise TrustedIdentityError("Identity provider entry contains unsupported fields")

    issuer = _clean_https_url(raw.get("issuer"), "issuer", preserve_trailing_slash=True)
    # Store mapping canonicalization is intentionally separate from exact JWT
    # issuer validation; OIDC issuer strings are matched exactly.
    try:
        mapping_issuer = normalize_external_issuer(issuer)
    except StoreError as exc:
        raise TrustedIdentityError("issuer is not acceptable for product mapping") from exc

    audiences = raw.get("audiences")
    if (
        not isinstance(audiences, list)
        or not 1 <= len(audiences) <= 8
        or not all(
            isinstance(item, str)
            and item == item.strip()
            and 1 <= len(item) <= 512
            for item in audiences
        )
        or len(set(audiences)) != len(audiences)
    ):
        raise TrustedIdentityError("audiences must contain 1–8 unique nonblank strings")

    algorithms = raw.get("algorithms")
    if (
        not isinstance(algorithms, list)
        or not 1 <= len(algorithms) <= len(ALLOWED_ALGORITHMS)
        or not all(isinstance(item, str) and item in ALLOWED_ALGORITHMS for item in algorithms)
        or len(set(algorithms)) != len(algorithms)
    ):
        raise TrustedIdentityError("algorithms must be a unique asymmetric allowlist")

    jwks_url = _clean_https_url(raw.get("jwks_url"), "jwks_url", preserve_trailing_slash=True)
    max_lifetime = _bounded_int(
        raw.get("max_token_lifetime_seconds"),
        default=600, low=30, high=3600, label="max_token_lifetime_seconds",
    )
    leeway = _bounded_int(
        raw.get("leeway_seconds"), default=30, low=0, high=120, label="leeway_seconds",
    )
    cache = _bounded_int(
        raw.get("jwks_cache_seconds"), default=300, low=30, high=3600, label="jwks_cache_seconds",
    )
    cooldown = _bounded_int(
        raw.get("refresh_cooldown_seconds"),
        default=30, low=0, high=300, label="refresh_cooldown_seconds",
    )
    timeout = raw.get("timeout_seconds", 3)
    if (
        not isinstance(timeout, (int, float))
        or isinstance(timeout, bool)
        or not 0.5 <= float(timeout) <= 10
    ):
        raise TrustedIdentityError("timeout_seconds must be between 0.5 and 10")

    return Provider(
        issuer=issuer,
        mapping_issuer=mapping_issuer,
        audiences=tuple(audiences),
        jwks_url=jwks_url,
        algorithms=tuple(algorithms),
        max_token_lifetime_seconds=max_lifetime,
        leeway_seconds=leeway,
        jwks_cache_seconds=cache,
        refresh_cooldown_seconds=cooldown,
        timeout_seconds=float(timeout),
    )


def load_providers(path: Path) -> dict[str, Provider]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TrustedIdentityError("Identity provider configuration is unavailable") from exc
    if (
        not isinstance(document, dict)
        or document.get("schema_version") != 1
        or not isinstance(document.get("providers"), list)
        or not 1 <= len(document["providers"]) <= 16
        or set(document) != {"schema_version", "providers"}
    ):
        raise TrustedIdentityError("Invalid identity provider configuration")
    providers: dict[str, Provider] = {}
    mapping_issuers: set[str] = set()
    for raw in document["providers"]:
        provider = _parse_provider(raw)
        if provider.issuer in providers or provider.mapping_issuer in mapping_issuers:
            raise TrustedIdentityError("Duplicate/canonically ambiguous identity issuer")
        providers[provider.issuer] = provider
        mapping_issuers.add(provider.mapping_issuer)
    return providers


def fetch_jwks(url: str, timeout_seconds: float) -> dict:
    """Fetch a bounded JWKS document without redirects.

    The URL is operator-controlled and prevalidated. An attacker can choose
    token contents/kid but cannot choose this network destination.
    """
    data = bytearray()
    try:
        with httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
            headers={"Accept": "application/json"},
        ) as client:
            with client.stream("GET", url) as response:
                if response.status_code != 200:
                    raise TrustedIdentityError("JWKS endpoint rejected the request")
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > MAX_JWKS_BYTES:
                        raise TrustedIdentityError("JWKS response exceeds 256 KiB")
    except TrustedIdentityError:
        raise
    except httpx.HTTPError as exc:
        raise TrustedIdentityError("JWKS endpoint is unavailable") from exc

    try:
        parsed = json.loads(bytes(data))
    except (UnicodeError, ValueError) as exc:
        raise TrustedIdentityError("JWKS endpoint returned invalid JSON") from exc
    if not isinstance(parsed, dict) or not isinstance(parsed.get("keys"), list):
        raise TrustedIdentityError("JWKS endpoint returned an invalid key set")
    return parsed


class ExternalJWTAuthenticator:
    def __init__(
        self,
        providers: dict[str, Provider],
        *,
        fetcher: JWKSFetcher = fetch_jwks,
        clock: Callable[[], float] = time.time,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if not providers:
            raise TrustedIdentityError("At least one identity provider is required")
        self.providers = providers
        self.fetcher = fetcher
        self.clock = clock
        self.monotonic = monotonic
        self._cache: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()

    @classmethod
    def from_file(
        cls,
        path: Path,
        *,
        fetcher: JWKSFetcher = fetch_jwks,
        clock: Callable[[], float] = time.time,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> "ExternalJWTAuthenticator":
        return cls(
            load_providers(path),
            fetcher=fetcher,
            clock=clock,
            monotonic=monotonic,
        )

    def _fetch(self, provider: Provider, now_mono: float) -> _CacheEntry:
        document = self.fetcher(provider.jwks_url, provider.timeout_seconds)
        try:
            key_set = PyJWKSet.from_dict(document)
        except (PyJWTError, ValueError, TypeError) as exc:
            raise TrustedIdentityError("JWKS document contains unusable keys") from exc
        if not key_set.keys or len(key_set.keys) > 64:
            raise TrustedIdentityError("JWKS must contain between 1 and 64 usable keys")
        entry = _CacheEntry(
            jwks=key_set,
            expires_at=now_mono + provider.jwks_cache_seconds,
            refreshed_at=now_mono,
        )
        self._cache[provider.issuer] = entry
        return entry

    @staticmethod
    def _match_key(entry: _CacheEntry, kid: str, algorithm: str):
        matches = [key for key in entry.jwks.keys if key.key_id == kid]
        if len(matches) != 1:
            return None
        key = matches[0]
        if key.algorithm_name is not None and key.algorithm_name != algorithm:
            return None
        return key

    def _key_for(self, provider: Provider, kid: str, algorithm: str):
        now_mono = self.monotonic()
        with self._lock:
            entry = self._cache.get(provider.issuer)
            if entry is None or entry.expires_at <= now_mono:
                entry = self._fetch(provider, now_mono)
            key = self._match_key(entry, kid, algorithm)
            if key is not None:
                return key
            if now_mono - entry.refreshed_at >= provider.refresh_cooldown_seconds:
                entry = self._fetch(provider, now_mono)
                key = self._match_key(entry, kid, algorithm)
                if key is not None:
                    return key
        raise TrustedIdentityError("No trusted signing key matches the assertion")

    def authenticate(self, token: str, store: Store) -> str:
        if not isinstance(token, str) or not 1 <= len(token.encode("utf-8")) <= MAX_JWT_BYTES:
            raise StoreError(401, "Invalid external identity assertion")

        try:
            header = jwt.get_unverified_header(token)
            unverified = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_nbf": False,
                    "verify_iat": False,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )
        except (PyJWTError, UnicodeError, ValueError, TypeError):
            raise StoreError(401, "Invalid external identity assertion") from None

        issuer = unverified.get("iss") if isinstance(unverified, dict) else None
        if not isinstance(issuer, str):
            raise StoreError(401, "Invalid external identity assertion")
        provider = self.providers.get(issuer)
        if provider is None:
            # Never perform discovery or network access for an attacker-chosen issuer.
            raise StoreError(401, "External identity issuer is not trusted")

        algorithm = header.get("alg") if isinstance(header, dict) else None
        kid = header.get("kid") if isinstance(header, dict) else None
        if (
            not isinstance(algorithm, str)
            or algorithm not in provider.algorithms
            or not isinstance(kid, str)
            or not 1 <= len(kid) <= 255
        ):
            raise StoreError(401, "Invalid external identity assertion")

        try:
            signing_key = self._key_for(provider, kid, algorithm)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(provider.algorithms),
                audience=list(provider.audiences),
                issuer=provider.issuer,
                leeway=provider.leeway_seconds,
                options={"require": ["exp", "iat", "iss", "sub", "aud"]},
            )
        except (TrustedIdentityError, PyJWTError, ValueError, TypeError):
            raise StoreError(401, "Invalid external identity assertion") from None

        subject = payload.get("sub")
        issued_at = payload.get("iat")
        expires_at = payload.get("exp")
        if (
            not isinstance(issued_at, (int, float))
            or isinstance(issued_at, bool)
            or not isinstance(expires_at, (int, float))
            or isinstance(expires_at, bool)
            or expires_at <= issued_at
            or expires_at - issued_at > provider.max_token_lifetime_seconds
        ):
            raise StoreError(401, "Invalid external identity assertion")
        try:
            subject = normalize_external_subject(subject)
        except StoreError:
            raise StoreError(401, "Invalid external identity assertion") from None

        # The cryptographically validated issuer+subject is the only ownership
        # input. Email/name/profile claims are intentionally ignored.
        return store.authenticate_external_identity(
            provider.mapping_issuer,
            subject,
            now=self.clock(),
        )
