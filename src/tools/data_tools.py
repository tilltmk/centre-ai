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
            },
            {
                'name': 'import_claude_data',
                'description': 'Import Claude conversation data from JSON files into proper conversation storage',
                'parameters': {
                    'import_path': {'type': 'string', 'required': True, 'description': 'Path to import folder containing JSON files'}
                },
                'handler': self.import_claude_data
            },
            {
                'name': 'store_direct_instruction',
                'description': 'Store direct instructions for Claude to remember',
                'parameters': {
                    'instruction': {'type': 'string', 'required': True, 'description': 'Instruction text'},
                    'category': {'type': 'string', 'required': False, 'description': 'Category of instruction', 'default': 'general'},
                    'priority': {'type': 'integer', 'required': False, 'description': 'Priority level 1-10', 'default': 5}
                },
                'handler': self.store_direct_instruction
            },
            {
                'name': 'auto_create_memory',
                'description': 'Automatically create memories from conversation context',
                'parameters': {
                    'content': {'type': 'string', 'required': True, 'description': 'Content to analyze and create memory from'},
                    'context': {'type': 'string', 'required': False, 'description': 'Additional context'}
                },
                'handler': self.auto_create_memory
            },
            {
                'name': 'import_har_file',
                'description': 'Import conversation data from HAR (HTTP Archive) files',
                'parameters': {
                    'har_file_path': {'type': 'string', 'required': True, 'description': 'Path to HAR file'}
                },
                'handler': self.import_har_file
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

    def import_claude_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import Claude conversation data into proper conversation storage"""
        import_path = params.get('import_path', '')

        try:
            import os
            import asyncpg
            import asyncio
            import uuid

            # Check if import path exists
            if not os.path.exists(import_path):
                return {
                    'success': False,
                    'error': f'Import path not found: {import_path}'
                }

            # Get database connection string
            db_url = f"postgresql://{os.getenv('POSTGRES_USER', 'centre_ai')}:{os.getenv('POSTGRES_PASSWORD', 'centre_ai_password')}@{os.getenv('POSTGRES_HOST', 'postgres')}:5432/{os.getenv('POSTGRES_DB', 'centre_ai')}"

            async def run_import():
                conn = await asyncpg.connect(db_url)

                results = {
                    'success': True,
                    'imported_files': [],
                    'errors': [],
                    'total_conversations': 0,
                    'total_projects': 0
                }

                # Import conversations into conversations table
                conv_file = os.path.join(import_path, 'conversationsclaude.json')
                if os.path.exists(conv_file):
                    try:
                        with open(conv_file, 'r', encoding='utf-8') as f:
                            conv_data = json.load(f)

                        conv_imported = 0
                        for conv in conv_data:
                            try:
                                # Use original UUID with prefix to avoid conflicts
                                session_id = f"claude_import_{conv.get('uuid', str(uuid.uuid4()))}"

                                # Count messages
                                message_count = len(conv.get('chat_messages', []))

                                # Insert into conversations table
                                conversation_id = await conn.fetchval("""
                                    INSERT INTO conversations (session_id, title, summary, participants, message_count, metadata)
                                    VALUES ($1, $2, $3, $4, $5, $6)
                                    RETURNING id
                                """,
                                session_id,
                                conv.get('name', 'Imported Conversation'),
                                conv.get('summary', 'Imported from Claude export')[:500] if conv.get('summary') else 'Imported from Claude export',
                                ['claude', 'user'],
                                message_count,
                                json.dumps({
                                    'source': 'claude_export',
                                    'original_id': conv.get('uuid', ''),
                                    'created_at': conv.get('created_at', ''),
                                    'updated_at': conv.get('updated_at', '')
                                }))

                                # Insert messages into messages table if they exist
                                if 'chat_messages' in conv and conv['chat_messages']:
                                    for i, msg in enumerate(conv['chat_messages']):
                                        await conn.execute("""
                                            INSERT INTO messages (conversation_id, role, content, metadata)
                                            VALUES ($1, $2, $3, $4)
                                        """,
                                        conversation_id,
                                        msg.get('sender', 'user'),
                                        msg.get('text', '')[:10000],  # Limit content length
                                        json.dumps({
                                            'sequence': i,
                                            'original_data': {k: v for k, v in msg.items() if k != 'text'},
                                            'source': 'claude_export'
                                        }))

                                conv_imported += 1
                                if conv_imported % 50 == 0:  # Progress indicator
                                    print(f"Imported {conv_imported} conversations...")

                            except Exception as e:
                                results['errors'].append(f'Error importing conversation {conv.get("uuid", "unknown")}: {str(e)}')
                                continue

                        results['total_conversations'] = conv_imported
                        results['imported_files'].append('conversationsclaude.json')

                    except Exception as e:
                        results['errors'].append(f'Error importing conversations: {str(e)}')

                # Import projects into conversations with project type
                proj_file = os.path.join(import_path, 'projects.json')
                if os.path.exists(proj_file):
                    try:
                        with open(proj_file, 'r', encoding='utf-8') as f:
                            proj_data = json.load(f)

                        proj_imported = 0
                        for proj in proj_data:
                            try:
                                # Use original UUID with prefix for projects
                                session_id = f"claude_project_{proj.get('uuid', str(uuid.uuid4()))}"

                                await conn.execute("""
                                    INSERT INTO conversations (session_id, title, summary, participants, message_count, metadata)
                                    VALUES ($1, $2, $3, $4, $5, $6)
                                """,
                                session_id,
                                f"[PROJECT] {proj.get('name', 'Imported Project')}",
                                proj.get('description', 'Project imported from Claude export')[:500] if proj.get('description') else 'Project imported from Claude export',
                                ['claude', 'user'],
                                0,  # Projects don't have messages
                                json.dumps({
                                    'source': 'claude_export',
                                    'type': 'project',
                                    'original_id': proj.get('uuid', ''),
                                    'created_at': proj.get('created_at', '')
                                }))

                                proj_imported += 1

                            except Exception as e:
                                results['errors'].append(f'Error importing project {proj.get("uuid", "unknown")}: {str(e)}')
                                continue

                        results['total_projects'] = proj_imported
                        results['imported_files'].append('projects.json')

                    except Exception as e:
                        results['errors'].append(f'Error importing projects: {str(e)}')

                await conn.close()
                return results

            return asyncio.run(run_import())

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def store_direct_instruction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Store direct instructions for Claude"""
        instruction = params.get('instruction', '')
        category = params.get('category', 'general')
        priority = params.get('priority', 5)

        try:
            import os
            import asyncpg
            import asyncio

            db_url = f"postgresql://{os.getenv('POSTGRES_USER', 'centre_ai')}:{os.getenv('POSTGRES_PASSWORD', 'centre_ai_password')}@{os.getenv('POSTGRES_HOST', 'postgres')}:5432/{os.getenv('POSTGRES_DB', 'centre_ai')}"

            async def store_instruction():
                conn = await asyncpg.connect(db_url)

                await conn.execute("""
                    INSERT INTO memories (content, memory_type, importance, tags, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                """, instruction, 'instruction', priority, [category, 'claude_instruction'], json.dumps({
                    'type': 'direct_instruction',
                    'category': category,
                    'priority': priority
                }))

                await conn.close()
                return {
                    'success': True,
                    'message': f'Instruction stored with priority {priority}'
                }

            return asyncio.run(store_instruction())

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def auto_create_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically create memories from conversation context"""
        content = params.get('content', '')
        context = params.get('context', '')

        try:
            import os
            import asyncpg
            import asyncio

            # Simple memory extraction logic - could be enhanced with AI
            if len(content) < 50:
                return {'success': False, 'error': 'Content too short for memory creation'}

            # Extract key information (simplified)
            memory_content = content[:200] + "..." if len(content) > 200 else content

            db_url = f"postgresql://{os.getenv('POSTGRES_USER', 'centre_ai')}:{os.getenv('POSTGRES_PASSWORD', 'centre_ai_password')}@{os.getenv('POSTGRES_HOST', 'postgres')}:5432/{os.getenv('POSTGRES_DB', 'centre_ai')}"

            async def create_memory():
                conn = await asyncpg.connect(db_url)

                await conn.execute("""
                    INSERT INTO memories (content, memory_type, importance, tags, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                """, memory_content, 'auto_generated', 5, ['auto', 'conversation'], json.dumps({
                    'type': 'auto_memory',
                    'context': context,
                    'source_length': len(content)
                }))

                await conn.close()
                return {
                    'success': True,
                    'memory_created': memory_content
                }

            return asyncio.run(create_memory())

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
