"""
Tests for AuthManager module
"""

import pytest
import os
import jwt
import base64
from datetime import datetime, timedelta
from src.auth.manager import AuthManager


class TestAuthManager:
    """Test suite for AuthManager"""

    @pytest.fixture
    def auth_manager(self, monkeypatch):
        """Create AuthManager with test environment"""
        monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
        monkeypatch.setenv('API_KEY', 'test-api-key-123')
        monkeypatch.setenv('BASIC_AUTH_USERNAME', 'testuser')
        monkeypatch.setenv('BASIC_AUTH_PASSWORD', 'testpass')
        return AuthManager()

    @pytest.fixture
    def mock_request(self):
        """Create mock request object"""
        class MockRequest:
            def __init__(self):
                self.headers = {}
                self.args = {}
        return MockRequest()

    def test_init_loads_api_keys(self, auth_manager):
        """Test that API keys are loaded on init"""
        assert len(auth_manager.api_keys) > 0
        assert 'default' in auth_manager.api_keys
        assert auth_manager.api_keys['default'] == 'test-api-key-123'

    def test_init_secret_key(self, auth_manager):
        """Test secret key is loaded"""
        assert auth_manager.secret_key == 'test-secret-key'

    def test_verify_api_key_valid(self, auth_manager):
        """Test valid API key verification"""
        result = auth_manager._verify_api_key('test-api-key-123')
        assert result['authenticated'] is True
        assert result['method'] == 'api_key'
        assert result['user'] == 'default'

    def test_verify_api_key_invalid(self, auth_manager):
        """Test invalid API key verification"""
        result = auth_manager._verify_api_key('wrong-key')
        assert result['authenticated'] is False
        assert 'Invalid' in result['message']

    def test_verify_api_key_empty(self, auth_manager):
        """Test empty API key"""
        result = auth_manager._verify_api_key('')
        assert result['authenticated'] is False

    def test_generate_jwt_basic(self, auth_manager):
        """Test basic JWT generation"""
        token = auth_manager.generate_jwt('testuser')
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=['HS256'])
        assert payload['user'] == 'testuser'
        assert 'iat' in payload
        assert 'exp' in payload

    def test_generate_jwt_with_claims(self, auth_manager):
        """Test JWT with additional claims"""
        token = auth_manager.generate_jwt('testuser', {'role': 'admin', 'scope': 'full'})
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=['HS256'])
        assert payload['user'] == 'testuser'
        assert payload['role'] == 'admin'
        assert payload['scope'] == 'full'

    def test_verify_jwt_valid(self, auth_manager):
        """Test valid JWT verification"""
        token = auth_manager.generate_jwt('testuser')
        result = auth_manager._verify_jwt(token)
        assert result['authenticated'] is True
        assert result['method'] == 'jwt'
        assert result['user'] == 'testuser'

    def test_verify_jwt_invalid(self, auth_manager):
        """Test invalid JWT verification"""
        result = auth_manager._verify_jwt('invalid.jwt.token')
        assert result['authenticated'] is False
        assert 'Invalid' in result['message']

    def test_verify_jwt_expired(self, auth_manager):
        """Test expired JWT"""
        # Create token that's already expired
        payload = {
            'user': 'testuser',
            'iat': datetime.utcnow() - timedelta(hours=48),
            'exp': datetime.utcnow() - timedelta(hours=24)
        }
        token = jwt.encode(payload, auth_manager.secret_key, algorithm='HS256')

        result = auth_manager._verify_jwt(token)
        assert result['authenticated'] is False
        assert 'expired' in result['message'].lower()

    def test_verify_jwt_wrong_secret(self, auth_manager):
        """Test JWT with wrong secret"""
        token = jwt.encode({'user': 'test'}, 'wrong-secret', algorithm='HS256')
        result = auth_manager._verify_jwt(token)
        assert result['authenticated'] is False

    def test_verify_basic_auth_valid(self, auth_manager):
        """Test valid basic auth"""
        credentials = base64.b64encode(b'testuser:testpass').decode('utf-8')
        result = auth_manager._verify_basic_auth(credentials)
        assert result['authenticated'] is True
        assert result['method'] == 'basic_auth'
        assert result['user'] == 'testuser'

    def test_verify_basic_auth_invalid_password(self, auth_manager):
        """Test invalid password"""
        credentials = base64.b64encode(b'testuser:wrongpass').decode('utf-8')
        result = auth_manager._verify_basic_auth(credentials)
        assert result['authenticated'] is False
        assert 'Invalid' in result['message']

    def test_verify_basic_auth_invalid_username(self, auth_manager):
        """Test invalid username"""
        credentials = base64.b64encode(b'wronguser:testpass').decode('utf-8')
        result = auth_manager._verify_basic_auth(credentials)
        assert result['authenticated'] is False

    def test_verify_basic_auth_malformed(self, auth_manager):
        """Test malformed basic auth"""
        credentials = base64.b64encode(b'no-colon-here').decode('utf-8')
        result = auth_manager._verify_basic_auth(credentials)
        assert result['authenticated'] is False

    def test_verify_basic_auth_invalid_encoding(self, auth_manager):
        """Test invalid base64 encoding"""
        result = auth_manager._verify_basic_auth('not-valid-base64!')
        assert result['authenticated'] is False

    def test_authenticate_with_bearer_token(self, auth_manager, mock_request):
        """Test authentication with Bearer token"""
        token = auth_manager.generate_jwt('testuser')
        mock_request.headers['Authorization'] = f'Bearer {token}'

        result = auth_manager.authenticate(mock_request)
        assert result['authenticated'] is True
        assert result['method'] == 'jwt'

    def test_authenticate_with_api_key_header(self, auth_manager, mock_request):
        """Test authentication with X-API-Key header"""
        mock_request.headers['X-API-Key'] = 'test-api-key-123'

        result = auth_manager.authenticate(mock_request)
        assert result['authenticated'] is True
        assert result['method'] == 'api_key'

    def test_authenticate_with_basic_auth(self, auth_manager, mock_request):
        """Test authentication with Basic Auth"""
        credentials = base64.b64encode(b'testuser:testpass').decode('utf-8')
        mock_request.headers['Authorization'] = f'Basic {credentials}'

        result = auth_manager.authenticate(mock_request)
        assert result['authenticated'] is True
        assert result['method'] == 'basic_auth'

    def test_authenticate_with_api_key_query(self, auth_manager, mock_request):
        """Test authentication with API key in query parameter"""
        mock_request.args['api_key'] = 'test-api-key-123'

        result = auth_manager.authenticate(mock_request)
        assert result['authenticated'] is True
        assert result['method'] == 'api_key'

    def test_authenticate_no_auth(self, auth_manager, mock_request):
        """Test authentication with no credentials"""
        result = auth_manager.authenticate(mock_request)
        assert result['authenticated'] is False
        assert 'No valid' in result['message']

    def test_authenticate_invalid_bearer(self, auth_manager, mock_request):
        """Test with invalid bearer token falls through to other methods"""
        mock_request.headers['Authorization'] = 'Bearer invalid-token'
        mock_request.headers['X-API-Key'] = 'test-api-key-123'

        # Should fall through to API key
        result = auth_manager.authenticate(mock_request)
        assert result['authenticated'] is True
        assert result['method'] == 'api_key'

    def test_authenticate_priority_order(self, auth_manager, mock_request):
        """Test authentication priority: Bearer > API Key > Basic"""
        token = auth_manager.generate_jwt('jwtuser')
        mock_request.headers['Authorization'] = f'Bearer {token}'
        mock_request.headers['X-API-Key'] = 'test-api-key-123'

        result = auth_manager.authenticate(mock_request)
        assert result['method'] == 'jwt'  # Bearer takes priority

    def test_hash_password(self, auth_manager):
        """Test password hashing"""
        password = 'test-password-123'
        hashed = auth_manager.hash_password(password)
        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 20

    def test_hash_password_different_each_time(self, auth_manager):
        """Test that hashing same password gives different results (salt)"""
        password = 'test-password'
        hash1 = auth_manager.hash_password(password)
        hash2 = auth_manager.hash_password(password)
        assert hash1 != hash2  # Different salts

    def test_verify_password_correct(self, auth_manager):
        """Test correct password verification"""
        password = 'my-secure-password'
        hashed = auth_manager.hash_password(password)
        assert auth_manager.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, auth_manager):
        """Test incorrect password verification"""
        password = 'my-secure-password'
        hashed = auth_manager.hash_password(password)
        assert auth_manager.verify_password('wrong-password', hashed) is False

    def test_verify_password_empty(self, auth_manager):
        """Test empty password"""
        hashed = auth_manager.hash_password('password')
        assert auth_manager.verify_password('', hashed) is False

    def test_multiple_api_keys(self, monkeypatch):
        """Test loading multiple API keys"""
        monkeypatch.setenv('API_KEY', 'default-key')
        monkeypatch.setenv('API_KEY_1', 'key-one')
        monkeypatch.setenv('API_KEY_2', 'key-two')

        auth = AuthManager()
        assert auth.api_keys['default'] == 'default-key'
        assert auth.api_keys['key_1'] == 'key-one'
        assert auth.api_keys['key_2'] == 'key-two'

    def test_default_api_key_when_none_configured(self, monkeypatch):
        """Test default API key generation when none configured"""
        # Clear all API key env vars
        monkeypatch.delenv('API_KEY', raising=False)
        for i in range(1, 11):
            monkeypatch.delenv(f'API_KEY_{i}', raising=False)

        auth = AuthManager()
        assert 'default' in auth.api_keys
        assert auth.api_keys['default'] == 'dev-api-key-12345'
