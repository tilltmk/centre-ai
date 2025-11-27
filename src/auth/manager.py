"""
Authentication Manager
Supports multiple authentication methods for maximum compatibility
"""

import os
import jwt
import bcrypt
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages multiple authentication methods"""

    def __init__(self):
        self.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
        self.api_keys = self._load_api_keys()
        self.jwt_algorithm = 'HS256'
        self.jwt_expiry_hours = 24

    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment"""
        api_keys = {}

        # Single API key from env
        api_key = os.getenv('API_KEY')
        if api_key:
            api_keys['default'] = api_key

        # Multiple API keys from env
        for i in range(1, 11):  # Support up to 10 API keys
            key = os.getenv(f'API_KEY_{i}')
            if key:
                api_keys[f'key_{i}'] = key

        if not api_keys:
            # Generate a default API key for development
            default_key = 'dev-api-key-12345'
            api_keys['default'] = default_key
            logger.warning(f"No API keys configured. Using default: {default_key}")

        logger.info(f"Loaded {len(api_keys)} API keys")
        return api_keys

    def authenticate(self, request) -> Dict[str, Any]:
        """
        Authenticate request using multiple methods
        Checks in order: Bearer Token -> API Key -> Basic Auth
        """

        # 1. Try Bearer Token (JWT)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            result = self._verify_jwt(token)
            if result['authenticated']:
                return result

        # 2. Try API Key (X-API-Key header)
        api_key = request.headers.get('X-API-Key', '')
        if api_key:
            result = self._verify_api_key(api_key)
            if result['authenticated']:
                return result

        # 3. Try Basic Auth
        if auth_header.startswith('Basic '):
            encoded = auth_header[6:]
            result = self._verify_basic_auth(encoded)
            if result['authenticated']:
                return result

        # 4. Try API Key in query parameter (for compatibility)
        api_key = request.args.get('api_key', '')
        if api_key:
            result = self._verify_api_key(api_key)
            if result['authenticated']:
                return result

        return {
            'authenticated': False,
            'message': 'No valid authentication provided'
        }

    def _verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """Verify API key"""
        for key_name, stored_key in self.api_keys.items():
            if api_key == stored_key:
                logger.info(f"API key authenticated: {key_name}")
                return {
                    'authenticated': True,
                    'method': 'api_key',
                    'user': key_name
                }

        return {
            'authenticated': False,
            'message': 'Invalid API key'
        }

    def _verify_jwt(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])

            # Check expiration
            exp = payload.get('exp')
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                return {
                    'authenticated': False,
                    'message': 'Token expired'
                }

            user = payload.get('user', 'unknown')
            logger.info(f"JWT authenticated: {user}")

            return {
                'authenticated': True,
                'method': 'jwt',
                'user': user,
                'payload': payload
            }

        except jwt.InvalidTokenError as e:
            return {
                'authenticated': False,
                'message': f'Invalid token: {str(e)}'
            }

    def _verify_basic_auth(self, encoded: str) -> Dict[str, Any]:
        """Verify Basic Authentication"""
        try:
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)

            # Check against configured users (simplified)
            # In production, use proper user database
            env_username = os.getenv('BASIC_AUTH_USERNAME', 'admin')
            env_password = os.getenv('BASIC_AUTH_PASSWORD', 'admin')

            if username == env_username and password == env_password:
                logger.info(f"Basic auth authenticated: {username}")
                return {
                    'authenticated': True,
                    'method': 'basic_auth',
                    'user': username
                }

            return {
                'authenticated': False,
                'message': 'Invalid username or password'
            }

        except Exception as e:
            return {
                'authenticated': False,
                'message': f'Invalid basic auth: {str(e)}'
            }

    def generate_jwt(self, user: str, additional_claims: Dict[str, Any] = None) -> str:
        """Generate JWT token"""
        payload = {
            'user': user,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiry_hours)
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.jwt_algorithm)
        return token

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
