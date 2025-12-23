"""
CBOR Encoding/Decoding for Bundle Protocol Version 7

Implements Concise Binary Object Representation per RFC 8949
with deterministic encoding requirements per RFC 9171.

Standards:
- RFC 8949: Concise Binary Object Representation (CBOR)
- RFC 9171 Section 4.1: CBOR Encoding Requirements
"""

from typing import Any, List, Tuple, Union, Optional
from enum import IntEnum
import struct


class CBORMajorType(IntEnum):
    """CBOR Major Types (3-bit identifier in initial byte)"""
    UNSIGNED_INT = 0   # 0b000
    NEGATIVE_INT = 1   # 0b001
    BYTE_STRING = 2    # 0b010
    TEXT_STRING = 3    # 0b011
    ARRAY = 4          # 0b100
    MAP = 5            # 0b101
    TAG = 6            # 0b110
    SIMPLE = 7         # 0b111 (floats, booleans, null, undefined, break)


class CBORSimpleValue(IntEnum):
    """CBOR Simple Values"""
    FALSE = 20
    TRUE = 21
    NULL = 22
    UNDEFINED = 23
    BREAK = 31  # "break" stop code for indefinite-length items


# Additional info values for length encoding
AI_ONE_BYTE = 24
AI_TWO_BYTES = 25
AI_FOUR_BYTES = 26
AI_EIGHT_BYTES = 27
AI_INDEFINITE = 31


class CBOREncoder:
    """
    Deterministic CBOR encoder per RFC 8949 and RFC 9171.

    RFC 9171 requires core deterministic encoding with the exception
    that indefinite-length items are permitted (for bundle arrays).
    """

    def __init__(self):
        self._buffer = bytearray()

    def get_bytes(self) -> bytes:
        """Return the encoded CBOR bytes."""
        return bytes(self._buffer)

    def reset(self) -> None:
        """Clear the encoder buffer."""
        self._buffer = bytearray()

    def _encode_head(self, major_type: int, argument: int) -> None:
        """
        Encode CBOR initial byte(s) with major type and argument.

        Uses shortest possible encoding (deterministic requirement).
        """
        mt_shifted = major_type << 5

        if argument < 24:
            # Argument fits in initial byte
            self._buffer.append(mt_shifted | argument)
        elif argument <= 0xFF:
            # One additional byte
            self._buffer.append(mt_shifted | AI_ONE_BYTE)
            self._buffer.append(argument)
        elif argument <= 0xFFFF:
            # Two additional bytes (network byte order)
            self._buffer.append(mt_shifted | AI_TWO_BYTES)
            self._buffer.extend(struct.pack('>H', argument))
        elif argument <= 0xFFFFFFFF:
            # Four additional bytes
            self._buffer.append(mt_shifted | AI_FOUR_BYTES)
            self._buffer.extend(struct.pack('>I', argument))
        else:
            # Eight additional bytes
            self._buffer.append(mt_shifted | AI_EIGHT_BYTES)
            self._buffer.extend(struct.pack('>Q', argument))

    def encode_unsigned_int(self, value: int) -> 'CBOREncoder':
        """Encode an unsigned integer (major type 0)."""
        if value < 0:
            raise ValueError("Value must be non-negative for unsigned int")
        self._encode_head(CBORMajorType.UNSIGNED_INT, value)
        return self

    def encode_negative_int(self, value: int) -> 'CBOREncoder':
        """Encode a negative integer (major type 1)."""
        if value >= 0:
            raise ValueError("Value must be negative")
        # CBOR encodes -1 as 0, -2 as 1, etc.
        self._encode_head(CBORMajorType.NEGATIVE_INT, -1 - value)
        return self

    def encode_int(self, value: int) -> 'CBOREncoder':
        """Encode any integer (chooses major type based on sign)."""
        if value >= 0:
            return self.encode_unsigned_int(value)
        else:
            return self.encode_negative_int(value)

    def encode_bytes(self, data: bytes) -> 'CBOREncoder':
        """Encode a definite-length byte string (major type 2)."""
        self._encode_head(CBORMajorType.BYTE_STRING, len(data))
        self._buffer.extend(data)
        return self

    def encode_text(self, text: str) -> 'CBOREncoder':
        """Encode a definite-length text string (major type 3)."""
        utf8_bytes = text.encode('utf-8')
        self._encode_head(CBORMajorType.TEXT_STRING, len(utf8_bytes))
        self._buffer.extend(utf8_bytes)
        return self

    def encode_array_header(self, length: int) -> 'CBOREncoder':
        """Encode a definite-length array header (major type 4)."""
        self._encode_head(CBORMajorType.ARRAY, length)
        return self

    def encode_indefinite_array_start(self) -> 'CBOREncoder':
        """Start an indefinite-length array (major type 4, AI 31)."""
        self._buffer.append((CBORMajorType.ARRAY << 5) | AI_INDEFINITE)
        return self

    def encode_map_header(self, length: int) -> 'CBOREncoder':
        """Encode a definite-length map header (major type 5)."""
        self._encode_head(CBORMajorType.MAP, length)
        return self

    def encode_break(self) -> 'CBOREncoder':
        """Encode the "break" stop code for indefinite-length items."""
        self._buffer.append((CBORMajorType.SIMPLE << 5) | CBORSimpleValue.BREAK)
        return self

    def encode_bool(self, value: bool) -> 'CBOREncoder':
        """Encode a boolean value."""
        simple = CBORSimpleValue.TRUE if value else CBORSimpleValue.FALSE
        self._buffer.append((CBORMajorType.SIMPLE << 5) | simple)
        return self

    def encode_null(self) -> 'CBOREncoder':
        """Encode null."""
        self._buffer.append((CBORMajorType.SIMPLE << 5) | CBORSimpleValue.NULL)
        return self

    def encode(self, value: Any) -> 'CBOREncoder':
        """
        Encode any Python value to CBOR.

        Supports: int, bytes, str, list, dict, bool, None
        """
        if value is None:
            return self.encode_null()
        elif isinstance(value, bool):
            return self.encode_bool(value)
        elif isinstance(value, int):
            return self.encode_int(value)
        elif isinstance(value, bytes):
            return self.encode_bytes(value)
        elif isinstance(value, str):
            return self.encode_text(value)
        elif isinstance(value, (list, tuple)):
            self.encode_array_header(len(value))
            for item in value:
                self.encode(item)
            return self
        elif isinstance(value, dict):
            # Deterministic: sort keys
            self.encode_map_header(len(value))
            for key in sorted(value.keys(), key=lambda k: CBOREncoder().encode(k).get_bytes()):
                self.encode(key)
                self.encode(value[key])
            return self
        else:
            raise TypeError(f"Cannot encode type {type(value)}")


