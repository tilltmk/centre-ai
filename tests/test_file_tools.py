"""
Tests for FileTools module
"""

import pytest
from src.tools.file_tools import FileTools


class TestFileTools:
    """Test suite for FileTools"""

    @pytest.fixture
    def tools(self):
        """Create FileTools instance"""
        return FileTools()

    def test_get_tools_returns_list(self, tools):
        """Test that get_tools returns a list of tools"""
        tool_list = tools.get_tools()
        assert isinstance(tool_list, list)
        assert len(tool_list) == 5

    def test_get_tools_have_required_fields(self, tools):
        """Test that all tools have required fields"""
        tool_list = tools.get_tools()
        for tool in tool_list:
            assert 'name' in tool
            assert 'description' in tool
            assert 'parameters' in tool
            assert 'handler' in tool
            assert callable(tool['handler'])

    # file_extension tests
    def test_file_extension_py(self, tools):
        """Test Python file extension"""
        result = tools.file_extension({'filename': 'test.py'})
        assert result['success'] is True
        assert result['extension'] == '.py'
        assert result['filename'] == 'test.py'

    def test_file_extension_multiple_dots(self, tools):
        """Test file with multiple dots"""
        result = tools.file_extension({'filename': 'archive.tar.gz'})
        assert result['extension'] == '.gz'

    def test_file_extension_no_extension(self, tools):
        """Test file with no extension"""
        result = tools.file_extension({'filename': 'README'})
        assert result['extension'] == ''

    def test_file_extension_hidden_file(self, tools):
        """Test hidden file"""
        result = tools.file_extension({'filename': '.gitignore'})
        assert result['extension'] == ''

    def test_file_extension_with_path(self, tools):
        """Test file with full path"""
        result = tools.file_extension({'filename': '/path/to/file.txt'})
        assert result['extension'] == '.txt'

    def test_file_extension_empty(self, tools):
        """Test empty filename"""
        result = tools.file_extension({'filename': ''})
        assert result['extension'] == ''

    # file_mimetype tests
    def test_file_mimetype_python(self, tools):
        """Test Python file MIME type"""
        result = tools.file_mimetype({'filename': 'test.py'})
        assert result['success'] is True
        assert result['mimetype'] == 'text/x-python'

    def test_file_mimetype_json(self, tools):
        """Test JSON file MIME type"""
        result = tools.file_mimetype({'filename': 'data.json'})
        assert result['mimetype'] == 'application/json'

    def test_file_mimetype_html(self, tools):
        """Test HTML file MIME type"""
        result = tools.file_mimetype({'filename': 'page.html'})
        assert result['mimetype'] == 'text/html'

    def test_file_mimetype_image(self, tools):
        """Test image file MIME type"""
        result = tools.file_mimetype({'filename': 'image.png'})
        assert result['mimetype'] == 'image/png'

    def test_file_mimetype_unknown(self, tools):
        """Test unknown file MIME type"""
        result = tools.file_mimetype({'filename': 'file.unknownext'})
        assert result['mimetype'] == 'unknown'

    def test_file_mimetype_gzip(self, tools):
        """Test gzipped file"""
        result = tools.file_mimetype({'filename': 'file.txt.gz'})
        assert result['mimetype'] == 'text/plain'
        assert result['encoding'] == 'gzip'

    # path_join tests
    def test_path_join_basic(self, tools):
        """Test basic path joining"""
        result = tools.path_join({'parts': ['home', 'user', 'file.txt']})
        assert result['success'] is True
        assert result['result'] == 'home/user/file.txt'

    def test_path_join_absolute(self, tools):
        """Test joining with absolute path"""
        result = tools.path_join({'parts': ['/home', 'user', 'file.txt']})
        assert result['result'] == '/home/user/file.txt'

    def test_path_join_single_part(self, tools):
        """Test single path part"""
        result = tools.path_join({'parts': ['file.txt']})
        assert result['result'] == 'file.txt'

    def test_path_join_empty_list(self, tools):
        """Test empty parts list"""
        result = tools.path_join({'parts': []})
        assert result['success'] is False
        assert 'error' in result

    def test_path_join_with_slashes(self, tools):
        """Test parts with trailing slashes"""
        result = tools.path_join({'parts': ['home/', 'user/', 'file.txt']})
        assert 'home' in result['result']
        assert 'user' in result['result']
        assert 'file.txt' in result['result']

    # path_basename tests
    def test_path_basename_basic(self, tools):
        """Test basic basename extraction"""
        result = tools.path_basename({'path': '/home/user/file.txt'})
        assert result['success'] is True
        assert result['basename'] == 'file.txt'

    def test_path_basename_no_path(self, tools):
        """Test filename only"""
        result = tools.path_basename({'path': 'file.txt'})
        assert result['basename'] == 'file.txt'

    def test_path_basename_directory(self, tools):
        """Test directory path"""
        result = tools.path_basename({'path': '/home/user/'})
        assert result['basename'] == ''

    def test_path_basename_root(self, tools):
        """Test root path"""
        result = tools.path_basename({'path': '/'})
        assert result['basename'] == ''

    def test_path_basename_nested(self, tools):
        """Test deeply nested path"""
        result = tools.path_basename({'path': '/a/b/c/d/e/file.txt'})
        assert result['basename'] == 'file.txt'

    # path_dirname tests
    def test_path_dirname_basic(self, tools):
        """Test basic dirname extraction"""
        result = tools.path_dirname({'path': '/home/user/file.txt'})
        assert result['success'] is True
        assert result['dirname'] == '/home/user'

    def test_path_dirname_no_path(self, tools):
        """Test filename only"""
        result = tools.path_dirname({'path': 'file.txt'})
        assert result['dirname'] == ''

    def test_path_dirname_root(self, tools):
        """Test root path"""
        result = tools.path_dirname({'path': '/file.txt'})
        assert result['dirname'] == '/'

    def test_path_dirname_nested(self, tools):
        """Test deeply nested path"""
        result = tools.path_dirname({'path': '/a/b/c/d/e/file.txt'})
        assert result['dirname'] == '/a/b/c/d/e'

    def test_path_dirname_trailing_slash(self, tools):
        """Test path with trailing slash"""
        result = tools.path_dirname({'path': '/home/user/'})
        assert result['dirname'] == '/home/user'

    def test_path_dirname_empty(self, tools):
        """Test empty path"""
        result = tools.path_dirname({'path': ''})
        assert result['dirname'] == ''
