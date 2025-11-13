"""
Code Indexer
Indexes code repositories for semantic search
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
import logging

logger = logging.getLogger(__name__)


class CodeIndexer:
    """Indexes code files from Git repositories"""

    # Common programming file extensions
    CODE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript-react',
        '.tsx': 'typescript-react',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.sql': 'sql',
        '.sh': 'bash',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.xml': 'xml',
        '.md': 'markdown',
        '.rst': 'rst',
        '.tex': 'latex'
    }

    # Default ignore patterns (like .gitignore)
    DEFAULT_IGNORE_PATTERNS = [
        '.git/',
        '__pycache__/',
        'node_modules/',
        'venv/',
        'env/',
        '.env/',
        'dist/',
        'build/',
        '.next/',
        '.cache/',
        'target/',
        'bin/',
        'obj/',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '*.so',
        '*.dll',
        '*.dylib',
        '*.exe',
        '*.o',
        '*.a',
        '*.class',
        '*.jar',
        '*.war',
        '*.ear',
        '*.min.js',
        '*.min.css',
        '*.map',
        'package-lock.json',
        'yarn.lock',
        '.DS_Store'
    ]

    def __init__(self, vector_db=None):
        self.vector_db = vector_db
        self.ignore_spec = PathSpec.from_lines(
            GitWildMatchPattern,
            self.DEFAULT_IGNORE_PATTERNS
        )

    def _should_ignore(self, file_path: str) -> bool:
        """Check if file should be ignored"""
        return self.ignore_spec.match_file(file_path)

    def _get_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        _, ext = os.path.splitext(file_path)
        return self.CODE_EXTENSIONS.get(ext.lower())

    def _hash_content(self, content: str) -> str:
        """Generate hash of file content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _chunk_code(self, content: str, chunk_size: int = 500) -> List[str]:
        """Split code into chunks for indexing"""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            if current_size + line_size > chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(line)
            current_size += line_size

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def scan_repository(self, repo_path: str) -> List[Dict[str, Any]]:
        """
        Scan repository and return list of code files with metadata
        """
        files = []

        for root, dirs, filenames in os.walk(repo_path):
            # Filter directories
            dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]

            for filename in filenames:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, repo_path)

                # Skip ignored files
                if self._should_ignore(relative_path):
                    continue

                # Check if it's a code file
                language = self._get_language(filename)
                if not language:
                    continue

                # Try to read file
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Skip empty files
                    if not content.strip():
                        continue

                    file_info = {
                        'file_path': relative_path,
                        'language': language,
                        'content': content,
                        'file_hash': self._hash_content(content),
                        'lines_count': len(content.split('\n')),
                        'size_bytes': len(content.encode('utf-8'))
                    }

                    files.append(file_info)

                except Exception as e:
                    logger.debug(f"Skipping file {relative_path}: {str(e)}")
                    continue

        logger.info(f"Scanned repository: found {len(files)} code files")
        return files

    def index_file(
        self,
        repo_id: str,
        file_info: Dict[str, Any],
        collection_name: str = 'code_files'
    ) -> bool:
        """Index a single file to vector database"""
        if not self.vector_db:
            logger.error("Vector DB not initialized")
            return False

        try:
            # Chunk the code
            chunks = self._chunk_code(file_info['content'])

            # Create points for each chunk
            points = []
            for i, chunk in enumerate(chunks):
                point_id = f"{repo_id}:{file_info['file_path']}:chunk{i}"

                # Generate embedding
                vector = self.vector_db.embed_text(chunk)

                # Create payload
                payload = {
                    'repo_id': repo_id,
                    'file_path': file_info['file_path'],
                    'language': file_info['language'],
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'content': chunk,
                    'file_hash': file_info['file_hash']
                }

                points.append({
                    'id': point_id,
                    'vector': vector,
                    'payload': payload
                })

            # Upsert to vector DB
            success = self.vector_db.upsert_points(collection_name, points)

            if success:
                logger.debug(f"Indexed {file_info['file_path']} ({len(chunks)} chunks)")

            return success

        except Exception as e:
            logger.error(f"Error indexing file {file_info['file_path']}: {str(e)}")
            return False

    def index_repository(
        self,
        repo_id: str,
        repo_path: str,
        collection_name: str = 'code_files'
    ) -> Dict[str, Any]:
        """Index entire repository"""
        if not self.vector_db:
            return {
                'success': False,
                'error': 'Vector DB not initialized'
            }

        try:
            # Scan repository
            files = self.scan_repository(repo_path)

            if not files:
                return {
                    'success': True,
                    'files_indexed': 0,
                    'message': 'No code files found to index'
                }

            # Index each file
            indexed_count = 0
            failed_count = 0

            for file_info in files:
                if self.index_file(repo_id, file_info, collection_name):
                    indexed_count += 1
                else:
                    failed_count += 1

            return {
                'success': True,
                'files_scanned': len(files),
                'files_indexed': indexed_count,
                'files_failed': failed_count,
                'languages': list(set(f['language'] for f in files))
            }

        except Exception as e:
            logger.error(f"Error indexing repository: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def search_code(
        self,
        query: str,
        repo_id: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 10,
        collection_name: str = 'code_files'
    ) -> List[Dict[str, Any]]:
        """Search code semantically"""
        if not self.vector_db:
            logger.error("Vector DB not initialized")
            return []

        try:
            # Build filter conditions
            filter_conditions = {}
            if repo_id:
                filter_conditions['repo_id'] = repo_id
            if language:
                filter_conditions['language'] = language

            # Search
            results = self.vector_db.search_text(
                collection_name=collection_name,
                query_text=query,
                limit=limit,
                filter_conditions=filter_conditions if filter_conditions else None
            )

            return results

        except Exception as e:
            logger.error(f"Error searching code: {str(e)}")
            return []

    def delete_repository_index(
        self,
        repo_id: str,
        collection_name: str = 'code_files'
    ) -> bool:
        """Delete all indexed data for a repository"""
        # Note: Qdrant doesn't support delete by filter in community edition
        # This would require iterating through all points and deleting individually
        # For now, we'll return a placeholder
        logger.warning(f"Repository index deletion not fully implemented for {repo_id}")
        return True
