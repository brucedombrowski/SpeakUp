"""
Primary Block for Bundle Protocol Version 7

Implements the Primary Block per RFC 9171 Section 4.3.1.

The primary block contains identifying and processing information
that applies to the bundle as a whole. It must be the first block
in every bundle.

Standards:
- RFC 9171 Section 4.3.1: Primary Block
- CCSDS 734.20-O-1 Section 4.3.1
"""

from dataclasses import dataclass
from enum import IntFlag
from typing import Any

from ..core.eid import EndpointID
from ..core.time import CreationTimestamp, DTNTime
from ..encoding.cbor import cbor_encode


class BundleProcessingFlags(IntFlag):
    """
    Bundle Processing Control Flags per RFC 9171 Section 4.2.3.

    These flags control how the bundle is processed throughout
    its lifetime in the DTN.
    """
    # No flags set
    NONE = 0x0000

    # Bundle is a fragment
    IS_FRAGMENT = 0x0001

    # Administrative record (status report, etc.)
    IS_ADMIN_RECORD = 0x0002

    # Bundle must not be fragmented
    DO_NOT_FRAGMENT = 0x0004

    # Request acknowledgment by destination
    REQUEST_ACK = 0x0008

    # Request status time in reports
    REQUEST_STATUS_TIME = 0x0040

    # Request reception status report
    REQUEST_RECEPTION_REPORT = 0x4000

    # Request forwarding status report
    REQUEST_FORWARD_REPORT = 0x10000

    # Request delivery status report
    REQUEST_DELIVERY_REPORT = 0x20000

    # Request deletion status report
    REQUEST_DELETE_REPORT = 0x40000


class CRCType(IntFlag):
    """CRC Type values per RFC 9171 Section 4.2.1."""
    NONE = 0      # No CRC
    CRC16 = 1     # CRC-16 (X.25)
    CRC32C = 2    # CRC-32C (Castagnoli)


