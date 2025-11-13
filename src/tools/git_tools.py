"""
Git Repository Tools
Tools for managing Git repositories: clone, fetch, modify, commit
"""

import os
import shutil
from typing import Dict, List, Any
import git
from git import Repo, GitCommandError
import logging

logger = logging.getLogger(__name__)


class GitTools:
    """Git repository management tools"""

    def __init__(self, repos_path: str = None):
        self.repos_path = repos_path or os.getenv('GIT_REPOS_PATH', '/app/git_repos')
        os.makedirs(self.repos_path, exist_ok=True)

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of git tools"""
        return [
            {
                'name': 'git_clone',
                'description': 'Clone a Git repository',
                'parameters': {
                    'repo_url': {'type': 'string', 'required': True, 'description': 'Git repository URL'},
                    'branch': {'type': 'string', 'required': False, 'description': 'Branch to clone', 'default': 'main'},
                    'depth': {'type': 'integer', 'required': False, 'description': 'Clone depth (shallow clone)', 'default': None}
                },
                'handler': self.git_clone
            },
            {
                'name': 'git_pull',
                'description': 'Pull latest changes from repository',
                'parameters': {
                    'repo_name': {'type': 'string', 'required': True, 'description': 'Repository name'}
                },
                'handler': self.git_pull
            },
            {
                'name': 'git_status',
                'description': 'Get Git repository status',
                'parameters': {
                    'repo_name': {'type': 'string', 'required': True, 'description': 'Repository name'}
                },
                'handler': self.git_status
            },
            {
                'name': 'git_log',
                'description': 'Get Git commit history',
                'parameters': {
                    'repo_name': {'type': 'string', 'required': True, 'description': 'Repository name'},
                    'max_count': {'type': 'integer', 'required': False, 'description': 'Max commits to show', 'default': 10}
                },
                'handler': self.git_log
            },
            {
                'name': 'git_diff',
                'description': 'Get Git diff',
                'parameters': {
                    'repo_name': {'type': 'string', 'required': True, 'description': 'Repository name'},
                    'file_path': {'type': 'string', 'required': False, 'description': 'Specific file path'}
                },
                'handler': self.git_diff
            },
            {
                'name': 'git_list_repos',
                'description': 'List all cloned repositories',
                'parameters': {},
                'handler': self.git_list_repos
            },
            {
                'name': 'git_list_files',
                'description': 'List files in repository',
                'parameters': {
                    'repo_name': {'type': 'string', 'required': True, 'description': 'Repository name'},
                    'path': {'type': 'string', 'required': False, 'description': 'Subdirectory path', 'default': '.'}
                },
                'handler': self.git_list_files
            },
            {
                'name': 'git_read_file',
                'description': 'Read a file from repository',
                'parameters': {
                    'repo_name': {'type': 'string', 'required': True, 'description': 'Repository name'},
                    'file_path': {'type': 'string', 'required': True, 'description': 'File path'}
                },
                'handler': self.git_read_file
            },
            {
                'name': 'git_write_file',
                'description': 'Write/modify a file in repository',
                'parameters': {
                    'repo_name': {'type': 'string', 'required': True, 'description': 'Repository name'},
                    'file_path': {'type': 'string', 'required': True, 'description': 'File path'},
                    'content': {'type': 'string', 'required': True, 'description': 'File content'}
                },
                'handler': self.git_write_file
            },
            {
                'name': 'git_commit',
                'description': 'Commit changes to repository',
                'parameters': {
                    'repo_name': {'type': 'string', 'required': True, 'description': 'Repository name'},
                    'message': {'type': 'string', 'required': True, 'description': 'Commit message'},
                    'files': {'type': 'array', 'required': False, 'description': 'Specific files to commit'}
                },
                'handler': self.git_commit
            },
            {
                'name': 'git_push',
                'description': 'Push commits to remote',
                'parameters': {
                    'repo_name': {'type': 'string', 'required': True, 'description': 'Repository name'},
                    'branch': {'type': 'string', 'required': False, 'description': 'Branch to push'}
                },
                'handler': self.git_push
            },
            {
                'name': 'git_delete_repo',
                'description': 'Delete a cloned repository',
                'parameters': {
                    'repo_name': {'type': 'string', 'required': True, 'description': 'Repository name'}
                },
                'handler': self.git_delete_repo
            }
        ]

    def _get_repo_path(self, repo_name: str) -> str:
        """Get full path to repository"""
        return os.path.join(self.repos_path, repo_name)

    def _sanitize_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL"""
        # Remove .git extension and get last part of path
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        return repo_name

    def git_clone(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clone a Git repository"""
        repo_url = params.get('repo_url')
        branch = params.get('branch', 'main')
        depth = params.get('depth')

        try:
            # Extract repo name
            repo_name = self._sanitize_repo_name(repo_url)
            repo_path = self._get_repo_path(repo_name)

            # Check if already exists
            if os.path.exists(repo_path):
                return {
                    'success': False,
                    'error': f'Repository {repo_name} already exists. Use git_pull to update.'
                }

            # Clone repository
            clone_kwargs = {'branch': branch}
            if depth:
                clone_kwargs['depth'] = depth

            logger.info(f"Cloning repository: {repo_url} to {repo_path}")
            repo = Repo.clone_from(repo_url, repo_path, **clone_kwargs)

            return {
                'success': True,
                'repo_name': repo_name,
                'repo_path': repo_path,
                'branch': repo.active_branch.name,
                'commit': str(repo.head.commit.hexsha[:8]),
                'message': f'Successfully cloned {repo_name}'
            }

        except GitCommandError as e:
            logger.error(f"Git clone error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Clone error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def git_pull(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Pull latest changes"""
        repo_name = params.get('repo_name')
        repo_path = self._get_repo_path(repo_name)

        try:
            if not os.path.exists(repo_path):
                return {
                    'success': False,
                    'error': f'Repository {repo_name} not found'
                }

            repo = Repo(repo_path)
            origin = repo.remotes.origin

            # Pull changes
            pull_info = origin.pull()

            return {
                'success': True,
                'repo_name': repo_name,
                'branch': repo.active_branch.name,
                'commit': str(repo.head.commit.hexsha[:8]),
                'message': 'Successfully pulled latest changes'
            }

        except Exception as e:
            logger.error(f"Git pull error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def git_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository status"""
        repo_name = params.get('repo_name')
        repo_path = self._get_repo_path(repo_name)

        try:
            if not os.path.exists(repo_path):
                return {
                    'success': False,
                    'error': f'Repository {repo_name} not found'
                }

            repo = Repo(repo_path)

            return {
                'success': True,
                'repo_name': repo_name,
                'branch': repo.active_branch.name,
                'commit': str(repo.head.commit.hexsha[:8]),
                'is_dirty': repo.is_dirty(),
                'untracked_files': repo.untracked_files,
                'modified_files': [item.a_path for item in repo.index.diff(None)],
                'staged_files': [item.a_path for item in repo.index.diff('HEAD')]
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def git_log(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get commit history"""
        repo_name = params.get('repo_name')
        max_count = params.get('max_count', 10)
        repo_path = self._get_repo_path(repo_name)

        try:
            if not os.path.exists(repo_path):
                return {
                    'success': False,
                    'error': f'Repository {repo_name} not found'
                }

            repo = Repo(repo_path)
            commits = []

            for commit in repo.iter_commits(max_count=max_count):
                commits.append({
                    'hash': commit.hexsha[:8],
                    'author': str(commit.author),
                    'date': commit.committed_datetime.isoformat(),
                    'message': commit.message.strip()
                })

            return {
                'success': True,
                'repo_name': repo_name,
                'commits': commits,
                'count': len(commits)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def git_diff(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get diff"""
        repo_name = params.get('repo_name')
        file_path = params.get('file_path')
        repo_path = self._get_repo_path(repo_name)

        try:
            if not os.path.exists(repo_path):
                return {
                    'success': False,
                    'error': f'Repository {repo_name} not found'
                }

            repo = Repo(repo_path)

            if file_path:
                diff = repo.git.diff('HEAD', file_path)
            else:
                diff = repo.git.diff('HEAD')

            return {
                'success': True,
                'repo_name': repo_name,
                'diff': diff
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def git_list_repos(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all cloned repositories"""
        try:
            repos = []

            if os.path.exists(self.repos_path):
                for item in os.listdir(self.repos_path):
                    repo_path = os.path.join(self.repos_path, item)
                    if os.path.isdir(repo_path) and os.path.exists(os.path.join(repo_path, '.git')):
                        try:
                            repo = Repo(repo_path)
                            repos.append({
                                'name': item,
                                'path': repo_path,
                                'branch': repo.active_branch.name,
                                'commit': str(repo.head.commit.hexsha[:8]),
                                'is_dirty': repo.is_dirty()
                            })
                        except:
                            pass

            return {
                'success': True,
                'repos': repos,
                'count': len(repos)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def git_list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files in repository"""
        repo_name = params.get('repo_name')
        path = params.get('path', '.')
        repo_path = self._get_repo_path(repo_name)

        try:
            if not os.path.exists(repo_path):
                return {
                    'success': False,
                    'error': f'Repository {repo_name} not found'
                }

            full_path = os.path.join(repo_path, path)
            if not os.path.exists(full_path):
                return {
                    'success': False,
                    'error': f'Path {path} not found in repository'
                }

            files = []
            dirs = []

            for item in os.listdir(full_path):
                if item.startswith('.'):
                    continue

                item_path = os.path.join(full_path, item)
                rel_path = os.path.relpath(item_path, repo_path)

                if os.path.isdir(item_path):
                    dirs.append(rel_path)
                else:
                    size = os.path.getsize(item_path)
                    files.append({
                        'path': rel_path,
                        'size': size
                    })

            return {
                'success': True,
                'repo_name': repo_name,
                'path': path,
                'directories': sorted(dirs),
                'files': sorted(files, key=lambda x: x['path']),
                'total_files': len(files),
                'total_dirs': len(dirs)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def git_read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file from repository"""
        repo_name = params.get('repo_name')
        file_path = params.get('file_path')
        repo_path = self._get_repo_path(repo_name)

        try:
            if not os.path.exists(repo_path):
                return {
                    'success': False,
                    'error': f'Repository {repo_name} not found'
                }

            full_path = os.path.join(repo_path, file_path)
            if not os.path.exists(full_path):
                return {
                    'success': False,
                    'error': f'File {file_path} not found'
                }

            if os.path.isdir(full_path):
                return {
                    'success': False,
                    'error': f'{file_path} is a directory, not a file'
                }

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'success': True,
                'repo_name': repo_name,
                'file_path': file_path,
                'content': content,
                'size': len(content)
            }

        except UnicodeDecodeError:
            return {
                'success': False,
                'error': 'File is binary and cannot be read as text'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def git_write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write/modify a file in repository"""
        repo_name = params.get('repo_name')
        file_path = params.get('file_path')
        content = params.get('content')
        repo_path = self._get_repo_path(repo_name)

        try:
            if not os.path.exists(repo_path):
                return {
                    'success': False,
                    'error': f'Repository {repo_name} not found'
                }

            full_path = os.path.join(repo_path, file_path)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                'success': True,
                'repo_name': repo_name,
                'file_path': file_path,
                'size': len(content),
                'message': f'Successfully wrote {file_path}'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def git_commit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Commit changes"""
        repo_name = params.get('repo_name')
        message = params.get('message')
        files = params.get('files', [])
        repo_path = self._get_repo_path(repo_name)

        try:
            if not os.path.exists(repo_path):
                return {
                    'success': False,
                    'error': f'Repository {repo_name} not found'
                }

            repo = Repo(repo_path)

            # Add files
            if files:
                repo.index.add(files)
            else:
                repo.git.add(A=True)

            # Commit
            commit = repo.index.commit(message)

            return {
                'success': True,
                'repo_name': repo_name,
                'commit': str(commit.hexsha[:8]),
                'message': message,
                'files_committed': len(commit.stats.files)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def git_push(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Push commits to remote"""
        repo_name = params.get('repo_name')
        branch = params.get('branch')
        repo_path = self._get_repo_path(repo_name)

        try:
            if not os.path.exists(repo_path):
                return {
                    'success': False,
                    'error': f'Repository {repo_name} not found'
                }

            repo = Repo(repo_path)
            origin = repo.remotes.origin

            if branch:
                push_info = origin.push(branch)
            else:
                push_info = origin.push()

            return {
                'success': True,
                'repo_name': repo_name,
                'message': 'Successfully pushed to remote'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def git_delete_repo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a cloned repository"""
        repo_name = params.get('repo_name')
        repo_path = self._get_repo_path(repo_name)

        try:
            if not os.path.exists(repo_path):
                return {
                    'success': False,
                    'error': f'Repository {repo_name} not found'
                }

            # Delete the repository directory
            shutil.rmtree(repo_path)

            return {
                'success': True,
                'repo_name': repo_name,
                'message': f'Successfully deleted {repo_name}'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
