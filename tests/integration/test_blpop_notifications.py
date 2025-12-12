"""Integration tests for BLPOP notification behavior with multiple waiters."""

import pytest
import asyncio
import time

from tests.helpers import execute_command
from app.handler import execute_command as async_execute_command


class TestBlpopNotificationCount:
    """Test that BLPOP waiters are notified proportionally to available elements."""
    
    def test_rpush_one_element_wakes_one_waiter(self):
        """RPUSH with 1 element should wake only 1 waiter."""
        async def test():
            # Start 3 BLPOP waiters
            waiters = [
                asyncio.create_task(async_execute_command(['BLPOP', 'mylist', '2'])),
                asyncio.create_task(async_execute_command(['BLPOP', 'mylist', '2'])),
                asyncio.create_task(async_execute_command(['BLPOP', 'mylist', '2']))
            ]
            
            # Give them time to register
            await asyncio.sleep(0.1)
            
            # Push ONE element
            await async_execute_command(['RPUSH', 'mylist', 'value1'])
            
            # Give time for notification
            await asyncio.sleep(0.1)
            
            # Check status - only first should complete
            assert waiters[0].done()
            assert not waiters[1].done()
            assert not waiters[2].done()
            
            # Verify result
            result = await waiters[0]
            assert result == ['mylist', 'value1']
            
            # Cancel remaining
            for w in waiters[1:]:
                w.cancel()
                try:
                    await w
                except asyncio.CancelledError:
                    pass
        
        asyncio.run(test())
    
    def test_rpush_multiple_elements_wakes_multiple_waiters(self):
        """RPUSH with 3 elements should wake 3 waiters."""
        async def test():
            # Start 5 BLPOP waiters
            waiters = [
                asyncio.create_task(async_execute_command(['BLPOP', 'mylist', '2']))
                for _ in range(5)
            ]
            
            await asyncio.sleep(0.1)
            
            # Push THREE elements
            await async_execute_command(['RPUSH', 'mylist', 'a', 'b', 'c'])
            
            await asyncio.sleep(0.1)
            
            # First 3 should complete
            assert waiters[0].done()
            assert waiters[1].done()
            assert waiters[2].done()
            assert not waiters[3].done()
            assert not waiters[4].done()
            
            # Verify they got different values
            results = [await waiters[i] for i in range(3)]
            values = [r[1] for r in results]
            assert set(values) == {'a', 'b', 'c'}
            
            # Cancel remaining
            for w in waiters[3:]:
                w.cancel()
                try:
                    await w
                except asyncio.CancelledError:
                    pass
        
        asyncio.run(test())
    
    def test_rpush_more_elements_than_waiters(self):
        """RPUSH with 5 elements but only 2 waiters - both wake up."""
        async def test():
            # Start only 2 waiters
            waiters = [
                asyncio.create_task(async_execute_command(['BLPOP', 'mylist', '2'])),
                asyncio.create_task(async_execute_command(['BLPOP', 'mylist', '2']))
            ]
            
            await asyncio.sleep(0.1)
            
            # Push FIVE elements
            await async_execute_command(['RPUSH', 'mylist', '1', '2', '3', '4', '5'])
            
            await asyncio.sleep(0.1)
            
            # Both should complete
            assert waiters[0].done()
            assert waiters[1].done()
            
            # Remaining elements should still be in list
            remaining = await async_execute_command(['LRANGE', 'mylist', '0', '-1'])
            assert len(remaining) == 3  # 5 - 2 = 3 left
        
        asyncio.run(test())
    
    def test_lpush_notifies_proportionally(self):
        """LPUSH should also notify proportional number of waiters."""
        async def test():
            # Start 4 waiters
            waiters = [
                asyncio.create_task(async_execute_command(['BLPOP', 'mylist', '2']))
                for _ in range(4)
            ]
            
            await asyncio.sleep(0.1)
            
            # LPUSH 2 elements
            await async_execute_command(['LPUSH', 'mylist', 'x', 'y'])
            
            await asyncio.sleep(0.1)
            
            # First 2 should complete
            assert waiters[0].done()
            assert waiters[1].done()
            assert not waiters[2].done()
            assert not waiters[3].done()
            
            # Cancel remaining
            for w in waiters[2:]:
                w.cancel()
                try:
                    await w
                except asyncio.CancelledError:
                    pass
        
        asyncio.run(test())
    
    def test_sequential_pushes_wake_waiters_incrementally(self):
        """Sequential RPUSHes should wake waiters one by one."""
        async def test():
            # Start 3 waiters
            waiters = [
                asyncio.create_task(async_execute_command(['BLPOP', 'mylist', '2']))
                for _ in range(3)
            ]
            
            await asyncio.sleep(0.1)
            
            # Push one element
            await async_execute_command(['RPUSH', 'mylist', 'first'])
            await asyncio.sleep(0.05)
            
            # Only first waiter should complete
            assert waiters[0].done()
            assert not waiters[1].done()
            assert not waiters[2].done()
            
            # Push another
            await async_execute_command(['RPUSH', 'mylist', 'second'])
            await asyncio.sleep(0.05)
            
            # Second should complete
            assert waiters[1].done()
            assert not waiters[2].done()
            
            # Push third
            await async_execute_command(['RPUSH', 'mylist', 'third'])
            await asyncio.sleep(0.05)
            
            # All should complete
            assert waiters[2].done()
        
        asyncio.run(test())
    
    def test_no_waiters_all_elements_remain(self):
        """RPUSH with no waiters should keep all elements in list."""
        # No waiters - just push
        result = execute_command(['RPUSH', 'mylist', '1', '2', '3', '4', '5'])
        assert result == 5
        
        # All elements should be there
        elements = execute_command(['LRANGE', 'mylist', '0', '-1'])
        assert elements == ['1', '2', '3', '4', '5']
    
    def test_mixed_rpush_lpush_notifications(self):
        """Mix of RPUSH and LPUSH should notify correctly."""
        async def test():
            # Start 4 waiters
            waiters = [
                asyncio.create_task(async_execute_command(['BLPOP', 'mylist', '2']))
                for _ in range(4)
            ]
            
            await asyncio.sleep(0.1)
            
            # RPUSH 2 elements - wakes 2
            await async_execute_command(['RPUSH', 'mylist', 'r1', 'r2'])
            await asyncio.sleep(0.05)
            
            assert waiters[0].done()
            assert waiters[1].done()
            assert not waiters[2].done()
            assert not waiters[3].done()
            
            # LPUSH 2 more - wakes remaining 2
            await async_execute_command(['LPUSH', 'mylist', 'l1', 'l2'])
            await asyncio.sleep(0.05)
            
            assert waiters[2].done()
            assert waiters[3].done()
        
        asyncio.run(test())


