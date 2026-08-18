"""Authentication and authorization tests."""
import pytest
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from src.auth import (
    JWTAuthenticator,
    APIKeyAuthenticator,
    APIKey,
    jwt_auth,
)


@pytest.fixture
def jwt_authenticator() -> JWTAuthenticator:
    """Create JWT authenticator."""
    return JWTAuthenticator(
        secret_key="test-secret-key",
        algorithm="HS256",
    )


@pytest.fixture
def api_key_authenticator() -> APIKeyAuthenticator:
    """Create API key authenticator."""
    return APIKeyAuthenticator()


def test_create_jwt_token(jwt_authenticator: JWTAuthenticator) -> None:
    """Test JWT token creation."""
    token = jwt_authenticator.create_token(
        user_id="user123",
        tenant_id="tenant_abc",
        scopes=["read", "write"],
    )

    assert isinstance(token, str)
    assert len(token) > 0
    assert token.count(".") == 2  # JWT has 3 parts separated by dots


def test_verify_valid_token(jwt_authenticator: JWTAuthenticator) -> None:
    """Test verification of valid JWT token."""
    token = jwt_authenticator.create_token(
        user_id="user123",
        tenant_id="tenant_abc",
        scopes=["read", "write"],
    )

    payload = jwt_authenticator.verify_token(token)

    assert payload.sub == "user123"
    assert payload.tenant_id == "tenant_abc"
    assert "read" in payload.scopes
    assert "write" in payload.scopes


def test_verify_expired_token(jwt_authenticator: JWTAuthenticator) -> None:
    """Test verification of expired JWT token."""
    # Create token that expires immediately
    token = jwt_authenticator.create_token(
        user_id="user123",
        tenant_id="tenant_abc",
        scopes=["read"],
        expires_delta=timedelta(seconds=-1),
    )

    # verify_token raises HTTPException, not jwt.ExpiredSignatureError
    with pytest.raises(HTTPException) as exc_info:
        jwt_authenticator.verify_token(token)

    assert exc_info.value.status_code == 401
    assert "Token expired" in exc_info.value.detail


def test_verify_invalid_token(jwt_authenticator: JWTAuthenticator) -> None:
    """Test verification of invalid JWT token."""
    # verify_token raises HTTPException for invalid tokens
    with pytest.raises(HTTPException) as exc_info:
        jwt_authenticator.verify_token("invalid.token.here")

    assert exc_info.value.status_code == 401
    assert "Invalid token" in exc_info.value.detail


