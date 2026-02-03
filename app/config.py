"""Server configuration - stores global server settings."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Role(str, Enum):
    """Server role in replication."""

    MASTER = "master"
    SLAVE = "slave"


@dataclass
class ReplicationConfig:
    """Replication configuration for the server."""

    role: Role
    master_host: Optional[str] = None
    master_port: Optional[int] = None
    master_replid: str = "8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb"
    master_repl_offset: int = 0

    def is_master(self) -> bool:
        """Check if this server is a master."""
        return self.role == Role.MASTER

    def is_slave(self) -> bool:
        """Check if this server is a slave/replica."""
        return self.role == Role.SLAVE


class ServerConfig:
    """
    Global server configuration singleton.

    Stores server-wide settings that need to be accessed from various parts
    of the application, such as replication configuration.
    """

    _instance: Optional["ServerConfig"] = None
    _replication: ReplicationConfig
    _listening_port: int = 6379  # Default port

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Default to master role
            cls._instance._replication = ReplicationConfig(role=Role.MASTER)
            cls._instance._listening_port = 6379
        return cls._instance

    @classmethod
    def initialize(
        cls,
        role: Role = Role.MASTER,
        master_host: Optional[str] = None,
        master_port: Optional[int] = None,
        listening_port: int = 6379,
    ) -> None:
        """
        Initialize the server configuration.

        Args:
            role: Server role (Role.MASTER or Role.SLAVE)
            master_host: Master server host (for replicas)
            master_port: Master server port (for replicas)
            listening_port: Port this server is listening on
        """
        instance = cls()
        instance._replication = ReplicationConfig(
            role=role,
            master_host=master_host,
            master_port=master_port,
        )
        instance._listening_port = listening_port

    @classmethod
    def get_replication_config(cls) -> ReplicationConfig:
        """
        Get the current replication configuration.

        Returns:
            Current replication configuration
        """
        instance = cls()
        return instance._replication

    @classmethod
    def get_listening_port(cls) -> int:
        """
        Get the port this server is listening on.

        Returns:
            Listening port number
        """
        instance = cls()
        return instance._listening_port

    @classmethod
    def reset(cls) -> None:
        """Reset configuration to default (useful for testing)."""
        cls._instance = None