@dataclass
class PrimaryBlock:
    """
    Bundle Primary Block per RFC 9171 Section 4.3.1.

    The primary block is an array with the following fields:
    [0] version (always 7)
    [1] bundle processing control flags
    [2] CRC type
    [3] destination EID
    [4] source node EID
    [5] report-to EID
    [6] creation timestamp
    [7] lifetime (milliseconds)
    [8] fragment offset (if IS_FRAGMENT flag set)
    [9] total ADU length (if IS_FRAGMENT flag set)
    [10] CRC value (if CRC type != 0)

    Attributes:
        destination: Where the bundle should be delivered
        source: Origin of the bundle
        report_to: Where to send status reports
        creation_timestamp: When bundle was created + sequence
        lifetime_ms: Bundle lifetime in milliseconds
        flags: Bundle processing control flags
        crc_type: Type of CRC to use
        fragment_offset: Offset if this is a fragment
        total_adu_length: Total length if this is a fragment
    """
    destination: EndpointID
    source: EndpointID
    report_to: EndpointID
    creation_timestamp: CreationTimestamp
    lifetime_ms: int
    flags: BundleProcessingFlags = BundleProcessingFlags.NONE
    crc_type: CRCType = CRCType.CRC16
    fragment_offset: int | None = None
    total_adu_length: int | None = None

    VERSION = 7  # Bundle Protocol Version 7

    def __post_init__(self):
        # Validate fragmentation fields
        is_fragment = bool(self.flags & BundleProcessingFlags.IS_FRAGMENT)
        has_frag_fields = (self.fragment_offset is not None or
                          self.total_adu_length is not None)

        if is_fragment and not has_frag_fields:
            raise ValueError("Fragment flag set but fragment fields missing")
        if has_frag_fields and not is_fragment:
            raise ValueError("Fragment fields present but IS_FRAGMENT flag not set")

        # Validate source EID for anonymous bundles
        if self.source.is_none:
            if not self.creation_timestamp.time.is_unknown:
                raise ValueError("Anonymous bundles must have unknown creation time")
            if self.creation_timestamp.sequence_number != 0:
                raise ValueError("Anonymous bundles must have sequence number 0")

        # Validate lifetime
        if self.lifetime_ms < 0:
            raise ValueError("Lifetime cannot be negative")

    @property
    def is_fragment(self) -> bool:
        """Check if this bundle is a fragment."""
        return bool(self.flags & BundleProcessingFlags.IS_FRAGMENT)

    @property
    def is_admin_record(self) -> bool:
        """Check if this bundle contains an administrative record."""
        return bool(self.flags & BundleProcessingFlags.IS_ADMIN_RECORD)

    @property
    def expiration_time(self) -> DTNTime | None:
        """
        Calculate bundle expiration time.

        Returns None if creation time is unknown.
        """
        if self.creation_timestamp.time.is_unknown:
            return None
        expiry_ms = self.creation_timestamp.time.milliseconds + self.lifetime_ms
        return DTNTime(milliseconds=expiry_ms)

    def is_expired(self, current_time: DTNTime | None = None) -> bool:
        """
        Check if bundle has expired.

        Args:
            current_time: Time to check against (defaults to now)

        Returns:
            True if expired, False if not or if expiration cannot be determined
        """
        expiry = self.expiration_time
        if expiry is None:
            return False  # Cannot determine expiration

        if current_time is None:
            current_time = DTNTime.now()

        return current_time.milliseconds > expiry.milliseconds

    def to_cbor_array(self) -> list[Any]:
        """
        Convert to CBOR array representation.

        Returns array suitable for CBOR encoding. CRC value is NOT
        included - it must be calculated after encoding.
        """
        # Base fields (always present)
        arr = [
            self.VERSION,
            int(self.flags),
            int(self.crc_type),
            list(self.destination.to_cbor_value()),
            list(self.source.to_cbor_value()),
            list(self.report_to.to_cbor_value()),
            list(self.creation_timestamp.to_cbor_array()),
            self.lifetime_ms,
        ]

        # Fragment fields (conditional)
        if self.is_fragment:
            arr.append(self.fragment_offset)
            arr.append(self.total_adu_length)

        # CRC placeholder - actual CRC calculated after encoding
        # For CRC calculation, we encode with CRC field as zero bytes
        # of appropriate length, then replace with actual CRC

        return arr

    def encode_for_crc(self) -> bytes:
        """
        Encode block with zero CRC for CRC calculation.

        The CRC is calculated over the block with the CRC field
        containing zeros, then the actual CRC replaces the zeros.
        """
        arr = self.to_cbor_array()

        # Add CRC placeholder
        if self.crc_type == CRCType.CRC16:
            arr.append(b'\x00\x00')  # 2 bytes
        elif self.crc_type == CRCType.CRC32C:
            arr.append(b'\x00\x00\x00\x00')  # 4 bytes
        # CRCType.NONE - no CRC field

        return cbor_encode(arr)

    @classmethod
    def from_cbor_array(cls, arr: list[Any]) -> 'PrimaryBlock':
        """
        Create PrimaryBlock from decoded CBOR array.

        Args:
            arr: Decoded CBOR array (CRC already verified/stripped)

        Returns:
            Decoded PrimaryBlock
        """
        if len(arr) < 8:
            raise ValueError(f"Primary block too short: {len(arr)} elements")

        version = arr[0]
        if version != 7:
            raise ValueError(f"Unsupported bundle version: {version}")

        flags = BundleProcessingFlags(arr[1])
        crc_type = CRCType(arr[2])
        destination = EndpointID.from_cbor_value(tuple(arr[3]))
        source = EndpointID.from_cbor_value(tuple(arr[4]))
        report_to = EndpointID.from_cbor_value(tuple(arr[5]))
        creation_ts = CreationTimestamp.from_cbor_array(tuple(arr[6]))
        lifetime_ms = arr[7]

        # Fragment fields
        fragment_offset = None
        total_adu_length = None
        if flags & BundleProcessingFlags.IS_FRAGMENT:
            if len(arr) < 10:
                raise ValueError("Fragment flag set but fragment fields missing")
            fragment_offset = arr[8]
            total_adu_length = arr[9]

        return cls(
            destination=destination,
            source=source,
            report_to=report_to,
            creation_timestamp=creation_ts,
            lifetime_ms=lifetime_ms,
            flags=flags,
            crc_type=crc_type,
            fragment_offset=fragment_offset,
            total_adu_length=total_adu_length,
        )

    def __str__(self) -> str:
        return (
            f"PrimaryBlock(v{self.VERSION}, "
            f"src={self.source}, dst={self.destination}, "
            f"lifetime={self.lifetime_ms}ms)"
        )