class CBORDecoder:
    """
    CBOR decoder per RFC 8949.
    """

    def __init__(self, data: bytes):
        self._data = data
        self._pos = 0

    @property
    def remaining(self) -> int:
        """Bytes remaining to decode."""
        return len(self._data) - self._pos

    def _read_byte(self) -> int:
        """Read a single byte."""
        if self._pos >= len(self._data):
            raise ValueError("Unexpected end of CBOR data")
        byte = self._data[self._pos]
        self._pos += 1
        return byte

    def _read_bytes(self, n: int) -> bytes:
        """Read n bytes."""
        if self._pos + n > len(self._data):
            raise ValueError("Unexpected end of CBOR data")
        data = self._data[self._pos:self._pos + n]
        self._pos += n
        return data

    def _decode_argument(self, additional_info: int) -> int:
        """Decode the argument based on additional info."""
        if additional_info < 24:
            return additional_info
        elif additional_info == AI_ONE_BYTE:
            return self._read_byte()
        elif additional_info == AI_TWO_BYTES:
            return struct.unpack('>H', self._read_bytes(2))[0]
        elif additional_info == AI_FOUR_BYTES:
            return struct.unpack('>I', self._read_bytes(4))[0]
        elif additional_info == AI_EIGHT_BYTES:
            return struct.unpack('>Q', self._read_bytes(8))[0]
        elif additional_info == AI_INDEFINITE:
            return -1  # Indicates indefinite length
        else:
            raise ValueError(f"Invalid additional info: {additional_info}")

    def decode(self) -> Any:
        """Decode the next CBOR data item."""
        initial_byte = self._read_byte()
        major_type = initial_byte >> 5
        additional_info = initial_byte & 0x1F

        if major_type == CBORMajorType.UNSIGNED_INT:
            return self._decode_argument(additional_info)

        elif major_type == CBORMajorType.NEGATIVE_INT:
            return -1 - self._decode_argument(additional_info)

        elif major_type == CBORMajorType.BYTE_STRING:
            length = self._decode_argument(additional_info)
            if length < 0:
                raise ValueError("Indefinite byte strings not supported")
            return self._read_bytes(length)

        elif major_type == CBORMajorType.TEXT_STRING:
            length = self._decode_argument(additional_info)
            if length < 0:
                raise ValueError("Indefinite text strings not supported")
            return self._read_bytes(length).decode('utf-8')

        elif major_type == CBORMajorType.ARRAY:
            length = self._decode_argument(additional_info)
            if length < 0:
                # Indefinite-length array
                items = []
                while True:
                    if self._data[self._pos] == 0xFF:  # break code
                        self._pos += 1
                        break
                    items.append(self.decode())
                return items
            else:
                return [self.decode() for _ in range(length)]

        elif major_type == CBORMajorType.MAP:
            length = self._decode_argument(additional_info)
            if length < 0:
                raise ValueError("Indefinite maps not supported")
            result = {}
            for _ in range(length):
                key = self.decode()
                value = self.decode()
                result[key] = value
            return result

        elif major_type == CBORMajorType.SIMPLE:
            if additional_info == CBORSimpleValue.FALSE:
                return False
            elif additional_info == CBORSimpleValue.TRUE:
                return True
            elif additional_info == CBORSimpleValue.NULL:
                return None
            elif additional_info == CBORSimpleValue.BREAK:
                raise ValueError("Unexpected break code")
            else:
                raise ValueError(f"Unknown simple value: {additional_info}")

        else:
            raise ValueError(f"Unknown major type: {major_type}")


def cbor_encode(value: Any) -> bytes:
    """Convenience function to encode a value to CBOR."""
    return CBOREncoder().encode(value).get_bytes()


def cbor_decode(data: bytes) -> Any:
    """Convenience function to decode CBOR data."""
    return CBORDecoder(data).decode()
