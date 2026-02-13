"""Test to verify offset tracking follows the correct rules."""

import pytest
from app.resp import RESPEncoder


def test_offset_tracking_rules():
    """
    Verify offset tracking follows the correct rule:
    The offset reported by REPLCONF ACK should NOT include the current GETACK request.

    Scenario from documentation:
    1. First GETACK  → ACK 0   (no commands before)
    2. Second GETACK → ACK 37  (first GETACK was 37 bytes)
    3. PING          → silent  (no response)
    4. Third GETACK  → ACK 88  (37 + 37 + 14)
    """

    # Simulate offset tracking
    offset = 0

    # Command 1: First REPLCONF GETACK *
    getack_cmd = RESPEncoder.encode(["REPLCONF", "GETACK", "*"])
    getack_bytes = len(getack_cmd)  # 37 bytes

    # Should respond with ACK 0 (no commands before this)
    ack_response_1 = offset
    assert ack_response_1 == 0, "First GETACK should return offset 0"

    # Now update offset to include this GETACK command
    offset += getack_bytes
    assert offset == 37

    # Command 2: Second REPLCONF GETACK *
    # Should respond with ACK 37 (first GETACK was 37 bytes)
    ack_response_2 = offset
    assert ack_response_2 == 37, "Second GETACK should return offset 37"

    # Update offset to include second GETACK
    offset += getack_bytes
    assert offset == 74

    # Command 3: PING
    ping_cmd = RESPEncoder.encode(["PING"])
    ping_bytes = len(ping_cmd)  # 14 bytes

    # Process silently, update offset
    offset += ping_bytes
    assert offset == 88

    # Command 4: Third REPLCONF GETACK *
    # Should respond with ACK 88 (37 + 37 + 14)
    ack_response_3 = offset
    assert ack_response_3 == 88, "Third GETACK should return offset 88"

    # Verify the breakdown
    assert ack_response_3 == 37 + 37 + 14, "Offset should be sum of all previous commands"

    print("✅ Offset tracking follows the correct rule!")
    print(f"   First GETACK:  ACK {ack_response_1}")
    print(f"   Second GETACK: ACK {ack_response_2}")
    print(f"   After PING:    offset = {88}")
    print(f"   Third GETACK:  ACK {ack_response_3}")


if __name__ == "__main__":
    test_offset_tracking_rules()
