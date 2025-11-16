"""
Tests for MemoryStore module
"""

import pytest
import time
from datetime import datetime, timedelta
from src.memory.store import MemoryStore


class TestMemoryStore:
    """Test suite for MemoryStore"""

    @pytest.fixture
    def store(self, temp_db_path):
        """Create MemoryStore instance with temp database"""
        return MemoryStore(db_path=temp_db_path)

    @pytest.fixture
    def populated_store(self, store):
        """Create store with some test data"""
        store.store('key1', 'value1', 'user1', tags=['tag1'])
        store.store('key2', {'nested': 'data'}, 'user1', tags=['tag1', 'tag2'])
        store.store('key3', [1, 2, 3], 'user2', tags=['tag2'])
        return store

    def test_store_basic(self, store):
        """Test basic storage"""
        result = store.store('test_key', 'test_value', 'user1')
        assert result['success'] is True
        assert result['key'] == 'test_key'
        assert 'stored_at' in result

    def test_store_dict_value(self, store):
        """Test storing dictionary values"""
        result = store.store('dict_key', {'name': 'test', 'value': 123}, 'user1')
        assert result['success'] is True

    def test_store_list_value(self, store):
        """Test storing list values"""
        result = store.store('list_key', [1, 2, 3, 'four'], 'user1')
        assert result['success'] is True

    def test_store_with_tags(self, store):
        """Test storing with tags"""
        result = store.store('tagged_key', 'value', 'user1', tags=['important', 'test'])
        assert result['success'] is True

    def test_store_with_ttl(self, store):
        """Test storing with TTL"""
        result = store.store('ttl_key', 'value', 'user1', ttl=3600)
        assert result['success'] is True

    def test_store_update_existing(self, store):
        """Test updating existing key"""
        store.store('key', 'value1', 'user1')
        result = store.store('key', 'value2', 'user1')
        assert result['success'] is True

        retrieved = store.retrieve('key', 'user1')
        assert retrieved['value'] == 'value2'

    def test_retrieve_basic(self, populated_store):
        """Test basic retrieval"""
        result = populated_store.retrieve('key1', 'user1')
        assert result['success'] is True
        assert result['value'] == 'value1'
        assert result['key'] == 'key1'
        assert 'created_at' in result

    def test_retrieve_dict_value(self, populated_store):
        """Test retrieving dictionary values"""
        result = populated_store.retrieve('key2', 'user1')
        assert result['success'] is True
        assert result['value'] == {'nested': 'data'}

    def test_retrieve_list_value(self, populated_store):
        """Test retrieving list values"""
        result = populated_store.retrieve('key3', 'user2')
        assert result['success'] is True
        assert result['value'] == [1, 2, 3]

    def test_retrieve_with_tags(self, populated_store):
        """Test tags are retrieved correctly"""
        result = populated_store.retrieve('key2', 'user1')
        assert result['success'] is True
        assert 'tag1' in result['tags']
        assert 'tag2' in result['tags']

    def test_retrieve_not_found(self, store):
        """Test retrieving non-existent key"""
        result = store.retrieve('nonexistent', 'user1')
        assert result['success'] is False
        assert 'not found' in result['error']

    def test_retrieve_wrong_user(self, populated_store):
        """Test retrieving key with wrong user"""
        result = populated_store.retrieve('key1', 'wrong_user')
        assert result['success'] is False

    def test_retrieve_expired(self, store):
        """Test retrieving expired key"""
        # Store with 1 second TTL
        store.store('expire_key', 'value', 'user1', ttl=1)

        # Wait for expiration
        time.sleep(1.5)

        result = store.retrieve('expire_key', 'user1')
        assert result['success'] is False
        assert 'expired' in result['error']

    def test_delete_basic(self, populated_store):
        """Test basic deletion"""
        result = populated_store.delete('key1', 'user1')
        assert result['success'] is True
        assert result['key'] == 'key1'

        # Verify deletion
        retrieve_result = populated_store.retrieve('key1', 'user1')
        assert retrieve_result['success'] is False

    def test_delete_not_found(self, store):
        """Test deleting non-existent key"""
        result = store.delete('nonexistent', 'user1')
        assert result['success'] is False

    def test_delete_wrong_user(self, populated_store):
        """Test deleting key with wrong user"""
        result = populated_store.delete('key1', 'wrong_user')
        assert result['success'] is False

    def test_search_by_tags_single(self, populated_store):
        """Test searching by single tag"""
        result = populated_store.search_by_tags(['tag1'], 'user1')
        assert result['success'] is True
        assert result['count'] == 2

    def test_search_by_tags_multiple(self, populated_store):
        """Test searching by multiple tags"""
        result = populated_store.search_by_tags(['tag2'], 'user1')
        assert result['success'] is True
        assert result['count'] == 1

    def test_search_by_tags_no_match(self, populated_store):
        """Test searching with no matches"""
        result = populated_store.search_by_tags(['nonexistent'], 'user1')
        assert result['success'] is True
        assert result['count'] == 0

    def test_search_by_tags_user_specific(self, populated_store):
        """Test that search is user-specific"""
        result = populated_store.search_by_tags(['tag2'], 'user2')
        assert result['success'] is True
        assert result['count'] == 1

    def test_list_all_basic(self, populated_store):
        """Test listing all memories"""
        result = populated_store.list_all('user1')
        assert result['success'] is True
        assert result['count'] == 2

    def test_list_all_user_specific(self, populated_store):
        """Test listing is user-specific"""
        result = populated_store.list_all('user2')
        assert result['success'] is True
        assert result['count'] == 1

    def test_list_all_empty(self, store):
        """Test listing empty store"""
        result = store.list_all('user1')
        assert result['success'] is True
        assert result['count'] == 0

    def test_list_all_with_limit(self, store):
        """Test listing with limit"""
        # Add many items
        for i in range(10):
            store.store(f'key{i}', f'value{i}', 'user1')

        result = store.list_all('user1', limit=5)
        assert result['count'] == 5

    def test_count_empty(self, store):
        """Test count on empty store"""
        count = store.count()
        assert count == 0

    def test_count_with_data(self, populated_store):
        """Test count with data"""
        count = populated_store.count()
        assert count == 3

    def test_count_after_delete(self, populated_store):
        """Test count after deletion"""
        initial_count = populated_store.count()
        populated_store.delete('key1', 'user1')
        new_count = populated_store.count()
        assert new_count == initial_count - 1

    def test_get_stats_empty(self, store):
        """Test stats on empty store"""
        stats = store.get_stats()
        assert stats['total_memories'] == 0
        assert stats['unique_users'] == 0
        assert 'db_path' in stats

    def test_get_stats_with_data(self, populated_store):
        """Test stats with data"""
        stats = populated_store.get_stats()
        assert stats['total_memories'] == 3
        assert stats['unique_users'] == 2

    def test_cleanup_expired(self, store):
        """Test cleaning up expired memories"""
        # Store with short TTL
        store.store('expire1', 'value', 'user1', ttl=1)
        store.store('expire2', 'value', 'user1', ttl=1)
        store.store('keep', 'value', 'user1')  # No TTL

        time.sleep(1.5)

        deleted = store.cleanup_expired()
        assert deleted == 2

        # Verify non-expired still exists
        result = store.retrieve('keep', 'user1')
        assert result['success'] is True

    def test_cleanup_expired_none(self, populated_store):
        """Test cleanup when nothing is expired"""
        deleted = populated_store.cleanup_expired()
        assert deleted == 0

    def test_unicode_keys_and_values(self, store):
        """Test unicode support"""
        store.store('日本語', {'text': 'こんにちは'}, 'user1')
        result = store.retrieve('日本語', 'user1')
        assert result['success'] is True
        assert result['value']['text'] == 'こんにちは'

    def test_large_value(self, store):
        """Test storing large values"""
        large_data = {'data': 'x' * 10000}
        store.store('large', large_data, 'user1')
        result = store.retrieve('large', 'user1')
        assert result['success'] is True
        assert len(result['value']['data']) == 10000

    def test_concurrent_access(self, store):
        """Test multiple operations"""
        # Simulate concurrent-like access
        for i in range(100):
            store.store(f'key{i}', f'value{i}', 'user1')

        count = store.count()
        assert count == 100

        # Verify random access
        result = store.retrieve('key50', 'user1')
        assert result['value'] == 'value50'
