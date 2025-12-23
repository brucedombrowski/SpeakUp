"""
Bundle Protocol Version 7 (BPv7) Implementation

A pure Python implementation of CCSDS 734.20-O-1 / RFC 9171
Bundle Protocol Version 7 for Delay-Tolerant Networking.

Standards:
- CCSDS 734.20-O-1: CCSDS Bundle Protocol Version 7
- RFC 9171: Bundle Protocol Version 7
- RFC 8949: Concise Binary Object Representation (CBOR)

Example Usage:
    from bpv7 import Bundle, EndpointID

    # Create a bundle
    bundle = Bundle.create(
        destination=EndpointID.dtn("//node2/inbox"),
        source=EndpointID.dtn("//node1/app"),
        payload=b"Hello, DTN!",
        lifetime_ms=3600000,  # 1 hour
    )

    # Encode to CBOR bytes
    encoded = bundle.encode()

    # Decode from CBOR bytes
    decoded = Bundle.decode(encoded)
"""

__version__ = "0.1.0"
__standards__ = [
    "CCSDS 734.20-O-1",
    "RFC 9171",
    "RFC 8949",
]

from .core.eid import EndpointID, EIDScheme
from .core.time import DTNTime, CreationTimestamp
from .core.bundle import Bundle
from .blocks.primary import PrimaryBlock, BundleProcessingFlags
from .blocks.payload import (
    PayloadBlock,
    CanonicalBlock,
    BlockProcessingFlags,
    BlockType,
    PreviousNodeBlock,
    BundleAgeBlock,
    HopCountBlock,
)
from .encoding.cbor import cbor_encode, cbor_decode
from .encoding.crc import crc16_x25, crc32c

__all__ = [
    # Core types
    'Bundle',
    'EndpointID',
    'EIDScheme',
    'DTNTime',
    'CreationTimestamp',
    # Blocks
    'PrimaryBlock',
    'PayloadBlock',
    'CanonicalBlock',
    'BundleProcessingFlags',
    'BlockProcessingFlags',
    'BlockType',
    'PreviousNodeBlock',
    'BundleAgeBlock',
    'HopCountBlock',
    # Encoding
    'cbor_encode',
    'cbor_decode',
    'crc16_x25',
    'crc32c',
]
