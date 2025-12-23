"""
Endpoint Identifier Tests

Verifies EID handling per RFC 9171 Section 4.2.5.
"""

import unittest

from ..core.eid import EIDScheme, EndpointID


class TestEndpointID(unittest.TestCase):
    """Tests for Endpoint Identifier handling."""

    def test_dtn_none(self):
        """dtn:none is the null endpoint."""
        eid = EndpointID.none()
        self.assertTrue(eid.is_none)
        self.assertEqual(eid.scheme, EIDScheme.DTN)
        self.assertEqual(eid.ssp, 0)
        self.assertEqual(str(eid), "dtn:none")

    def test_dtn_scheme(self):
        """dtn: scheme URIs."""
        eid = EndpointID.dtn("//node1/inbox")
        self.assertEqual(eid.scheme, EIDScheme.DTN)
        self.assertEqual(eid.ssp, "//node1/inbox")
        self.assertEqual(str(eid), "dtn://node1/inbox")
        self.assertFalse(eid.is_none)

    def test_ipn_scheme(self):
        """ipn: scheme numeric endpoints."""
        eid = EndpointID.ipn(1, 0)
        self.assertEqual(eid.scheme, EIDScheme.IPN)
        self.assertEqual(eid.ssp, (1, 0))
        self.assertEqual(str(eid), "ipn:1.0")
        self.assertFalse(eid.is_none)

        # Common IPN endpoints
        eid = EndpointID.ipn(42, 7)
        self.assertEqual(str(eid), "ipn:42.7")

    def test_parse_dtn_none(self):
        """Parse dtn:none string."""
        eid = EndpointID.parse("dtn:none")
        self.assertTrue(eid.is_none)

    def test_parse_dtn_uri(self):
        """Parse dtn: URI string."""
        eid = EndpointID.parse("dtn://node1/inbox")
        self.assertEqual(eid.scheme, EIDScheme.DTN)
        self.assertEqual(eid.ssp, "//node1/inbox")

    def test_parse_ipn(self):
        """Parse ipn: string."""
        eid = EndpointID.parse("ipn:1.0")
        self.assertEqual(eid.scheme, EIDScheme.IPN)
        self.assertEqual(eid.ssp, (1, 0))

        eid = EndpointID.parse("ipn:42.7")
        self.assertEqual(eid.ssp, (42, 7))

    def test_cbor_encoding_dtn_none(self):
        """dtn:none encodes as [1, 0]."""
        eid = EndpointID.none()
        cbor_val = eid.to_cbor_value()
        self.assertEqual(cbor_val, (1, 0))

    def test_cbor_encoding_dtn_uri(self):
        """dtn: URI encodes as [1, "uri"]."""
        eid = EndpointID.dtn("//node1/inbox")
        cbor_val = eid.to_cbor_value()
        self.assertEqual(cbor_val, (1, "//node1/inbox"))

    def test_cbor_encoding_ipn(self):
        """ipn: encodes as [2, [node, service]]."""
        eid = EndpointID.ipn(42, 7)
        cbor_val = eid.to_cbor_value()
        self.assertEqual(cbor_val, (2, [42, 7]))

    def test_cbor_round_trip(self):
        """CBOR encode/decode round trip."""
        eids = [
            EndpointID.none(),
            EndpointID.dtn("//node1/inbox"),
            EndpointID.ipn(1, 0),
            EndpointID.ipn(42, 7),
        ]

        for eid in eids:
            cbor_val = eid.to_cbor_value()
            decoded = EndpointID.from_cbor_value(cbor_val)
            self.assertEqual(decoded.scheme, eid.scheme)
            self.assertEqual(str(decoded), str(eid))

    def test_invalid_dtn_empty(self):
        """Empty DTN URI is invalid."""
        with self.assertRaises(ValueError):
            EndpointID.dtn("")

    def test_invalid_ipn_negative(self):
        """Negative IPN values are invalid."""
        with self.assertRaises(ValueError):
            EndpointID.ipn(-1, 0)
        with self.assertRaises(ValueError):
            EndpointID.ipn(0, -1)

    def test_invalid_parse(self):
        """Unknown scheme raises error."""
        with self.assertRaises(ValueError):
            EndpointID.parse("unknown:foo")


class TestEIDSingleton(unittest.TestCase):
    """Tests for singleton endpoint detection."""

    def test_ipn_is_singleton(self):
        """IPN endpoints are always singleton."""
        eid = EndpointID.ipn(1, 0)
        self.assertTrue(eid.is_singleton)

    def test_dtn_singleton(self):
        """Standard DTN endpoints are singleton."""
        eid = EndpointID.dtn("//node1/inbox")
        self.assertTrue(eid.is_singleton)


if __name__ == '__main__':
    unittest.main()
