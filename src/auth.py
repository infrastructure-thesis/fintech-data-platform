"""API Authentication and Authorization."""
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Callable, Awaitable, cast

from fastapi import HTTPException, Depends, Header
from pydantic import BaseModel

from src.utils.logging import get_logger

logger = get_logger(__name__)

SECRET_KEY = (  # nosec B105
    "your-secret-key-from-secrets-manager-" "minimum-32-bytes-required-for-sha256"
)
ALGORITHM = "HS256"
TOKEN_EXPIRY_MINUTES = 60


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str
    tenant_id: str
    scopes: list[str]
    exp: datetime
    iat: datetime


class AuthCredentials(BaseModel):
    """API credentials for authentication."""

    api_key: str
    api_secret: str


class APIKey(BaseModel):
    """API key stored in database."""

    key_id: str
    key_secret: str
    tenant_id: str
    scopes: list[str]
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool


class JWTAuthenticator:
    """JWT-based authentication."""

    def __init__(
        self,
        secret_key: str = SECRET_KEY,
        algorithm: str = ALGORITHM,
    ) -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(
        self,
        user_id: str,
        tenant_id: str,
        scopes: list[str],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create JWT token."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=TOKEN_EXPIRY_MINUTES
            )

        payload: Dict[str, Any] = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "scopes": scopes,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        encoded_jwt: str = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )
        return encoded_jwt

    def verify_token(self, token: str) -> TokenPayload:
        """Verify JWT token."""
        try:
            payload: Dict[str, Any] = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            user_id: str = cast(str, payload.get("sub"))
            tenant_id: str = cast(str, payload.get("tenant_id"))
            scopes: list[str] = cast(list[str], payload.get("scopes", []))

            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")

            exp_ts: float = cast(float, payload.get("exp"))
            iat_ts: float = cast(float, payload.get("iat"))

            return TokenPayload(
                sub=user_id,
                tenant_id=tenant_id,
                scopes=scopes,
                exp=datetime.fromtimestamp(exp_ts, tz=timezone.utc),
                iat=datetime.fromtimestamp(iat_ts, tz=timezone.utc),
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")


class APIKeyAuthenticator:
    """API Key-based authentication."""

    def __init__(self) -> None:
        self.api_keys: Dict[str, APIKey] = {}

    def hash_secret(self, secret: str) -> str:
        """Hash API secret."""
        import hashlib

        return hashlib.sha256(secret.encode()).hexdigest()

    def verify_api_key(self, key_id: str, key_secret: str) -> Optional[APIKey]:
        """Verify API key and secret."""
        if key_id not in self.api_keys:
            logger.warning("api_key_not_found", key_id=key_id)
            return None

        api_key = self.api_keys[key_id]

        if not api_key.is_active:
            logger.warning("api_key_inactive", key_id=key_id)
            return None

        if api_key.expires_at and datetime.now(timezone.utc) > api_key.expires_at:
            logger.warning("api_key_expired", key_id=key_id)
            return None

        if self.hash_secret(key_secret) != api_key.key_secret:
            logger.warning("api_key_invalid_secret", key_id=key_id)
            return None

        return api_key


jwt_auth = JWTAuthenticator()
api_key_auth = APIKeyAuthenticator()


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> TokenPayload:
    """Extract and verify JWT token from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header",
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization scheme",
            )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format",
        )

    return jwt_auth.verify_token(token)


async def get_api_key(
    x_api_key: Optional[str] = Header(None),
    x_api_secret: Optional[str] = Header(None),
) -> APIKey:
    """Extract and verify API key."""
    if not x_api_key or not x_api_secret:
        raise HTTPException(
            status_code=401,
            detail="Missing API credentials",
        )

    api_key = api_key_auth.verify_api_key(x_api_key, x_api_secret)
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API credentials",
        )

    return api_key


def require_scope(
    required_scope: str,
) -> Callable[..., Awaitable[TokenPayload]]:
    """Decorator to require specific scope."""

    async def scope_checker(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        if required_scope not in current_user.scopes:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required scope: {required_scope}",
            )
        return current_user

    return scope_checker


def require_tenant(
    required_tenant: str,
) -> Callable[..., Awaitable[TokenPayload]]:
    """Decorator to require specific tenant."""

    async def tenant_checker(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        if current_user.tenant_id != required_tenant:
            raise HTTPException(
                status_code=403,
                detail="Tenant mismatch",
            )
        return current_user

    return tenant_checker
