"""
CRC Calculation Tests

Verifies CRC-16 and CRC-32C per RFC 9171 Section 4.2.1.
"""

import unittest
from ..encoding.crc import crc16_x25, crc32c, calculate_block_crc


class TestCRC16(unittest.TestCase):
    """Tests for CRC-16 X.25 implementation."""

    def test_crc16_empty(self):
        """CRC-16 of empty data."""
        result = crc16_x25(b'')
        # Initial XOR out gives 0xFFFF for empty
        self.assertIsInstance(result, int)

    def test_crc16_known_values(self):
        """CRC-16 matches known test vectors."""
        # "123456789" is a standard test vector
        data = b'123456789'
        result = crc16_x25(data)
        # X.25 CRC of "123456789" is 0x906E
        self.assertEqual(result, 0x906E)

    def test_crc16_deterministic(self):
        """Same input produces same CRC."""
        data = b'Hello, World!'
        crc1 = crc16_x25(data)
        crc2 = crc16_x25(data)
        self.assertEqual(crc1, crc2)


class TestCRC32C(unittest.TestCase):
    """Tests for CRC-32C (Castagnoli) implementation."""

    def test_crc32c_empty(self):
        """CRC-32C of empty data."""
        result = crc32c(b'')
        self.assertIsInstance(result, int)

    def test_crc32c_known_values(self):
        """CRC-32C matches known test vectors."""
        # "123456789" test vector for CRC-32C
        data = b'123456789'
        result = crc32c(data)
        # CRC-32C of "123456789" is 0xE3069283
        self.assertEqual(result, 0xE3069283)

    def test_crc32c_deterministic(self):
        """Same input produces same CRC."""
        data = b'Hello, World!'
        crc1 = crc32c(data)
        crc2 = crc32c(data)
        self.assertEqual(crc1, crc2)


class TestBlockCRC(unittest.TestCase):
    """Tests for block CRC calculation."""

    def test_no_crc(self):
        """CRC type 0 produces no CRC bytes."""
        result = calculate_block_crc(b'test', 0)
        self.assertEqual(result, b'')

    def test_crc16_produces_2_bytes(self):
        """CRC type 1 produces 2 bytes."""
        result = calculate_block_crc(b'test', 1)
        self.assertEqual(len(result), 2)

    def test_crc32c_produces_4_bytes(self):
        """CRC type 2 produces 4 bytes."""
        result = calculate_block_crc(b'test', 2)
        self.assertEqual(len(result), 4)

    def test_network_byte_order(self):
        """CRC bytes are in network (big-endian) order."""
        data = b'test'
        crc16 = crc16_x25(data)
        result = calculate_block_crc(data, 1)

        # Verify big-endian encoding
        expected = crc16.to_bytes(2, 'big')
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
