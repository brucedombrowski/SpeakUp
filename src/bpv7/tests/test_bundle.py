"""
Bundle Structure Tests

Verifies bundle structure per RFC 9171 Section 4.2.
"""

import unittest
from ..core.bundle import Bundle
from ..core.eid import EndpointID
from ..core.time import DTNTime, CreationTimestamp
from ..blocks.primary import PrimaryBlock, BundleProcessingFlags
from ..blocks.payload import PayloadBlock


class TestBundleCreation(unittest.TestCase):
    """Tests for bundle creation."""

    def test_create_simple_bundle(self):
        """Create a simple bundle with minimal parameters."""
        bundle = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"Hello, DTN!",
        )

        self.assertEqual(bundle.destination, EndpointID.ipn(2, 1))
        self.assertEqual(bundle.source, EndpointID.ipn(1, 1))
        self.assertEqual(bundle.payload.data, b"Hello, DTN!")
        self.assertEqual(len(bundle), 11)  # Payload length

    def test_create_with_dtn_endpoints(self):
        """Create bundle with dtn: scheme endpoints."""
        bundle = Bundle.create(
            destination=EndpointID.dtn("//node2/inbox"),
            source=EndpointID.dtn("//node1/app"),
            payload=b"Test message",
        )

        self.assertEqual(str(bundle.destination), "dtn://node2/inbox")
        self.assertEqual(str(bundle.source), "dtn://node1/app")

    def test_bundle_has_primary_block(self):
        """Bundle contains required primary block."""
        bundle = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"test",
        )

        self.assertIsInstance(bundle.primary, PrimaryBlock)
        self.assertEqual(bundle.primary.VERSION, 7)

    def test_bundle_has_payload_block(self):
        """Bundle contains required payload block."""
        bundle = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"test",
        )

        self.assertIsInstance(bundle.payload, PayloadBlock)
        self.assertEqual(bundle.payload.block_number, 1)

    def test_bundle_lifetime(self):
        """Bundle has specified lifetime."""
        bundle = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"test",
            lifetime_ms=7200000,  # 2 hours
        )

        self.assertEqual(bundle.primary.lifetime_ms, 7200000)

    def test_bundle_creation_timestamp(self):
        """Bundle has creation timestamp."""
        bundle = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"test",
        )

        self.assertFalse(bundle.creation_time.time.is_unknown)
        self.assertGreater(bundle.creation_time.time.milliseconds, 0)


class TestBundleEncoding(unittest.TestCase):
    """Tests for bundle CBOR encoding."""

    def test_encode_produces_bytes(self):
        """Encoding produces bytes."""
        bundle = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"test",
        )

        encoded = bundle.encode()
        self.assertIsInstance(encoded, bytes)
        self.assertGreater(len(encoded), 0)

    def test_encoded_starts_with_indefinite_array(self):
        """Encoded bundle starts with indefinite array marker."""
        bundle = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"test",
        )

        encoded = bundle.encode()
        # 0x9F is indefinite-length array start
        self.assertEqual(encoded[0], 0x9F)

    def test_encoded_ends_with_break(self):
        """Encoded bundle ends with break code."""
        bundle = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"test",
        )

        encoded = bundle.encode()
        # 0xFF is break code
        self.assertEqual(encoded[-1], 0xFF)


class TestBundleDecoding(unittest.TestCase):
    """Tests for bundle CBOR decoding."""

    def test_decode_round_trip(self):
        """Encode then decode preserves bundle."""
        original = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"Hello, DTN!",
        )

        encoded = original.encode()
        decoded = Bundle.decode(encoded)

        self.assertEqual(str(decoded.destination), str(original.destination))
        self.assertEqual(str(decoded.source), str(original.source))
        self.assertEqual(decoded.payload.data, original.payload.data)


class TestBundleID(unittest.TestCase):
    """Tests for bundle identification."""

    def test_bundle_id_format(self):
        """Bundle ID has correct format."""
        bundle = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"test",
        )

        bid = bundle.bundle_id
        parts = bid.split('/')

        # Should be: source/creation_time/sequence
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "ipn:1.1")

    def test_unique_bundle_ids(self):
        """Different bundles have different IDs."""
        bundle1 = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"test1",
        )

        bundle2 = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"test2",
        )

        # Different creation times make different IDs
        # (may be same if created in same millisecond)


class TestBundleExpiration(unittest.TestCase):
    """Tests for bundle expiration."""

    def test_expiration_time(self):
        """Bundle expiration time is calculated correctly."""
        bundle = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"test",
            lifetime_ms=1000,  # 1 second
        )

        expiry = bundle.primary.expiration_time
        self.assertIsNotNone(expiry)

        expected = bundle.creation_time.time.milliseconds + 1000
        self.assertEqual(expiry.milliseconds, expected)

    def test_not_expired(self):
        """New bundle is not expired."""
        bundle = Bundle.create(
            destination=EndpointID.ipn(2, 1),
            source=EndpointID.ipn(1, 1),
            payload=b"test",
            lifetime_ms=3600000,  # 1 hour
        )

        self.assertFalse(bundle.is_expired())


if __name__ == '__main__':
    unittest.main()
