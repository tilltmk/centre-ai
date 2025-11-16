"""
Tests for DataTools module
"""

import pytest
import json
import hashlib
import base64
from src.tools.data_tools import DataTools


class TestDataTools:
    """Test suite for DataTools"""

    @pytest.fixture
    def tools(self):
        """Create DataTools instance"""
        return DataTools()

    def test_get_tools_returns_list(self, tools):
        """Test that get_tools returns a list of tools"""
        tool_list = tools.get_tools()
        assert isinstance(tool_list, list)
        assert len(tool_list) == 8

    def test_get_tools_have_required_fields(self, tools):
        """Test that all tools have required fields"""
        tool_list = tools.get_tools()
        for tool in tool_list:
            assert 'name' in tool
            assert 'description' in tool
            assert 'parameters' in tool
            assert 'handler' in tool
            assert callable(tool['handler'])

    # json_format tests
    def test_json_format_basic(self, tools):
        """Test basic JSON formatting"""
        result = tools.json_format({'json_string': '{"name":"test","value":123}'})
        assert result['success'] is True
        parsed = json.loads(result['result'])
        assert parsed['name'] == 'test'
        assert parsed['value'] == 123
        assert '\n' in result['result']  # Pretty printed

    def test_json_format_array(self, tools):
        """Test JSON array formatting"""
        result = tools.json_format({'json_string': '[1,2,3]'})
        assert result['success'] is True
        parsed = json.loads(result['result'])
        assert parsed == [1, 2, 3]

    def test_json_format_nested(self, tools):
        """Test nested JSON formatting"""
        result = tools.json_format({'json_string': '{"a":{"b":{"c":1}}}'})
        assert result['success'] is True
        parsed = json.loads(result['result'])
        assert parsed['a']['b']['c'] == 1

    def test_json_format_invalid(self, tools):
        """Test invalid JSON"""
        result = tools.json_format({'json_string': '{invalid json}'})
        assert result['success'] is False
        assert 'error' in result

    def test_json_format_empty_object(self, tools):
        """Test empty JSON object"""
        result = tools.json_format({'json_string': '{}'})
        assert result['success'] is True

    def test_json_format_unicode(self, tools):
        """Test JSON with unicode"""
        result = tools.json_format({'json_string': '{"text":"こんにちは"}'})
        assert result['success'] is True
        assert 'こんにちは' in result['result']

    # json_validate tests
    def test_json_validate_valid(self, tools):
        """Test valid JSON validation"""
        result = tools.json_validate({'json_string': '{"name":"test"}'})
        assert result['valid'] is True
        assert result['message'] == 'Valid JSON'

    def test_json_validate_invalid(self, tools):
        """Test invalid JSON validation"""
        result = tools.json_validate({'json_string': '{invalid}'})
        assert result['valid'] is False
        assert 'error' in result

    def test_json_validate_array(self, tools):
        """Test array JSON validation"""
        result = tools.json_validate({'json_string': '[1, 2, 3]'})
        assert result['valid'] is True

    def test_json_validate_empty(self, tools):
        """Test empty string validation"""
        result = tools.json_validate({'json_string': ''})
        assert result['valid'] is False

    # calculate tests
    def test_calculate_addition(self, tools):
        """Test addition"""
        result = tools.calculate({'expression': '2 + 3'})
        assert result['success'] is True
        assert result['result'] == 5

    def test_calculate_subtraction(self, tools):
        """Test subtraction"""
        result = tools.calculate({'expression': '10 - 3'})
        assert result['success'] is True
        assert result['result'] == 7

    def test_calculate_multiplication(self, tools):
        """Test multiplication"""
        result = tools.calculate({'expression': '4 * 5'})
        assert result['success'] is True
        assert result['result'] == 20

    def test_calculate_division(self, tools):
        """Test division"""
        result = tools.calculate({'expression': '20 / 4'})
        assert result['success'] is True
        assert result['result'] == 5.0

    def test_calculate_complex(self, tools):
        """Test complex expression"""
        result = tools.calculate({'expression': '(2 + 3) * 4 - 10 / 2'})
        assert result['success'] is True
        assert result['result'] == 15.0

    def test_calculate_float(self, tools):
        """Test float calculations"""
        result = tools.calculate({'expression': '3.14 * 2'})
        assert result['success'] is True
        assert abs(result['result'] - 6.28) < 0.001

    def test_calculate_modulo(self, tools):
        """Test modulo operation"""
        result = tools.calculate({'expression': '10 % 3'})
        assert result['success'] is True
        assert result['result'] == 1

    def test_calculate_invalid_chars(self, tools):
        """Test invalid characters are rejected"""
        result = tools.calculate({'expression': 'import os'})
        assert result['success'] is False
        assert 'Invalid characters' in result['error']

    def test_calculate_division_by_zero(self, tools):
        """Test division by zero"""
        result = tools.calculate({'expression': '1 / 0'})
        assert result['success'] is False

    # hash_text tests
    def test_hash_text_sha256_default(self, tools):
        """Test default SHA256 hashing"""
        result = tools.hash_text({'text': 'test'})
        assert result['success'] is True
        assert result['algorithm'] == 'sha256'
        expected = hashlib.sha256('test'.encode()).hexdigest()
        assert result['hash'] == expected

    def test_hash_text_md5(self, tools):
        """Test MD5 hashing"""
        result = tools.hash_text({'text': 'test', 'algorithm': 'md5'})
        assert result['success'] is True
        assert result['algorithm'] == 'md5'
        expected = hashlib.md5('test'.encode()).hexdigest()
        assert result['hash'] == expected

    def test_hash_text_sha1(self, tools):
        """Test SHA1 hashing"""
        result = tools.hash_text({'text': 'test', 'algorithm': 'sha1'})
        assert result['success'] is True
        assert result['algorithm'] == 'sha1'
        expected = hashlib.sha1('test'.encode()).hexdigest()
        assert result['hash'] == expected

    def test_hash_text_invalid_algorithm(self, tools):
        """Test invalid algorithm"""
        result = tools.hash_text({'text': 'test', 'algorithm': 'invalid'})
        assert result['success'] is False
        assert 'Unsupported algorithm' in result['error']

    def test_hash_text_empty(self, tools):
        """Test empty text hashing"""
        result = tools.hash_text({'text': ''})
        assert result['success'] is True
        assert len(result['hash']) == 64  # SHA256 hex length

    # base64_encode tests
    def test_base64_encode_basic(self, tools):
        """Test basic base64 encoding"""
        result = tools.base64_encode({'text': 'hello'})
        assert result['success'] is True
        assert result['encoded'] == base64.b64encode('hello'.encode()).decode()

    def test_base64_encode_empty(self, tools):
        """Test empty text encoding"""
        result = tools.base64_encode({'text': ''})
        assert result['success'] is True
        assert result['encoded'] == ''

    def test_base64_encode_special_chars(self, tools):
        """Test encoding with special characters"""
        result = tools.base64_encode({'text': 'Hello!@#$%'})
        assert result['success'] is True
        decoded = base64.b64decode(result['encoded']).decode()
        assert decoded == 'Hello!@#$%'

    def test_base64_encode_unicode(self, tools):
        """Test unicode encoding"""
        result = tools.base64_encode({'text': 'こんにちは'})
        assert result['success'] is True
        decoded = base64.b64decode(result['encoded']).decode()
        assert decoded == 'こんにちは'

    # base64_decode tests
    def test_base64_decode_basic(self, tools):
        """Test basic base64 decoding"""
        encoded = base64.b64encode('hello'.encode()).decode()
        result = tools.base64_decode({'encoded': encoded})
        assert result['success'] is True
        assert result['decoded'] == 'hello'

    def test_base64_decode_empty(self, tools):
        """Test empty base64 decoding"""
        result = tools.base64_decode({'encoded': ''})
        assert result['success'] is True
        assert result['decoded'] == ''

    def test_base64_decode_invalid(self, tools):
        """Test invalid base64 decoding"""
        result = tools.base64_decode({'encoded': 'not-valid-base64!'})
        assert result['success'] is False

    def test_base64_roundtrip(self, tools):
        """Test encode/decode roundtrip"""
        original = 'Test message with 123 and !@#'
        encoded = tools.base64_encode({'text': original})
        decoded = tools.base64_decode({'encoded': encoded['encoded']})
        assert decoded['decoded'] == original

    # list_sort tests
    def test_list_sort_numbers(self, tools):
        """Test sorting numbers"""
        result = tools.list_sort({'items': [3, 1, 4, 1, 5, 9]})
        assert result['success'] is True
        assert result['result'] == [1, 1, 3, 4, 5, 9]
        assert result['count'] == 6

    def test_list_sort_strings(self, tools):
        """Test sorting strings"""
        result = tools.list_sort({'items': ['c', 'a', 'b']})
        assert result['success'] is True
        assert result['result'] == ['a', 'b', 'c']

    def test_list_sort_reverse(self, tools):
        """Test reverse sorting"""
        result = tools.list_sort({'items': [1, 2, 3], 'reverse': True})
        assert result['success'] is True
        assert result['result'] == [3, 2, 1]

    def test_list_sort_empty(self, tools):
        """Test sorting empty list"""
        result = tools.list_sort({'items': []})
        assert result['success'] is True
        assert result['result'] == []
        assert result['count'] == 0

    def test_list_sort_already_sorted(self, tools):
        """Test already sorted list"""
        result = tools.list_sort({'items': [1, 2, 3, 4]})
        assert result['success'] is True
        assert result['result'] == [1, 2, 3, 4]

    # list_unique tests
    def test_list_unique_basic(self, tools):
        """Test basic unique filtering"""
        result = tools.list_unique({'items': [1, 2, 2, 3, 3, 3]})
        assert result['success'] is True
        assert result['result'] == [1, 2, 3]
        assert result['original_count'] == 6
        assert result['unique_count'] == 3
        assert result['duplicates_removed'] == 3

    def test_list_unique_strings(self, tools):
        """Test unique strings"""
        result = tools.list_unique({'items': ['a', 'b', 'a', 'c', 'b']})
        assert result['success'] is True
        assert result['result'] == ['a', 'b', 'c']

    def test_list_unique_no_duplicates(self, tools):
        """Test list with no duplicates"""
        result = tools.list_unique({'items': [1, 2, 3]})
        assert result['success'] is True
        assert result['result'] == [1, 2, 3]
        assert result['duplicates_removed'] == 0

    def test_list_unique_all_same(self, tools):
        """Test list with all same elements"""
        result = tools.list_unique({'items': [5, 5, 5, 5]})
        assert result['success'] is True
        assert result['result'] == [5]
        assert result['duplicates_removed'] == 3

    def test_list_unique_empty(self, tools):
        """Test empty list"""
        result = tools.list_unique({'items': []})
        assert result['success'] is True
        assert result['result'] == []
        assert result['duplicates_removed'] == 0

    def test_list_unique_preserves_order(self, tools):
        """Test that order is preserved"""
        result = tools.list_unique({'items': [3, 1, 2, 1, 3]})
        assert result['result'] == [3, 1, 2]  # Order of first appearance
