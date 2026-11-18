import json
import time
from dataclasses import replace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm

from build3d_api.main import create_app
from build3d_api.store import Store, StoreError
from build3d_api.trusted_identity import (
    ExternalJWTAuthenticator,
    TrustedIdentityError,
    load_providers,
)


ISSUER = "https://identity.example.com/"
AUDIENCE = "build3d-api"
JWKS_URL = "https://identity.example.com/.well-known/jwks.json"


class StaticFetcher:
    def __init__(self, document):
        self.document = document
        self.calls = []

    def __call__(self, url, timeout):
        self.calls.append((url, timeout))
        return self.document


@pytest.fixture
def signing_material():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = RSAAlgorithm.to_jwk(private.public_key(), as_dict=True)
    public_jwk.update({"kid": "key-1", "use": "sig", "alg": "RS256"})
    return private, {"keys": [public_jwk]}


def provider_file(tmp_path, **overrides):
    entry = {
        "issuer": ISSUER,
        "audiences": [AUDIENCE],
        "jwks_url": JWKS_URL,
        "algorithms": ["RS256"],
        "max_token_lifetime_seconds": 600,
        "leeway_seconds": 5,
        "jwks_cache_seconds": 300,
        "refresh_cooldown_seconds": 30,
        "timeout_seconds": 2,
    }
    entry.update(overrides)
    path = tmp_path / "providers.json"
    path.write_text(json.dumps({"schema_version": 1, "providers": [entry]}))
    return path


def token(private, *, issuer=ISSUER, subject="provider-alice", audience=AUDIENCE,
          lifetime=300, kid="key-1", algorithm="RS256", now=None, extra=None):
    now = int(time.time()) if now is None else int(now)
    claims = {
        "iss": issuer,
        "sub": subject,
        "aud": audience,
        "iat": now,
        "exp": now + lifetime,
        # This claim must never influence ownership.
        "email": "someone-else@example.com",
    }
    if extra:
        claims.update(extra)
    key = private if algorithm == "RS256" else b"not-a-trusted-secret"
    return jwt.encode(claims, key, algorithm=algorithm, headers={"kid": kid})


def jwt_app(env, path, fetcher, *, requests_per_minute=None):
    settings = replace(
        env.settings,
        external_jwt_auth_enabled=True,
        identity_provider_file=path,
        **(
            {"requests_per_minute": requests_per_minute}
            if requests_per_minute is not None
            else {}
        ),
    )
    authenticator = ExternalJWTAuthenticator.from_file(path, fetcher=fetcher)
    return create_app(
        settings,
        engine=env.engine,
        storage=env.client.app.state.artifact_storage,
        jwt_authenticator=authenticator,
    ), authenticator


