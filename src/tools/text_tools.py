"""
Text Processing Tools
Tools for text manipulation and analysis
"""

from typing import Dict, List, Any
import re


class TextTools:
    """Text processing tools"""

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of text tools"""
        return [
            {
                'name': 'text_length',
                'description': 'Count characters in text',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to count'}
                },
                'handler': self.text_length
            },
            {
                'name': 'text_uppercase',
                'description': 'Convert text to uppercase',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to convert'}
                },
                'handler': self.text_uppercase
            },
            {
                'name': 'text_lowercase',
                'description': 'Convert text to lowercase',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to convert'}
                },
                'handler': self.text_lowercase
            },
            {
                'name': 'text_reverse',
                'description': 'Reverse text',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to reverse'}
                },
                'handler': self.text_reverse
            },
            {
                'name': 'text_word_count',
                'description': 'Count words in text',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to analyze'}
                },
                'handler': self.text_word_count
            },
            {
                'name': 'text_find_replace',
                'description': 'Find and replace text',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Input text'},
                    'find': {'type': 'string', 'required': True, 'description': 'Text to find'},
                    'replace': {'type': 'string', 'required': True, 'description': 'Replacement text'}
                },
                'handler': self.text_find_replace
            },
            {
                'name': 'text_extract_emails',
                'description': 'Extract email addresses from text',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to search'}
                },
                'handler': self.text_extract_emails
            },
            {
                'name': 'text_extract_urls',
                'description': 'Extract URLs from text',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to search'}
                },
                'handler': self.text_extract_urls
            }
        ]

    def text_length(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Count characters in text"""
        text = params.get('text', '')
        return {
            'length': len(text),
            'text_preview': text[:50] + '...' if len(text) > 50 else text
        }

    def text_uppercase(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert text to uppercase"""
        text = params.get('text', '')
        return {'result': text.upper()}

    def text_lowercase(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert text to lowercase"""
        text = params.get('text', '')
        return {'result': text.lower()}

    def text_reverse(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reverse text"""
        text = params.get('text', '')
        return {'result': text[::-1]}

    def text_word_count(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Count words in text"""
        text = params.get('text', '')
        words = text.split()
        return {
            'word_count': len(words),
            'character_count': len(text),
            'line_count': text.count('\n') + 1
        }

    def text_find_replace(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find and replace text"""
        text = params.get('text', '')
        find = params.get('find', '')
        replace = params.get('replace', '')

        result = text.replace(find, replace)
        count = text.count(find)

        return {
            'result': result,
            'replacements': count
        }

    def text_extract_emails(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract email addresses from text"""
        text = params.get('text', '')
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)

        return {
            'emails': list(set(emails)),
            'count': len(set(emails))
        }

    def text_extract_urls(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract URLs from text"""
        text = params.get('text', '')
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)

        return {
            'urls': list(set(urls)),
            'count': len(set(urls))
        }
