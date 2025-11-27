"""
OAuth 2.1 HTTP Endpoints for MCP Server
Implements authorization, token, and registration endpoints
"""
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode, urlparse, parse_qs

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, HTMLResponse
from starlette.exceptions import HTTPException

from .oauth import OAuth2Server, get_authorization_server_metadata, get_protected_resource_metadata
from .config import config
import logging

logger = logging.getLogger("oauth-routes")


async def oauth_metadata(request: Request) -> JSONResponse:
    """
    OAuth 2.0 Authorization Server Metadata (RFC 8414)
    /.well-known/oauth-authorization-server
    """
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    metadata = get_authorization_server_metadata(base_url)
    return JSONResponse(metadata)


async def protected_resource_metadata(request: Request) -> JSONResponse:
    """
    OAuth 2.0 Protected Resource Metadata (RFC 8707)
    /.well-known/oauth-protected-resource
    """
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    auth_server_url = base_url  # Same server acts as both
    metadata = get_protected_resource_metadata(base_url, auth_server_url)
    return JSONResponse(metadata)


async def oauth_register(request: Request) -> JSONResponse:
    """
    Dynamic Client Registration Endpoint (RFC 7591)
    POST /oauth/register
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {"error": "invalid_request", "error_description": "Invalid JSON body"},
            status_code=400
        )

    # Required fields
    client_name = body.get("client_name")
    redirect_uris = body.get("redirect_uris", [])

    if not client_name:
        return JSONResponse(
            {"error": "invalid_client_metadata", "error_description": "client_name is required"},
            status_code=400
        )

    if not redirect_uris or not isinstance(redirect_uris, list):
        return JSONResponse(
            {"error": "invalid_redirect_uri", "error_description": "redirect_uris must be a non-empty array"},
            status_code=400
        )

    # Optional fields
    grant_types = body.get("grant_types", ["authorization_code", "refresh_token"])
    is_public = body.get("token_endpoint_auth_method") == "none"

    try:
        client_info = await OAuth2Server.register_client(
            client_name=client_name,
            redirect_uris=redirect_uris,
            grant_types=grant_types,
            is_public=is_public
        )

        response_data = {
            "client_id": client_info["client_id"],
            "client_name": client_info["client_name"],
            "redirect_uris": client_info["redirect_uris"],
            "grant_types": client_info["grant_types"],
            "token_endpoint_auth_method": "none" if is_public else "client_secret_post"
        }

        if not is_public:
            response_data["client_secret"] = client_info["client_secret"]

        return JSONResponse(response_data, status_code=201)

    except Exception as e:
        logger.error(f"Client registration error: {e}")
        return JSONResponse(
            {"error": "server_error", "error_description": str(e)},
            status_code=500
        )


async def oauth_authorize(request: Request) -> HTMLResponse:
    """
    Authorization Endpoint
    GET /oauth/authorize

    Params:
    - response_type: must be "code"
    - client_id: registered client ID
    - redirect_uri: must match registered URI
    - scope: requested scopes (space-separated)
    - state: CSRF protection
    - code_challenge: PKCE challenge (required)
    - code_challenge_method: S256 or plain (default: S256)
    - resource: Resource Indicator (RFC 8707)
    """
    # Parse query parameters
    response_type = request.query_params.get("response_type")
    client_id = request.query_params.get("client_id")
    redirect_uri = request.query_params.get("redirect_uri")
    scope = request.query_params.get("scope", "read write")
    state = request.query_params.get("state", "")
    code_challenge = request.query_params.get("code_challenge")
    code_challenge_method = request.query_params.get("code_challenge_method", "S256")
    resource = request.query_params.get("resource")

    # Validation
    if response_type != "code":
        return _error_redirect(redirect_uri, "unsupported_response_type", state)

    if not client_id:
        return JSONResponse(
            {"error": "invalid_request", "error_description": "client_id is required"},
            status_code=400
        )

    if not redirect_uri:
        return JSONResponse(
            {"error": "invalid_request", "error_description": "redirect_uri is required"},
            status_code=400
        )

    # PKCE is mandatory in OAuth 2.1
    if not code_challenge:
        return _error_redirect(redirect_uri, "invalid_request", state, "code_challenge is required")

    # Verify client exists and redirect_uri matches
    client = await OAuth2Server.get_client(client_id)
    if not client:
        return _error_redirect(redirect_uri, "invalid_client", state)

    if not await OAuth2Server.validate_redirect_uri(client_id, redirect_uri):
        return JSONResponse(
            {"error": "invalid_request", "error_description": "redirect_uri does not match registered URIs"},
            status_code=400
        )

    # In production, show consent screen here
    # For now, auto-approve (simplified for MCP use case)

    # Create authorization code
    try:
        code = await OAuth2Server.create_authorization_code(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            resource=resource,
            user_id="mcp_user"  # Simplified - in production get from session
        )

        # Redirect back with code
        params = {"code": code}
        if state:
            params["state"] = state

        redirect_url = f"{redirect_uri}?{urlencode(params)}"
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        logger.error(f"Authorization error: {e}")
        return _error_redirect(redirect_uri, "server_error", state)


async def oauth_token(request: Request) -> JSONResponse:
    """
    Token Endpoint
    POST /oauth/token

    Grant Types:
    - authorization_code: Exchange code for tokens
    - refresh_token: Refresh access token
    """
    try:
        # Parse form data
        form = await request.form()
        grant_type = form.get("grant_type")
        client_id = form.get("client_id")

        if not grant_type or not client_id:
            return JSONResponse(
                {"error": "invalid_request", "error_description": "grant_type and client_id are required"},
                status_code=400
            )

        # Verify client
        client = await OAuth2Server.get_client(client_id)
        if not client:
            return JSONResponse(
                {"error": "invalid_client", "error_description": "Client not found"},
                status_code=401
            )

        # Handle authorization_code grant
        if grant_type == "authorization_code":
            code = form.get("code")
            redirect_uri = form.get("redirect_uri")
            code_verifier = form.get("code_verifier")

            if not code or not redirect_uri or not code_verifier:
                return JSONResponse(
                    {"error": "invalid_request", "error_description": "code, redirect_uri, and code_verifier are required"},
                    status_code=400
                )

            token_response = await OAuth2Server.exchange_code(
                code=code,
                client_id=client_id,
                redirect_uri=redirect_uri,
                code_verifier=code_verifier
            )

            if not token_response:
                return JSONResponse(
                    {"error": "invalid_grant", "error_description": "Invalid authorization code or PKCE verification failed"},
                    status_code=400
                )

            return JSONResponse(token_response)

        # Handle refresh_token grant
        elif grant_type == "refresh_token":
            refresh_token = form.get("refresh_token")
            scope = form.get("scope")

            if not refresh_token:
                return JSONResponse(
                    {"error": "invalid_request", "error_description": "refresh_token is required"},
                    status_code=400
                )

            token_response = await OAuth2Server.refresh_access_token(
                refresh_token=refresh_token,
                client_id=client_id,
                scope=scope
            )

            if not token_response:
                return JSONResponse(
                    {"error": "invalid_grant", "error_description": "Invalid refresh token"},
                    status_code=400
                )

            return JSONResponse(token_response)

        else:
            return JSONResponse(
                {"error": "unsupported_grant_type", "error_description": f"Grant type '{grant_type}' is not supported"},
                status_code=400
            )

    except Exception as e:
        logger.error(f"Token endpoint error: {e}")
        return JSONResponse(
            {"error": "server_error", "error_description": str(e)},
            status_code=500
        )


async def oauth_revoke(request: Request) -> JSONResponse:
    """
    Token Revocation Endpoint (RFC 7009)
    POST /oauth/revoke
    """
    try:
        form = await request.form()
        token = form.get("token")
        token_type_hint = form.get("token_type_hint")  # access_token or refresh_token

        if not token:
            return JSONResponse(
                {"error": "invalid_request", "error_description": "token is required"},
                status_code=400
            )

        # For now, simple implementation - just respond OK
        # In production, actually revoke the token in database
        return JSONResponse({"status": "revoked"}, status_code=200)

    except Exception as e:
        logger.error(f"Token revocation error: {e}")
        return JSONResponse(
            {"error": "server_error", "error_description": str(e)},
            status_code=500
        )


def _error_redirect(redirect_uri: str, error: str, state: str = "", error_description: str = "") -> RedirectResponse:
    """Helper to redirect with error parameters"""
    params = {"error": error}
    if state:
        params["state"] = state
    if error_description:
        params["error_description"] = error_description

    redirect_url = f"{redirect_uri}?{urlencode(params)}"
    return RedirectResponse(url=redirect_url)
