"""
Web Tools
Tools for web-related operations
"""

from typing import Dict, List, Any
import urllib.parse


class WebTools:
    """Web-related tools"""

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of web tools"""
        return [
            {
                'name': 'url_encode',
                'description': 'URL encode text',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to encode'}
                },
                'handler': self.url_encode
            },
            {
                'name': 'url_decode',
                'description': 'URL decode text',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to decode'}
                },
                'handler': self.url_decode
            },
            {
                'name': 'url_parse',
                'description': 'Parse URL into components',
                'parameters': {
                    'url': {'type': 'string', 'required': True, 'description': 'URL to parse'}
                },
                'handler': self.url_parse
            },
            {
                'name': 'html_escape',
                'description': 'Escape HTML special characters',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to escape'}
                },
                'handler': self.html_escape
            },
            {
                'name': 'html_unescape',
                'description': 'Unescape HTML special characters',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to unescape'}
                },
                'handler': self.html_unescape
            }
        ]

    def url_encode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """URL encode text"""
        text = params.get('text', '')
        encoded = urllib.parse.quote(text)
        return {
            'success': True,
            'encoded': encoded
        }

    def url_decode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """URL decode text"""
        text = params.get('text', '')
        try:
            decoded = urllib.parse.unquote(text)
            return {
                'success': True,
                'decoded': decoded
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def url_parse(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse URL into components"""
        url = params.get('url', '')
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)

            return {
                'success': True,
                'scheme': parsed.scheme,
                'netloc': parsed.netloc,
                'path': parsed.path,
                'params': parsed.params,
                'query': parsed.query,
                'query_params': query_params,
                'fragment': parsed.fragment
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def html_escape(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Escape HTML special characters"""
        text = params.get('text', '')
        import html
        escaped = html.escape(text)
        return {
            'success': True,
            'escaped': escaped
        }

    def html_unescape(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Unescape HTML special characters"""
        text = params.get('text', '')
        import html
        unescaped = html.unescape(text)
        return {
            'success': True,
            'unescaped': unescaped
        }
