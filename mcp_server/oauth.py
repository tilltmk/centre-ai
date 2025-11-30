"""
OAuth 2.1 Authorization Server for MCP
Implements RFC 7591 (Dynamic Client Registration), RFC 8707 (Resource Indicators)
"""
import secrets
import hashlib
import base64
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode, urlparse, parse_qs
import bcrypt

from .database import db
from .config import config

logger = logging.getLogger("oauth")


class OAuth2Server:
    """OAuth 2.1 Authorization Server with PKCE"""

    TOKEN_EXPIRY = 3600  # 1 hour
    REFRESH_TOKEN_EXPIRY = 86400 * 30  # 30 days
    CODE_EXPIRY = 600  # 10 minutes

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_secret(secret: str) -> str:
        """Hash client secret"""
        return bcrypt.hashpw(secret.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_secret(secret: str, hashed: str) -> bool:
        """Verify client secret"""
        return bcrypt.checkpw(secret.encode(), hashed.encode())

    @staticmethod
    def verify_pkce(code_verifier: str, code_challenge: str, method: str = "S256") -> bool:
        """Verify PKCE code challenge"""
        if method == "S256":
            # SHA256 hash and base64url encode
            hashed = hashlib.sha256(code_verifier.encode()).digest()
            challenge = base64.urlsafe_b64encode(hashed).decode().rstrip("=")
            return challenge == code_challenge
        elif method == "plain":
            return code_verifier == code_challenge
        return False

    @staticmethod
    async def register_client(
        client_name: str,
        redirect_uris: List[str],
        grant_types: List[str] = None,
        is_public: bool = True
    ) -> Dict[str, Any]:
        """
        Dynamic Client Registration (RFC 7591)
        Public clients (like Claude) don't need client_secret with PKCE
        """
        if grant_types is None:
            grant_types = ["authorization_code", "refresh_token"]

        client_id = f"mcp_{secrets.token_urlsafe(16)}"
        client_secret = None
        client_secret_hash = None

        # Confidential clients get a secret
        if not is_public:
            client_secret = secrets.token_urlsafe(32)
            client_secret_hash = OAuth2Server.hash_secret(client_secret)

        async with db.acquire() as conn:
            await conn.execute("""
                INSERT INTO oauth_clients
                (client_id, client_secret_hash, client_name, redirect_uris, grant_types, is_public)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, client_id, client_secret_hash, client_name, redirect_uris, grant_types, is_public)

        result = {
            "client_id": client_id,
            "client_name": client_name,
            "redirect_uris": redirect_uris,
            "grant_types": grant_types,
            "is_public": is_public
        }

        if client_secret:
            result["client_secret"] = client_secret

        return result

    @staticmethod
    async def create_authorization_code(
        client_id: str,
        redirect_uri: str,
        scope: str,
        code_challenge: str,
        code_challenge_method: str,
        resource: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Create authorization code with PKCE"""
        code = OAuth2Server.generate_token(32)
        expires_at = datetime.utcnow() + timedelta(seconds=OAuth2Server.CODE_EXPIRY)

        async with db.acquire() as conn:
            await conn.execute("""
                INSERT INTO oauth_authorization_codes
                (code, client_id, user_id, redirect_uri, scope, code_challenge,
                 code_challenge_method, resource, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, code, client_id, user_id, redirect_uri, scope, code_challenge,
                code_challenge_method, resource, expires_at)

        return code

    @staticmethod
    async def exchange_code(
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str
    ) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token (with PKCE verification)"""
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM oauth_authorization_codes
                WHERE code = $1 AND client_id = $2 AND is_used = false
            """, code, client_id)

            if not row:
                return None

            # Check expiry
            if datetime.utcnow() > row["expires_at"]:
                return None

            # Verify redirect_uri
            if row["redirect_uri"] != redirect_uri:
                return None

            # Verify PKCE (with debug logging for Claude Web compatibility)
            pkce_valid = OAuth2Server.verify_pkce(
                code_verifier,
                row["code_challenge"],
                row["code_challenge_method"]
            )

            if not pkce_valid:
                # Log PKCE failure details for debugging
                logger.error(f"PKCE verification failed:")
                logger.error(f"  Code verifier: {code_verifier}")
                logger.error(f"  Stored challenge: {row['code_challenge']}")
                logger.error(f"  Challenge method: {row['code_challenge_method']}")

                # Generate expected challenge for debugging
                if row["code_challenge_method"] == "S256":
                    expected = base64.urlsafe_b64encode(
                        hashlib.sha256(code_verifier.encode()).digest()
                    ).decode().rstrip("=")
                    logger.error(f"  Expected challenge: {expected}")

                return None

            # Mark code as used
            await conn.execute("""
                UPDATE oauth_authorization_codes SET is_used = true WHERE code = $1
            """, code)

            # Create access token
            access_token = OAuth2Server.generate_token(48)
            token_expires_at = datetime.utcnow() + timedelta(seconds=OAuth2Server.TOKEN_EXPIRY)

            token_id = await conn.fetchval("""
                INSERT INTO oauth_access_tokens
                (access_token, client_id, user_id, scope, resource, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, access_token, client_id, row["user_id"], row["scope"],
                row["resource"], token_expires_at)

            # Create refresh token
            refresh_token = OAuth2Server.generate_token(48)
            refresh_expires_at = datetime.utcnow() + timedelta(seconds=OAuth2Server.REFRESH_TOKEN_EXPIRY)

            await conn.execute("""
                INSERT INTO oauth_refresh_tokens
                (refresh_token, access_token_id, client_id, user_id, scope, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, refresh_token, token_id, client_id, row["user_id"], row["scope"], refresh_expires_at)

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": OAuth2Server.TOKEN_EXPIRY,
            "refresh_token": refresh_token,
            "scope": row["scope"]
        }

    @staticmethod
    async def refresh_access_token(
        refresh_token: str,
        client_id: str,
        scope: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token"""
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM oauth_refresh_tokens
                WHERE refresh_token = $1 AND client_id = $2
            """, refresh_token, client_id)

            if not row:
                return None

            # Check expiry
            if datetime.utcnow() > row["expires_at"]:
                return None

            # Use original scope or requested scope (if narrower)
            token_scope = scope if scope else row["scope"]

            # Create new access token
            access_token = OAuth2Server.generate_token(48)
            token_expires_at = datetime.utcnow() + timedelta(seconds=OAuth2Server.TOKEN_EXPIRY)

            token_id = await conn.fetchval("""
                INSERT INTO oauth_access_tokens
                (access_token, client_id, user_id, scope, expires_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, access_token, client_id, row["user_id"], token_scope, token_expires_at)

            # Update refresh token association
            await conn.execute("""
                UPDATE oauth_refresh_tokens
                SET access_token_id = $1
                WHERE refresh_token = $2
            """, token_id, refresh_token)

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": OAuth2Server.TOKEN_EXPIRY,
            "refresh_token": refresh_token,
            "scope": token_scope
        }

    @staticmethod
    async def verify_access_token(access_token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode access token"""
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM oauth_access_tokens
                WHERE access_token = $1
            """, access_token)

            if not row:
                return None

            # Check expiry
            if datetime.utcnow() > row["expires_at"]:
                return None

            return {
                "client_id": row["client_id"],
                "user_id": row["user_id"],
                "scope": row["scope"],
                "resource": row["resource"]
            }

    @staticmethod
    async def get_client(client_id: str) -> Optional[Dict[str, Any]]:
        """Get OAuth client by ID"""
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM oauth_clients WHERE client_id = $1 AND is_active = true
            """, client_id)

            if not row:
                return None

            return {
                "client_id": row["client_id"],
                "client_name": row["client_name"],
                "redirect_uris": list(row["redirect_uris"]),
                "grant_types": list(row["grant_types"]),
                "scope": row["scope"],
                "is_public": row["is_public"]
            }

    @staticmethod
    async def validate_redirect_uri(client_id: str, redirect_uri: str) -> bool:
        """Validate redirect URI for client"""
        client = await OAuth2Server.get_client(client_id)
        if not client:
            return False
        return redirect_uri in client["redirect_uris"]


def get_authorization_server_metadata(base_url: str) -> Dict[str, Any]:
    """
    OAuth 2.0 Authorization Server Metadata (RFC 8414)
    """
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "registration_endpoint": f"{base_url}/oauth/register",
        "revocation_endpoint": f"{base_url}/oauth/revoke",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "scopes_supported": ["read", "write", "admin"],
        "service_documentation": f"{base_url}/docs"
    }


def get_protected_resource_metadata(base_url: str, auth_server_url: str) -> Dict[str, Any]:
    """
    OAuth 2.0 Protected Resource Metadata (RFC 8707)
    """
    return {
        "resource": base_url,
        "authorization_servers": [auth_server_url],
        "bearer_methods_supported": ["header"],
        "resource_documentation": f"{base_url}/docs",
        "resource_signing_alg_values_supported": []
    }


async def ensure_claude_client_registered():
    """
    Ensure Claude.ai is pre-registered as an OAuth client.
    Called on server startup.
    """
    from .config import config

    client_id = config.security.claude_oauth_client_id
    client_secret = config.security.claude_oauth_client_secret

    try:
        existing = await OAuth2Server.get_client(client_id)
        if existing:
            logger.info(f"Claude OAuth client already registered: {client_id}")
            return

        async with db.acquire() as conn:
            client_secret_hash = OAuth2Server.hash_secret(client_secret)

            await conn.execute("""
                INSERT INTO oauth_clients
                (client_id, client_secret_hash, client_name, redirect_uris, grant_types, is_public, scope)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (client_id) DO UPDATE SET
                    client_secret_hash = $2,
                    redirect_uris = $4
            """,
                client_id,
                client_secret_hash,
                "Claude",
                [
                    "https://claude.ai/api/mcp/auth_callback",
                    "https://claude.com/api/mcp/auth_callback"
                ],
                ["authorization_code", "refresh_token"],
                True,
                "read write"
            )

            logger.info(f"Claude OAuth client registered: {client_id}")

    except Exception as e:
        logger.error(f"Failed to register Claude OAuth client: {e}")
