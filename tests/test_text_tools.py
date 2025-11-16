"""
Tests for TextTools module
"""

import pytest
from src.tools.text_tools import TextTools


class TestTextTools:
    """Test suite for TextTools"""

    @pytest.fixture
    def tools(self):
        """Create TextTools instance"""
        return TextTools()

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

    # text_length tests
    def test_text_length_basic(self, tools):
        """Test basic text length counting"""
        result = tools.text_length({'text': 'hello'})
        assert result['length'] == 5
        assert result['text_preview'] == 'hello'

    def test_text_length_empty(self, tools):
        """Test empty text"""
        result = tools.text_length({'text': ''})
        assert result['length'] == 0

    def test_text_length_long_text(self, tools):
        """Test long text truncation in preview"""
        long_text = 'a' * 100
        result = tools.text_length({'text': long_text})
        assert result['length'] == 100
        assert result['text_preview'] == 'a' * 50 + '...'

    def test_text_length_with_unicode(self, tools):
        """Test unicode character counting"""
        result = tools.text_length({'text': 'こんにちは'})
        assert result['length'] == 5

    def test_text_length_missing_param(self, tools):
        """Test with missing parameter"""
        result = tools.text_length({})
        assert result['length'] == 0

    # text_uppercase tests
    def test_text_uppercase_basic(self, tools):
        """Test basic uppercase conversion"""
        result = tools.text_uppercase({'text': 'hello'})
        assert result['result'] == 'HELLO'

    def test_text_uppercase_mixed(self, tools):
        """Test mixed case to uppercase"""
        result = tools.text_uppercase({'text': 'Hello World'})
        assert result['result'] == 'HELLO WORLD'

    def test_text_uppercase_already_upper(self, tools):
        """Test already uppercase text"""
        result = tools.text_uppercase({'text': 'HELLO'})
        assert result['result'] == 'HELLO'

    def test_text_uppercase_with_numbers(self, tools):
        """Test text with numbers"""
        result = tools.text_uppercase({'text': 'test123'})
        assert result['result'] == 'TEST123'

    # text_lowercase tests
    def test_text_lowercase_basic(self, tools):
        """Test basic lowercase conversion"""
        result = tools.text_lowercase({'text': 'HELLO'})
        assert result['result'] == 'hello'

    def test_text_lowercase_mixed(self, tools):
        """Test mixed case to lowercase"""
        result = tools.text_lowercase({'text': 'Hello World'})
        assert result['result'] == 'hello world'

    def test_text_lowercase_already_lower(self, tools):
        """Test already lowercase text"""
        result = tools.text_lowercase({'text': 'hello'})
        assert result['result'] == 'hello'

    # text_reverse tests
    def test_text_reverse_basic(self, tools):
        """Test basic text reversal"""
        result = tools.text_reverse({'text': 'hello'})
        assert result['result'] == 'olleh'

    def test_text_reverse_palindrome(self, tools):
        """Test palindrome text"""
        result = tools.text_reverse({'text': 'radar'})
        assert result['result'] == 'radar'

    def test_text_reverse_with_spaces(self, tools):
        """Test text with spaces"""
        result = tools.text_reverse({'text': 'hello world'})
        assert result['result'] == 'dlrow olleh'

    def test_text_reverse_empty(self, tools):
        """Test empty text reversal"""
        result = tools.text_reverse({'text': ''})
        assert result['result'] == ''

    # text_word_count tests
    def test_text_word_count_basic(self, tools):
        """Test basic word counting"""
        result = tools.text_word_count({'text': 'hello world'})
        assert result['word_count'] == 2
        assert result['character_count'] == 11
        assert result['line_count'] == 1

    def test_text_word_count_multiple_lines(self, tools):
        """Test multiline text"""
        result = tools.text_word_count({'text': 'hello\nworld\ntest'})
        assert result['word_count'] == 3
        assert result['line_count'] == 3

    def test_text_word_count_single_word(self, tools):
        """Test single word"""
        result = tools.text_word_count({'text': 'hello'})
        assert result['word_count'] == 1

    def test_text_word_count_empty(self, tools):
        """Test empty text"""
        result = tools.text_word_count({'text': ''})
        assert result['word_count'] == 0
        assert result['line_count'] == 1

    def test_text_word_count_multiple_spaces(self, tools):
        """Test text with multiple spaces"""
        result = tools.text_word_count({'text': 'hello   world'})
        assert result['word_count'] == 2

    # text_find_replace tests
    def test_text_find_replace_basic(self, tools):
        """Test basic find and replace"""
        result = tools.text_find_replace({
            'text': 'hello world',
            'find': 'world',
            'replace': 'universe'
        })
        assert result['result'] == 'hello universe'
        assert result['replacements'] == 1

    def test_text_find_replace_multiple(self, tools):
        """Test multiple replacements"""
        result = tools.text_find_replace({
            'text': 'test test test',
            'find': 'test',
            'replace': 'replaced'
        })
        assert result['result'] == 'replaced replaced replaced'
        assert result['replacements'] == 3

    def test_text_find_replace_not_found(self, tools):
        """Test when pattern not found"""
        result = tools.text_find_replace({
            'text': 'hello world',
            'find': 'foo',
            'replace': 'bar'
        })
        assert result['result'] == 'hello world'
        assert result['replacements'] == 0

    def test_text_find_replace_empty_replace(self, tools):
        """Test replacing with empty string"""
        result = tools.text_find_replace({
            'text': 'hello world',
            'find': ' world',
            'replace': ''
        })
        assert result['result'] == 'hello'
        assert result['replacements'] == 1

    # text_extract_emails tests
    def test_text_extract_emails_single(self, tools):
        """Test extracting single email"""
        result = tools.text_extract_emails({'text': 'Contact us at test@example.com'})
        assert 'test@example.com' in result['emails']
        assert result['count'] == 1

    def test_text_extract_emails_multiple(self, tools):
        """Test extracting multiple emails"""
        result = tools.text_extract_emails({
            'text': 'Email test@example.com or admin@company.org for help'
        })
        assert result['count'] == 2
        assert 'test@example.com' in result['emails']
        assert 'admin@company.org' in result['emails']

    def test_text_extract_emails_none(self, tools):
        """Test no emails found"""
        result = tools.text_extract_emails({'text': 'No emails here'})
        assert result['count'] == 0
        assert result['emails'] == []

    def test_text_extract_emails_duplicates(self, tools):
        """Test duplicate emails are deduplicated"""
        result = tools.text_extract_emails({
            'text': 'test@example.com and test@example.com'
        })
        assert result['count'] == 1

    def test_text_extract_emails_complex(self, tools):
        """Test complex email formats"""
        result = tools.text_extract_emails({
            'text': 'user.name+tag@sub.domain.com'
        })
        assert result['count'] == 1
        assert 'user.name+tag@sub.domain.com' in result['emails']

    # text_extract_urls tests
    def test_text_extract_urls_http(self, tools):
        """Test extracting HTTP URLs"""
        result = tools.text_extract_urls({'text': 'Visit http://example.com'})
        assert result['count'] == 1
        assert 'http://example.com' in result['urls']

    def test_text_extract_urls_https(self, tools):
        """Test extracting HTTPS URLs"""
        result = tools.text_extract_urls({'text': 'Visit https://example.com'})
        assert result['count'] == 1
        assert 'https://example.com' in result['urls']

    def test_text_extract_urls_multiple(self, tools):
        """Test extracting multiple URLs"""
        result = tools.text_extract_urls({
            'text': 'Check https://example.com and http://test.org'
        })
        assert result['count'] == 2

    def test_text_extract_urls_none(self, tools):
        """Test no URLs found"""
        result = tools.text_extract_urls({'text': 'No URLs here'})
        assert result['count'] == 0
        assert result['urls'] == []

    def test_text_extract_urls_with_path(self, tools):
        """Test URLs with path"""
        result = tools.text_extract_urls({
            'text': 'https://example.com/path/to/page'
        })
        assert result['count'] == 1
        assert 'https://example.com/path/to/page' in result['urls']

    def test_text_extract_urls_duplicates(self, tools):
        """Test duplicate URLs are deduplicated"""
        result = tools.text_extract_urls({
            'text': 'https://example.com https://example.com'
        })
        assert result['count'] == 1