class TestBlpopNotificationEdgeCases:
    """Edge cases for BLPOP notification counting."""
    
    def test_waiter_registers_after_push(self):
        """Waiter arriving after RPUSH should get element immediately."""
        async def test():
            # Push first
            await async_execute_command(['RPUSH', 'mylist', 'already_there'])
            
            # Then wait
            result = await async_execute_command(['BLPOP', 'mylist', '1'])
            
            assert result == ['mylist', 'already_there']
        
        asyncio.run(test())
    
    def test_notification_count_matches_added_elements(self):
        """Notified count should match number of elements added."""
        from app.blocking import get_waiter_count
        
        async def test():
            # Start 10 waiters
            waiters = [
                asyncio.create_task(async_execute_command(['BLPOP', 'mylist', '5']))
                for _ in range(10)
            ]
            
            await asyncio.sleep(0.1)
            
            # Verify 10 waiting
            assert get_waiter_count('mylist') == 10
            
            # Add 3 elements
            await async_execute_command(['RPUSH', 'mylist', 'a', 'b', 'c'])
            await asyncio.sleep(0.1)
            
            # 3 should complete, 7 still waiting
            completed = sum(1 for w in waiters if w.done())
            assert completed == 3
            
            # Cancel remaining
            for w in waiters:
                if not w.done():
                    w.cancel()
                    try:
                        await w
                    except asyncio.CancelledError:
                        pass
        
        asyncio.run(test())
