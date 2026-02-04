"""RESP (Redis Serialization Protocol) parser and encoder."""

from typing import Any


class RESPParser:
    """Parser for RESP protocol messages."""

    @staticmethod
    def parse(data: bytes):
        """Parse RESP data and return the decoded value."""
        if not data:
            return None

        value, _ = RESPParser._parse_value(data, 0)
        return value

    @staticmethod
    def _parse_value(data: bytes, pos: int):
        """
        Parse a single RESP value starting at position pos.
        Returns (value, new_position).
        """
        if pos >= len(data):
            raise ValueError("Unexpected end of data")

        type_byte = chr(data[pos])
        pos += 1

        if type_byte == "*":
            return RESPParser._parse_array(data, pos)
        elif type_byte == "$":
            return RESPParser._parse_bulk_string(data, pos)
        elif type_byte == "+":
            return RESPParser._parse_simple_string(data, pos)
        elif type_byte == ":":
            return RESPParser._parse_integer(data, pos)
        elif type_byte == "-":
            return RESPParser._parse_error(data, pos)
        else:
            raise ValueError(f"Unknown RESP type: {type_byte}")

    @staticmethod
    def _parse_array(data: bytes, pos: int):
        """Parse RESP array: *<count>\r\n<elements>"""
        count_str, pos = RESPParser._read_until_crlf(data, pos)
        count = int(count_str)

        # Null array
        if count == -1:
            return None, pos

        elements = []
        for _ in range(count):
            value, pos = RESPParser._parse_value(data, pos)
            elements.append(value)

        return elements, pos

    @staticmethod
    def _parse_bulk_string(data: bytes, pos: int):
        """Parse RESP bulk string: $<length>\r\n<data>\r\n"""
        length_str, pos = RESPParser._read_until_crlf(data, pos)
        length = int(length_str)

        if length == -1:
            return None, pos

        # Read the actual string data
        if pos + length > len(data):
            raise ValueError("Bulk string length exceeds data")

        string_data = data[pos : pos + length].decode("utf-8")
        pos += length

        # Skip the trailing \r\n
        pos = RESPParser._expect_crlf(data, pos)

        return string_data, pos

    @staticmethod
    def _parse_simple_string(data: bytes, pos: int):
        """Parse RESP simple string: +<string>\r\n"""
        value, pos = RESPParser._read_until_crlf(data, pos)
        return value, pos

    @staticmethod
    def _parse_integer(data: bytes, pos: int):
        """Parse RESP integer: :<number>\r\n"""
        num_str, pos = RESPParser._read_until_crlf(data, pos)
        return int(num_str), pos

    @staticmethod
    def _parse_error(data: bytes, pos: int):
        """Parse RESP error: -<error message>\r\n"""
        value, pos = RESPParser._read_until_crlf(data, pos)
        return value, pos

    @staticmethod
    def _read_until_crlf(data: bytes, pos: int):
        """
        Read bytes until \r\n and return as string.
        Returns (string, new_position).
        """
        start = pos
        while pos < len(data) - 1:
            if data[pos] == ord("\r") and data[pos + 1] == ord("\n"):
                result = data[start:pos].decode("utf-8")
                return result, pos + 2  # Skip \r\n
            pos += 1

        raise ValueError("CRLF not found")

    @staticmethod
    def _expect_crlf(data: bytes, pos: int):
        """
        Verify and consume \r\n.
        Returns new_position.
        """
        if pos + 1 < len(data) and data[pos] == ord("\r") and data[pos + 1] == ord("\n"):
            return pos + 2
        else:
            raise ValueError(f"Expected CRLF at position {pos}")


class RESPEncoder:
    """Encoder for RESP protocol messages."""

    @staticmethod
    def encode(data: Any) -> bytes:
        """
        Encode Python data to RESP format.

        Args:
            data: Python object to encode

        Returns:
            RESP-encoded bytes
        """
        if data is None:
            # Null bulk string (for GET, etc.)
            return b"$-1\r\n"

        if isinstance(data, bool):
            # Boolean as simple string (true/false)
            return f"${'true' if data else 'false'}\r\n".encode()

        if isinstance(data, int):
            # Integer
            return f":{data}\r\n".encode()

        if isinstance(data, str):
            # Bulk string
            return f"${len(data)}\r\n{data}\r\n".encode()

        if isinstance(data, bytes):
            # Bulk string (bytes)
            return b"$%d\r\n%b\r\n" % (len(data), data)

        if isinstance(data, list):
            # Array
            if len(data) == 0:
                return b"*0\r\n"

            encoded = f"*{len(data)}\r\n".encode()
            for item in data:
                encoded += RESPEncoder.encode(item)
            return encoded

        if isinstance(data, dict):
            # Special handling for responses
            if "ok" in data:
                value = data["ok"]
                if isinstance(value, str):
                    return f"+{value}\r\n".encode()
                return RESPEncoder.encode(value)

            if "error" in data:
                return f"-{data['error']}\r\n".encode()

            # Queued command response (MULTI transaction)
            if "queued" in data:
                value = data["queued"]
                if isinstance(value, str):
                    return f"+{value}\r\n".encode()
                return RESPEncoder.encode(value)

            # Null array marker (for BLPOP timeout)
            if "null_array" in data:
                return b"*-1\r\n"
            
            # FULLRESYNC response with RDB file (for PSYNC)
            if "fullresync" in data:
                fullresync_data = data["fullresync"]
                replid = fullresync_data["replid"]
                offset = fullresync_data["offset"]
                rdb_bytes = fullresync_data["rdb"]
                
                response = f"+FULLRESYNC {replid} {offset}\r\n".encode()
                
                # Followed by RDB file: $<length>\r\n<binary_data>
                # Note: NO trailing \r\n after binary data
                response += f"${len(rdb_bytes)}\r\n".encode()
                response += rdb_bytes
                
                return response

        raise ValueError(f"Unsupported type for RESP encoding: {type(data)}")

    @staticmethod
    def _encode_simple_string(s: str) -> bytes:
        """Encode as RESP simple string: +<string>\r\n"""

    @staticmethod
    def _encode_bulk_string(s: str) -> bytes:
        """Encode as RESP bulk string: $<length>\r\n<data>\r\n"""
        if s is None:
            return b"$-1\r\n"

        length = len(s.encode("utf-8"))
        return f"${length}\r\n{s}\r\n".encode()

    @staticmethod
    def _encode_integer(n: int) -> bytes:
        """Encode as RESP integer: :<number>\r\n"""
        return f":{n}\r\n".encode()

    @staticmethod
    def _encode_error(msg: str) -> bytes:
        """Encode as RESP error: -<error message>\r\n"""
        return f"-{msg}\r\n".encode()

    @staticmethod
    def _encode_array(items: list) -> bytes:
        """Encode as RESP array: *<count>\r\n<elements>"""
        if items is None:
            return b"*-1\r\n"

        result = f"*{len(items)}\r\n".encode()
        for item in items:
            result += RESPEncoder.encode(item)  # Recursive call to public method

        return result
