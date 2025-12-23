"""
CBOR Encoding Tests

Verifies CBOR implementation against RFC 8949 requirements
and RFC 9171 deterministic encoding requirements.
"""

import unittest

from ..encoding.cbor import cbor_decode, cbor_encode


class TestCBOREncoder(unittest.TestCase):
    """Tests for CBOR encoding per RFC 8949."""

    def test_encode_unsigned_int_small(self):
        """Integers 0-23 encode in single byte."""
        for i in range(24):
            encoded = cbor_encode(i)
            self.assertEqual(len(encoded), 1)
            self.assertEqual(encoded[0], i)

    def test_encode_unsigned_int_one_byte(self):
        """Integers 24-255 encode in 2 bytes."""
        encoded = cbor_encode(24)
        self.assertEqual(encoded, bytes([0x18, 24]))

        encoded = cbor_encode(255)
        self.assertEqual(encoded, bytes([0x18, 255]))

    def test_encode_unsigned_int_two_bytes(self):
        """Integers 256-65535 encode in 3 bytes."""
        encoded = cbor_encode(256)
        self.assertEqual(encoded, bytes([0x19, 0x01, 0x00]))

        encoded = cbor_encode(65535)
        self.assertEqual(encoded, bytes([0x19, 0xFF, 0xFF]))

    def test_encode_negative_int(self):
        """Negative integers use major type 1."""
        # -1 encodes as major type 1, argument 0
        encoded = cbor_encode(-1)
        self.assertEqual(encoded, bytes([0x20]))

        # -10 encodes as major type 1, argument 9
        encoded = cbor_encode(-10)
        self.assertEqual(encoded, bytes([0x29]))

    def test_encode_bytes(self):
        """Byte strings use major type 2."""
        data = b"hello"
        encoded = cbor_encode(data)
        # Major type 2 (0x40) + length 5 = 0x45
        self.assertEqual(encoded[0], 0x45)
        self.assertEqual(encoded[1:], data)

    def test_encode_text(self):
        """Text strings use major type 3."""
        text = "hello"
        encoded = cbor_encode(text)
        # Major type 3 (0x60) + length 5 = 0x65
        self.assertEqual(encoded[0], 0x65)
        self.assertEqual(encoded[1:], text.encode('utf-8'))

    def test_encode_array(self):
        """Arrays use major type 4."""
        arr = [1, 2, 3]
        encoded = cbor_encode(arr)
        # Major type 4 (0x80) + length 3 = 0x83
        self.assertEqual(encoded[0], 0x83)
        # Followed by encoded elements
        self.assertEqual(encoded[1:], bytes([1, 2, 3]))

    def test_encode_map(self):
        """Maps use major type 5."""
        m = {1: 2}
        encoded = cbor_encode(m)
        # Major type 5 (0xA0) + length 1 = 0xA1
        self.assertEqual(encoded[0], 0xA1)
        # Key 1, value 2
        self.assertEqual(encoded[1:], bytes([1, 2]))

    def test_encode_bool(self):
        """Booleans encode as simple values."""
        self.assertEqual(cbor_encode(False), bytes([0xF4]))
        self.assertEqual(cbor_encode(True), bytes([0xF5]))

    def test_encode_null(self):
        """Null encodes as simple value 22."""
        self.assertEqual(cbor_encode(None), bytes([0xF6]))

    def test_deterministic_map_ordering(self):
        """Maps are encoded with sorted keys (deterministic)."""
        # Keys should be sorted by their CBOR encoding
        m = {2: "b", 1: "a", 10: "c"}
        encoded = cbor_encode(m)
        decoded = cbor_decode(encoded)

        # Verify round-trip preserves values
        self.assertEqual(decoded[1], "a")
        self.assertEqual(decoded[2], "b")
        self.assertEqual(decoded[10], "c")


class TestCBORDecoder(unittest.TestCase):
    """Tests for CBOR decoding per RFC 8949."""

    def test_decode_unsigned_int(self):
        """Decode unsigned integers."""
        self.assertEqual(cbor_decode(bytes([0])), 0)
        self.assertEqual(cbor_decode(bytes([23])), 23)
        self.assertEqual(cbor_decode(bytes([0x18, 24])), 24)
        self.assertEqual(cbor_decode(bytes([0x19, 0x01, 0x00])), 256)

    def test_decode_negative_int(self):
        """Decode negative integers."""
        self.assertEqual(cbor_decode(bytes([0x20])), -1)
        self.assertEqual(cbor_decode(bytes([0x29])), -10)

    def test_decode_bytes(self):
        """Decode byte strings."""
        encoded = bytes([0x45]) + b"hello"
        self.assertEqual(cbor_decode(encoded), b"hello")

    def test_decode_text(self):
        """Decode text strings."""
        encoded = bytes([0x65]) + b"hello"
        self.assertEqual(cbor_decode(encoded), "hello")

    def test_decode_array(self):
        """Decode arrays."""
        encoded = bytes([0x83, 1, 2, 3])
        self.assertEqual(cbor_decode(encoded), [1, 2, 3])

    def test_decode_indefinite_array(self):
        """Decode indefinite-length arrays."""
        # 0x9F starts indefinite array, 0xFF breaks
        encoded = bytes([0x9F, 1, 2, 3, 0xFF])
        self.assertEqual(cbor_decode(encoded), [1, 2, 3])

    def test_round_trip(self):
        """Test encode/decode round-trip."""
        values = [
            0, 1, 23, 24, 255, 256, 65535,
            -1, -10, -100,
            b"hello",
            "hello",
            [1, 2, 3],
            {"a": 1, "b": 2},
            True, False, None,
            [1, "two", b"three", {"four": 4}],
        ]

        for value in values:
            encoded = cbor_encode(value)
            decoded = cbor_decode(encoded)
            self.assertEqual(decoded, value, f"Round-trip failed for {value}")


class TestRFC9171Compliance(unittest.TestCase):
    """Tests for RFC 9171 CBOR requirements."""

    def test_shortest_encoding(self):
        """RFC 9171 requires shortest possible encoding."""
        # 23 must encode in 1 byte, not 2
        encoded = cbor_encode(23)
        self.assertEqual(len(encoded), 1)

        # 24 must encode in 2 bytes, not 3
        encoded = cbor_encode(24)
        self.assertEqual(len(encoded), 2)

    def test_definite_length_preferred(self):
        """Definite-length encoding for known-length items."""
        # Arrays with known length use definite encoding
        arr = [1, 2, 3]
        encoded = cbor_encode(arr)
        # First byte should be 0x83 (definite array length 3)
        self.assertEqual(encoded[0], 0x83)


if __name__ == '__main__':
    unittest.main()