def test_verify_token_missing_sub(
    jwt_authenticator: JWTAuthenticator,
) -> None:
    """Test verification of token missing subject."""
    import jwt

    # Create token manually without 'sub'
    payload = {
        "tenant_id": "tenant_abc",
        "scopes": ["read"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }

    token = jwt.encode(
        payload,
        jwt_authenticator.secret_key,
        algorithm=jwt_authenticator.algorithm,
    )

    with pytest.raises(HTTPException) as exc_info:
        jwt_authenticator.verify_token(token)

    assert exc_info.value.status_code == 401


def test_token_with_different_secret(
    jwt_authenticator: JWTAuthenticator,
) -> None:
    """Test token verification with different secret key."""
    token = jwt_authenticator.create_token(
        user_id="user123",
        tenant_id="tenant_abc",
        scopes=["read"],
    )

    # Try to verify with different secret
    wrong_jwt_auth = JWTAuthenticator(
        secret_key="different-secret-key",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        wrong_jwt_auth.verify_token(token)

    assert exc_info.value.status_code == 401


def test_api_key_hash(api_key_authenticator: APIKeyAuthenticator) -> None:
    """Test API key secret hashing."""
    secret = "my-secret-password"
    hashed = api_key_authenticator.hash_secret(secret)

    assert len(hashed) == 64  # SHA256 hex digest
    assert hashed != secret  # Should not be plain text


def test_api_key_hash_consistency(
    api_key_authenticator: APIKeyAuthenticator,
) -> None:
    """Test that hashing same secret produces same result."""
    secret = "my-secret-password"
    hash1 = api_key_authenticator.hash_secret(secret)
    hash2 = api_key_authenticator.hash_secret(secret)

    assert hash1 == hash2


def test_verify_api_key_success(
    api_key_authenticator: APIKeyAuthenticator,
) -> None:
    """Test successful API key verification."""
    api_key_authenticator.api_keys["key123"] = APIKey(
        key_id="key123",
        key_secret=api_key_authenticator.hash_secret("secret123"),
        tenant_id="tenant_abc",
        scopes=["read", "write"],
        created_at=datetime.now(timezone.utc),
        expires_at=None,
        is_active=True,
    )

    result = api_key_authenticator.verify_api_key("key123", "secret123")

    assert result is not None
    assert result.key_id == "key123"
    assert result.tenant_id == "tenant_abc"


def test_verify_api_key_nonexistent(
    api_key_authenticator: APIKeyAuthenticator,
) -> None:
    """Test API key verification with nonexistent key."""
    result = api_key_authenticator.verify_api_key(
        "nonexistent_key",
        "secret",
    )

    assert result is None


def test_verify_api_key_invalid_secret(
    api_key_authenticator: APIKeyAuthenticator,
) -> None:
    """Test API key verification with wrong secret."""
    api_key_authenticator.api_keys["key123"] = APIKey(
        key_id="key123",
        key_secret=api_key_authenticator.hash_secret("secret123"),
        tenant_id="tenant_abc",
        scopes=["read"],
        created_at=datetime.now(timezone.utc),
        expires_at=None,
        is_active=True,
    )

    result = api_key_authenticator.verify_api_key("key123", "wrong_secret")

    assert result is None


def test_verify_api_key_expired(
    api_key_authenticator: APIKeyAuthenticator,
) -> None:
    """Test API key verification when expired."""
    api_key_authenticator.api_keys["key123"] = APIKey(
        key_id="key123",
        key_secret=api_key_authenticator.hash_secret("secret123"),
        tenant_id="tenant_abc",
        scopes=["read"],
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        is_active=True,
    )

    result = api_key_authenticator.verify_api_key("key123", "secret123")

    assert result is None


def test_verify_api_key_inactive(
    api_key_authenticator: APIKeyAuthenticator,
) -> None:
    """Test API key verification when inactive."""
    api_key_authenticator.api_keys["key123"] = APIKey(
        key_id="key123",
        key_secret=api_key_authenticator.hash_secret("secret123"),
        tenant_id="tenant_abc",
        scopes=["read"],
        created_at=datetime.now(timezone.utc),
        expires_at=None,
        is_active=False,
    )

    result = api_key_authenticator.verify_api_key("key123", "secret123")

    assert result is None


def test_global_jwt_auth_instance() -> None:
    """Test that global jwt_auth instance works."""
    token = jwt_auth.create_token(
        user_id="global_user",
        tenant_id="global_tenant",
        scopes=["read"],
    )

    payload = jwt_auth.verify_token(token)

    assert payload.sub == "global_user"
    assert payload.tenant_id == "global_tenant"


def test_token_payload_model() -> None:
    """Test TokenPayload Pydantic model."""
    from src.auth import TokenPayload

    payload = TokenPayload(
        sub="user123",
        tenant_id="tenant_abc",
        scopes=["read", "write"],
        exp=datetime.now(timezone.utc),
        iat=datetime.now(timezone.utc),
    )

    assert payload.sub == "user123"
    assert len(payload.scopes) == 2


def test_verify_token_malformed_payload(jwt_authenticator):
    """Test token with wrong type for sub."""
    import jwt as pyjwt

    payload = {
        "sub": 123,  # Should be string, not int
        "tenant_id": "tenant_abc",
        "scopes": ["read"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }

    token = pyjwt.encode(
        payload,
        jwt_authenticator.secret_key,
        algorithm=jwt_authenticator.algorithm,
    )

    with pytest.raises(HTTPException) as exc_info:
        jwt_authenticator.verify_token(token)
    assert exc_info.value.status_code == 401
