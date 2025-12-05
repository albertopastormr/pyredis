"""Integration tests for TTL (Time To Live) functionality."""

import pytest
import time

from app.handler import execute_command
from app.resp import RESPEncoder


class TestTTLIntegration:
    """Test TTL with PX parameter."""
    
    def test_set_with_px_expires(self):
        """SET with PX causes key to expire."""
        # SET with 100ms TTL
        execute_command(['SET', 'tempkey', 'tempvalue', 'PX', '100'])
        
        # Should exist immediately
        result = execute_command(['GET', 'tempkey'])
        assert result == 'tempvalue'
        
        # Wait for expiration
        time.sleep(0.15)  # 150ms
        
        # Should be expired
        result = execute_command(['GET', 'tempkey'])
        assert result is None
    
    def test_set_with_px_before_expiration(self):
        """GET before expiration returns value."""
        execute_command(['SET', 'key', 'value', 'PX', '2000'])
        
        # Check immediately
        assert execute_command(['GET', 'key']) == 'value'
        
        # Check after 500ms (still valid)
        time.sleep(0.5)
        assert execute_command(['GET', 'key']) == 'value'
    
    def test_set_without_px_no_expiration(self):
        """SET without PX doesn't expire."""
        execute_command(['SET', 'permanent', 'value'])
        
        time.sleep(0.2)
        
        result = execute_command(['GET', 'permanent'])
        assert result == 'value'
    
    def test_set_overwrite_removes_ttl(self):
        """SET without PX removes previous TTL."""
        # Set with TTL
        execute_command(['SET', 'key', 'value1', 'PX', '100'])
        
        # Overwrite without TTL
        execute_command(['SET', 'key', 'value2'])
        
        # Wait past original TTL
        time.sleep(0.15)
        
        # Should still exist
        result = execute_command(['GET', 'key'])
        assert result == 'value2'
    
    def test_set_with_px_updates_ttl(self):
        """SET with new PX updates expiration."""
        # Set with short TTL
        execute_command(['SET', 'key', 'value1', 'PX', '100'])
        
        # Immediately reset with longer TTL
        execute_command(['SET', 'key', 'value2', 'PX', '2000'])
        
        # Wait past first TTL
        time.sleep(0.15)
        
        # Should still exist (new TTL)
        result = execute_command(['GET', 'key'])
        assert result == 'value2'
    
    def test_px_invalid_milliseconds(self):
        """SET with invalid PX value raises error."""
        with pytest.raises(ValueError, match="not an integer"):
            execute_command(['SET', 'key', 'value', 'PX', 'abc'])
        
        with pytest.raises(ValueError, match="invalid expire time"):
            execute_command(['SET', 'key', 'value', 'PX', '-1'])
        
        with pytest.raises(ValueError, match="invalid expire time"):
            execute_command(['SET', 'key', 'value', 'PX', '0'])
    
    def test_px_syntax_error(self):
        """SET with wrong PX syntax raises error."""
        # Missing milliseconds
        with pytest.raises(ValueError):
            execute_command(['SET', 'key', 'value', 'PX'])
        
        # Wrong parameter name
        with pytest.raises(ValueError, match="syntax error"):
            execute_command(['SET', 'key', 'value', 'EX', '1000'])
    
    def test_expired_key_returns_nil_resp(self):
        """Expired key returns nil in RESP format."""
        execute_command(['SET', 'key', 'value', 'PX', '50'])
        time.sleep(0.1)
        
        result = execute_command(['GET', 'key'])
        response = RESPEncoder.encode(result)
        
        # Should be null bulk string
        assert response == b"$-1\r\n"
