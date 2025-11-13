"""
Data Processing Tools
Tools for data manipulation and calculations
"""

from typing import Dict, List, Any
import json
import hashlib
import base64


class DataTools:
    """Data processing tools"""

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of data tools"""
        return [
            {
                'name': 'json_format',
                'description': 'Format and prettify JSON',
                'parameters': {
                    'json_string': {'type': 'string', 'required': True, 'description': 'JSON string to format'}
                },
                'handler': self.json_format
            },
            {
                'name': 'json_validate',
                'description': 'Validate JSON syntax',
                'parameters': {
                    'json_string': {'type': 'string', 'required': True, 'description': 'JSON string to validate'}
                },
                'handler': self.json_validate
            },
            {
                'name': 'calculate',
                'description': 'Perform mathematical calculations',
                'parameters': {
                    'expression': {'type': 'string', 'required': True, 'description': 'Math expression'}
                },
                'handler': self.calculate
            },
            {
                'name': 'hash_text',
                'description': 'Generate hash of text (MD5, SHA256)',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to hash'},
                    'algorithm': {'type': 'string', 'required': False, 'description': 'Hash algorithm (md5/sha256)', 'default': 'sha256'}
                },
                'handler': self.hash_text
            },
            {
                'name': 'base64_encode',
                'description': 'Encode text to Base64',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to encode'}
                },
                'handler': self.base64_encode
            },
            {
                'name': 'base64_decode',
                'description': 'Decode Base64 to text',
                'parameters': {
                    'encoded': {'type': 'string', 'required': True, 'description': 'Base64 encoded string'}
                },
                'handler': self.base64_decode
            },
            {
                'name': 'list_sort',
                'description': 'Sort a list of items',
                'parameters': {
                    'items': {'type': 'array', 'required': True, 'description': 'List of items to sort'},
                    'reverse': {'type': 'boolean', 'required': False, 'description': 'Sort in reverse', 'default': False}
                },
                'handler': self.list_sort
            },
            {
                'name': 'list_unique',
                'description': 'Get unique items from list',
                'parameters': {
                    'items': {'type': 'array', 'required': True, 'description': 'List of items'}
                },
                'handler': self.list_unique
            }
        ]

    def json_format(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Format and prettify JSON"""
        json_string = params.get('json_string', '')

        try:
            parsed = json.loads(json_string)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            return {
                'success': True,
                'result': formatted
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def json_validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON syntax"""
        json_string = params.get('json_string', '')

        try:
            json.loads(json_string)
            return {
                'valid': True,
                'message': 'Valid JSON'
            }
        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'error': str(e)
            }

    def calculate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform mathematical calculations"""
        expression = params.get('expression', '')

        try:
            # Safe evaluation of mathematical expressions
            # Only allow mathematical operations
            allowed_chars = set('0123456789+-*/()%. ')
            if not all(c in allowed_chars for c in expression):
                return {
                    'success': False,
                    'error': 'Invalid characters in expression'
                }

            result = eval(expression, {"__builtins__": {}}, {})
            return {
                'success': True,
                'expression': expression,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def hash_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hash of text"""
        text = params.get('text', '')
        algorithm = params.get('algorithm', 'sha256').lower()

        try:
            if algorithm == 'md5':
                hash_obj = hashlib.md5(text.encode('utf-8'))
            elif algorithm == 'sha256':
                hash_obj = hashlib.sha256(text.encode('utf-8'))
            elif algorithm == 'sha1':
                hash_obj = hashlib.sha1(text.encode('utf-8'))
            else:
                return {
                    'success': False,
                    'error': f'Unsupported algorithm: {algorithm}'
                }

            return {
                'success': True,
                'algorithm': algorithm,
                'hash': hash_obj.hexdigest()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def base64_encode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Encode text to Base64"""
        text = params.get('text', '')

        try:
            encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            return {
                'success': True,
                'encoded': encoded
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def base64_decode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Decode Base64 to text"""
        encoded = params.get('encoded', '')

        try:
            decoded = base64.b64decode(encoded).decode('utf-8')
            return {
                'success': True,
                'decoded': decoded
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def list_sort(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sort a list of items"""
        items = params.get('items', [])
        reverse = params.get('reverse', False)

        try:
            sorted_items = sorted(items, reverse=reverse)
            return {
                'success': True,
                'result': sorted_items,
                'count': len(sorted_items)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def list_unique(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get unique items from list"""
        items = params.get('items', [])

        try:
            # Preserve order while removing duplicates
            seen = set()
            unique_items = []
            for item in items:
                if item not in seen:
                    seen.add(item)
                    unique_items.append(item)

            return {
                'success': True,
                'result': unique_items,
                'original_count': len(items),
                'unique_count': len(unique_items),
                'duplicates_removed': len(items) - len(unique_items)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
