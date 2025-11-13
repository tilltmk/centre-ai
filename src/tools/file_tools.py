"""
File Tools
Tools for file operations (safe operations only)
"""

from typing import Dict, List, Any
import os
import mimetypes


class FileTools:
    """File-related tools"""

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of file tools"""
        return [
            {
                'name': 'file_extension',
                'description': 'Get file extension from filename',
                'parameters': {
                    'filename': {'type': 'string', 'required': True, 'description': 'Filename'}
                },
                'handler': self.file_extension
            },
            {
                'name': 'file_mimetype',
                'description': 'Get MIME type from filename',
                'parameters': {
                    'filename': {'type': 'string', 'required': True, 'description': 'Filename'}
                },
                'handler': self.file_mimetype
            },
            {
                'name': 'path_join',
                'description': 'Join path components',
                'parameters': {
                    'parts': {'type': 'array', 'required': True, 'description': 'Path parts to join'}
                },
                'handler': self.path_join
            },
            {
                'name': 'path_basename',
                'description': 'Get basename from path',
                'parameters': {
                    'path': {'type': 'string', 'required': True, 'description': 'File path'}
                },
                'handler': self.path_basename
            },
            {
                'name': 'path_dirname',
                'description': 'Get directory name from path',
                'parameters': {
                    'path': {'type': 'string', 'required': True, 'description': 'File path'}
                },
                'handler': self.path_dirname
            }
        ]

    def file_extension(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get file extension from filename"""
        filename = params.get('filename', '')
        _, ext = os.path.splitext(filename)
        return {
            'success': True,
            'filename': filename,
            'extension': ext
        }

    def file_mimetype(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get MIME type from filename"""
        filename = params.get('filename', '')
        mimetype, encoding = mimetypes.guess_type(filename)
        return {
            'success': True,
            'filename': filename,
            'mimetype': mimetype or 'unknown',
            'encoding': encoding
        }

    def path_join(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Join path components"""
        parts = params.get('parts', [])
        try:
            joined = os.path.join(*parts)
            return {
                'success': True,
                'result': joined
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def path_basename(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get basename from path"""
        path = params.get('path', '')
        basename = os.path.basename(path)
        return {
            'success': True,
            'basename': basename
        }

    def path_dirname(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get directory name from path"""
        path = params.get('path', '')
        dirname = os.path.dirname(path)
        return {
            'success': True,
            'dirname': dirname
        }
