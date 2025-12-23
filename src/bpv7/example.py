#!/usr/bin/env python3
"""
BPv7 Usage Example

Demonstrates Bundle Protocol Version 7 operations per
CCSDS 734.20-O-1 / RFC 9171.
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bpv7 import (
    Bundle,
    DTNTime,
    EndpointID,
    crc16_x25,
    crc32c,
)


def main():
    print("=" * 60)
    print("Bundle Protocol Version 7 - Implementation Demo")
    print("Standards: CCSDS 734.20-O-1 / RFC 9171")
    print("=" * 60)
    print()

    # Create endpoints
    print("Creating Endpoint IDs...")
    source = EndpointID.ipn(1, 1)  # Node 1, Service 1
    destination = EndpointID.ipn(2, 1)  # Node 2, Service 1
    print(f"  Source:      {source}")
    print(f"  Destination: {destination}")
    print()

    # Create a bundle
    print("Creating Bundle...")
    payload_data = b"Hello from Bundle Protocol Version 7!"
    bundle = Bundle.create(
        destination=destination,
        source=source,
        payload=payload_data,
        lifetime_ms=3600000,  # 1 hour
    )
    print(f"  {bundle}")
    print(f"  Bundle ID: {bundle.bundle_id}")
    print(f"  Payload:   {bundle.payload.data.decode('utf-8')}")
    print(f"  Lifetime:  {bundle.primary.lifetime_ms} ms")
    print()

    # Encode to CBOR
    print("Encoding to CBOR...")
    encoded = bundle.encode()
    print(f"  Encoded size: {len(encoded)} bytes")
    print(f"  CBOR hex: {encoded[:40].hex()}...")
    print()

    # Decode from CBOR
    print("Decoding from CBOR...")
    decoded = Bundle.decode(encoded)
    print(f"  {decoded}")
    print(f"  Payload matches: {decoded.payload.data == payload_data}")
    print()

    # Demonstrate CRC calculation
    print("CRC Verification (RFC 9171 §4.2.1)...")
    test_data = b"Bundle Protocol Test"
    crc16 = crc16_x25(test_data)
    crc32 = crc32c(test_data)
    print(f"  CRC-16 X.25:   0x{crc16:04X}")
    print(f"  CRC-32C:       0x{crc32:08X}")
    print()

    # Demonstrate DTN time
    print("DTN Time (RFC 9171 §4.2.6)...")
    now = DTNTime.now()
    print(f"  Current DTN time: {now.milliseconds} ms since 2000-01-01")
    print(f"  As datetime:      {now.to_datetime().isoformat()}")
    print()

    # Expiration check
    print("Bundle Expiration...")
    print(f"  Expires at: {bundle.primary.expiration_time.to_datetime().isoformat()}")
    print(f"  Is expired: {bundle.is_expired()}")
    print()

    print("=" * 60)
    print("BPv7 Implementation Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