def test_valid_external_jwt_maps_only_issuer_subject_and_keeps_api_keys(env, tmp_path, signing_material):
    private, jwks = signing_material
    path = provider_file(tmp_path)
    fetcher = StaticFetcher(jwks)
    env.store.link_external_identity(env.alice["user_id"], ISSUER, "provider-alice")
    alice_project = env.store.create_project(env.alice["user_id"], "Alice private")

    app, _ = jwt_app(env, path, fetcher)
    with TestClient(app) as client:
        assertion = token(private)
        headers = {"Authorization": f"Bearer {assertion}"}
        response = client.get("/v1/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["user_id"] == env.alice["user_id"]

        projects = client.get("/v1/projects", headers=headers)
        assert [item["id"] for item in projects.json()["items"]] == [alice_project["id"]]

        # Existing developer/API-key credentials remain independently valid.
        assert client.get("/v1/me", headers=env.other).json()["user_id"] == env.bob["user_id"]

    assert fetcher.calls == [(JWKS_URL, 2.0)]


def test_untrusted_issuer_and_disallowed_algorithm_never_fetch_jwks(env, tmp_path, signing_material):
    private, jwks = signing_material
    path = provider_file(tmp_path)
    fetcher = StaticFetcher(jwks)
    env.store.link_external_identity(env.alice["user_id"], ISSUER, "provider-alice")
    app, _ = jwt_app(env, path, fetcher)

    with TestClient(app) as client:
        unknown = token(private, issuer="https://attacker.example/")
        assert client.get("/v1/me", headers={"Authorization": f"Bearer {unknown}"}).status_code == 401

        hs = token(private, algorithm="HS256")
        assert client.get("/v1/me", headers={"Authorization": f"Bearer {hs}"}).status_code == 401

    assert fetcher.calls == []


@pytest.mark.parametrize("mutator", ["audience", "lifetime", "subject"])
def test_invalid_or_unmapped_assertions_fail_closed(env, tmp_path, signing_material, mutator):
    private, jwks = signing_material
    path = provider_file(tmp_path)
    fetcher = StaticFetcher(jwks)
    env.store.link_external_identity(env.alice["user_id"], ISSUER, "provider-alice")
    app, _ = jwt_app(env, path, fetcher)

    kwargs = {}
    if mutator == "audience":
        kwargs["audience"] = "wrong-audience"
    elif mutator == "lifetime":
        kwargs["lifetime"] = 601
    else:
        kwargs["subject"] = "not-linked"

    with TestClient(app) as client:
        response = client.get(
            "/v1/me",
            headers={"Authorization": f"Bearer {token(private, **kwargs)}"},
        )
        assert response.status_code == 401


def test_unknown_kid_does_not_force_unbounded_jwks_refresh(env, tmp_path, signing_material):
    private, jwks = signing_material
    path = provider_file(tmp_path, refresh_cooldown_seconds=60)
    fetcher = StaticFetcher(jwks)
    env.store.link_external_identity(env.alice["user_id"], ISSUER, "provider-alice")
    app, _ = jwt_app(env, path, fetcher)
    assertion = token(private, kid="unknown-key")
    headers = {"Authorization": f"Bearer {assertion}"}

    with TestClient(app) as client:
        assert client.get("/v1/me", headers=headers).status_code == 401
        assert client.get("/v1/me", headers=headers).status_code == 401

    assert len(fetcher.calls) == 1


def test_external_identity_rate_limit_is_database_backed(env, tmp_path, signing_material):
    private, jwks = signing_material
    path = provider_file(tmp_path)
    fetcher = StaticFetcher(jwks)
    env.store.link_external_identity(env.alice["user_id"], ISSUER, "provider-alice")
    app, _ = jwt_app(env, path, fetcher, requests_per_minute=2)
    headers = {"Authorization": f"Bearer {token(private)}"}

    with TestClient(app) as client:
        assert client.get("/v1/me", headers=headers).status_code == 200
        assert client.get("/v1/me", headers=headers).status_code == 200
        limited = client.get("/v1/me", headers=headers)
        assert limited.status_code == 429
        assert limited.headers["retry-after"] == "60"


def test_disabled_product_user_cannot_use_valid_external_assertion(env, tmp_path, signing_material):
    private, jwks = signing_material
    path = provider_file(tmp_path)
    fetcher = StaticFetcher(jwks)
    env.store.link_external_identity(env.alice["user_id"], ISSUER, "provider-alice")
    app, _ = jwt_app(env, path, fetcher)

    with TestClient(app) as client:
        headers = {"Authorization": f"Bearer {token(private)}"}
        assert client.get("/v1/me", headers=headers).status_code == 200
        env.store.disable_user(env.alice["user_id"])
        response = client.get("/v1/me", headers=headers)
        assert response.status_code == 401


def test_feature_flag_disabled_rejects_external_jwt_without_fetch(env, signing_material):
    private, _ = signing_material
    response = env.client.get(
        "/v1/me",
        headers={"Authorization": f"Bearer {token(private)}"},
    )
    assert response.status_code == 401


def test_external_identity_store_rate_limit_is_atomic(env):
    issuer = "https://rate.example.com"
    subject = "rate-user"
    env.store.link_external_identity(env.alice["user_id"], issuer, subject)
    limited = Store(env.engine, replace(env.settings, requests_per_minute=2))
    assert limited.authenticate_external_identity(issuer, subject, now=1000) == env.alice["user_id"]
    assert limited.authenticate_external_identity(issuer, subject, now=1000) == env.alice["user_id"]
    with pytest.raises(StoreError) as exc:
        limited.authenticate_external_identity(issuer, subject, now=1001)
    assert exc.value.status == 429
    assert limited.authenticate_external_identity(issuer, subject, now=1060) == env.alice["user_id"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"algorithms": ["HS256"]},
        {"jwks_url": "http://metadata.example.com/jwks"},
        {"issuer": "http://identity.example.com"},
        {"audiences": []},
        {"max_token_lifetime_seconds": 3601},
    ],
)
def test_provider_configuration_rejects_unsafe_values(tmp_path, overrides):
    path = provider_file(tmp_path, **overrides)
    with pytest.raises(TrustedIdentityError):
        load_providers(path)
