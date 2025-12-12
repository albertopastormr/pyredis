"""PING command implementation."""

from typing import Any, List
from .base import BaseCommand


class PingCommand(BaseCommand):
    """
    PING command - Tests server connectivity.
    
    Returns PONG if no argument is provided, otherwise returns the argument.
    """
    
    @property
    def name(self) -> str:
        return "PING"
    
    async def execute(self, args: List[str]) -> Any:
        """
        Execute PING command.
        
        Args:
            args: Optional message to echo back
        
        Returns:
            'PONG' if no args, otherwise the first argument
        """
        self.validate_args(args, min_args=0, max_args=1)
        
        if args:
            # PING with message returns the message
            return args[0]
        else:
            # PING without message returns simple string PONG
            return {'ok': 'PONG'}
