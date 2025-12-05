"""RESP (Redis Serialization Protocol) parser and encoder."""


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
        
        if type_byte == '*':
            return RESPParser._parse_array(data, pos)
        elif type_byte == '$':
            return RESPParser._parse_bulk_string(data, pos)
        elif type_byte == '+':
            return RESPParser._parse_simple_string(data, pos)
        elif type_byte == ':':
            return RESPParser._parse_integer(data, pos)
        elif type_byte == '-':
            return RESPParser._parse_error(data, pos)
        else:
            raise ValueError(f"Unknown RESP type: {type_byte}")
    
    @staticmethod
    def _parse_array(data: bytes, pos: int):
        """Parse RESP array: *<count>\r\n<elements>"""
        count_str, pos = RESPParser._read_until_crlf(data, pos)
        count = int(count_str)
        
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
        
        string_data = data[pos:pos + length].decode('utf-8')
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
            if data[pos] == ord('\r') and data[pos + 1] == ord('\n'):
                result = data[start:pos].decode('utf-8')
                return result, pos + 2  # Skip \r\n
            pos += 1
        
        raise ValueError("CRLF not found")
    
    @staticmethod
    def _expect_crlf(data: bytes, pos: int):
        """
        Verify and consume \r\n.
        Returns new_position.
        """
        if pos + 1 < len(data) and \
           data[pos] == ord('\r') and \
           data[pos + 1] == ord('\n'):
            return pos + 2
        else:
            raise ValueError(f"Expected CRLF at position {pos}")


class RESPEncoder:
    """Encoder for RESP protocol messages."""
    
    @staticmethod
    def encode(value) -> bytes:
        """
        Encode a Python value to RESP format.
        Automatically determines the appropriate RESP type.
        
        Supported types:
        - str → Bulk String ($3\\r\\nhey\\r\\n)
        - int → Integer (:42\\r\\n)
        - list → Array (*2\\r\\n...)
        - None → Null Bulk String ($-1\\r\\n)
        - dict with 'error' key → Error (-ERR message\\r\\n)
        - dict with 'ok' key → Simple String (+OK\\r\\n)
        """
        if value is None:
            return RESPEncoder._encode_bulk_string(None)
        
        elif isinstance(value, str):
            return RESPEncoder._encode_bulk_string(value)
        
        elif isinstance(value, int):
            return RESPEncoder._encode_integer(value)
        
        elif isinstance(value, list):
            return RESPEncoder._encode_array(value)
        
        elif isinstance(value, dict):
            # Special dict formats for control
            if 'error' in value:
                return RESPEncoder._encode_error(value['error'])
            elif 'ok' in value:
                return RESPEncoder._encode_simple_string(value['ok'])
            else:
                raise ValueError(f"Unsupported dict format: {value}")
        
        else:
            raise ValueError(f"Unsupported type for RESP encoding: {type(value)}")
    
    @staticmethod
    def _encode_simple_string(s: str) -> bytes:
        """Encode as RESP simple string: +<string>\r\n"""
        return f"+{s}\r\n".encode('utf-8')
    
    @staticmethod
    def _encode_bulk_string(s: str) -> bytes:
        """Encode as RESP bulk string: $<length>\r\n<data>\r\n"""
        if s is None:
            return b"$-1\r\n"
        
        length = len(s.encode('utf-8'))
        return f"${length}\r\n{s}\r\n".encode('utf-8')
    
    @staticmethod
    def _encode_integer(n: int) -> bytes:
        """Encode as RESP integer: :<number>\r\n"""
        return f":{n}\r\n".encode('utf-8')
    
    @staticmethod
    def _encode_error(msg: str) -> bytes:
        """Encode as RESP error: -<error message>\r\n"""
        return f"-{msg}\r\n".encode('utf-8')
    
    @staticmethod
    def _encode_array(items: list) -> bytes:
        """Encode as RESP array: *<count>\r\n<elements>"""
        if items is None:
            return b"*-1\r\n"
        
        result = f"*{len(items)}\r\n".encode('utf-8')
        for item in items:
            result += RESPEncoder.encode(item)  # Recursive call to public method
        
        return result
