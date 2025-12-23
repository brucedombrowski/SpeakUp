"""
Payload Block and Canonical Block for Bundle Protocol Version 7

Implements:
- Canonical Block structure per RFC 9171 Section 4.3.2
- Payload Block (block type 1) per RFC 9171 Section 4.3.3

All blocks except the primary block use the canonical block structure.

Standards:
- RFC 9171 Section 4.3.2: Canonical Block Format
- RFC 9171 Section 4.3.3: Payload Block
- CCSDS 734.20-O-1 Sections 4.3.2-4.3.3
"""

from typing import Optional, List, Any
from dataclasses import dataclass, field
from enum import IntFlag, IntEnum
from abc import ABC, abstractmethod

from ..encoding.cbor import cbor_encode


class BlockType(IntEnum):
    """
    Block Type Codes per RFC 9171.

    Block type numbers are managed by IANA.
    """
    PAYLOAD = 1           # Payload block (required)
    PREVIOUS_NODE = 6     # Previous Node block
    BUNDLE_AGE = 7        # Bundle Age block
    HOP_COUNT = 10        # Hop Count block
    # Block types 192-255 are reserved for private/experimental use


class BlockProcessingFlags(IntFlag):
    """
    Block Processing Control Flags per RFC 9171 Section 4.2.4.

    These flags control how individual blocks are processed.
    """
    NONE = 0x00

    # Block must be replicated in every fragment
    REPLICATE_IN_FRAGMENT = 0x01

    # Report status if block cannot be processed
    REPORT_IF_UNPROCESSABLE = 0x02

    # Delete bundle if block cannot be processed
    DELETE_IF_UNPROCESSABLE = 0x04

    # Discard block if it cannot be processed
    DISCARD_IF_UNPROCESSABLE = 0x10


class CRCType(IntEnum):
    """CRC Type for canonical blocks."""
    NONE = 0
    CRC16 = 1
    CRC32C = 2


@dataclass
class CanonicalBlock(ABC):
    """
    Abstract base for all canonical (non-primary) blocks.

    Per RFC 9171 Section 4.3.2, canonical blocks are arrays:
    [0] block type code
    [1] block number
    [2] block processing control flags
    [3] CRC type
    [4] block-type-specific data
    [5] CRC value (if CRC type != 0)

    Block numbers:
    - 0 is reserved for primary block
    - 1 is reserved for payload block
    - Other blocks get unique numbers 2+

    Attributes:
        block_number: Unique identifier within bundle
        flags: Block processing control flags
        crc_type: Type of CRC to use
    """
    block_number: int
    flags: BlockProcessingFlags = BlockProcessingFlags.NONE
    crc_type: CRCType = CRCType.CRC16

    @property
    @abstractmethod
    def block_type(self) -> BlockType:
        """Return the block type code."""
        pass

    @abstractmethod
    def get_data(self) -> Any:
        """Return block-type-specific data for CBOR encoding."""
        pass

    def to_cbor_array(self) -> List[Any]:
        """
        Convert to CBOR array representation.

        CRC is NOT included - must be calculated after encoding.
        """
        return [
            int(self.block_type),
            self.block_number,
            int(self.flags),
            int(self.crc_type),
            self.get_data(),
        ]

    def encode_for_crc(self) -> bytes:
        """Encode block with zero CRC for CRC calculation."""
        arr = self.to_cbor_array()

        if self.crc_type == CRCType.CRC16:
            arr.append(b'\x00\x00')
        elif self.crc_type == CRCType.CRC32C:
            arr.append(b'\x00\x00\x00\x00')

        return cbor_encode(arr)


@dataclass
class PayloadBlock(CanonicalBlock):
    """
    Bundle Payload Block per RFC 9171 Section 4.3.3.

    The payload block contains the application data unit (ADU).
    Every bundle must have exactly one payload block with
    block number 1.

    The payload block-type-specific data is simply the
    payload bytes.

    Attributes:
        data: The application data (payload bytes)
    """
    data: bytes = field(default_factory=bytes)

    def __post_init__(self):
        # Payload block always has block number 1
        object.__setattr__(self, 'block_number', 1)

    @property
    def block_type(self) -> BlockType:
        return BlockType.PAYLOAD

    def get_data(self) -> bytes:
        """Return payload data."""
        return self.data

    @classmethod
    def from_cbor_array(cls, arr: List[Any]) -> 'PayloadBlock':
        """Create PayloadBlock from decoded CBOR array."""
        if len(arr) < 5:
            raise ValueError(f"Canonical block too short: {len(arr)} elements")

        block_type = arr[0]
        if block_type != BlockType.PAYLOAD:
            raise ValueError(f"Expected payload block type 1, got {block_type}")

        block_number = arr[1]
        if block_number != 1:
            raise ValueError(f"Payload block number must be 1, got {block_number}")

        flags = BlockProcessingFlags(arr[2])
        crc_type = CRCType(arr[3])
        data = arr[4]

        if not isinstance(data, bytes):
            raise ValueError(f"Payload data must be bytes, got {type(data)}")

        return cls(
            block_number=1,
            flags=flags,
            crc_type=crc_type,
            data=data,
        )

    def __len__(self) -> int:
        """Return payload length."""
        return len(self.data)

    def __str__(self) -> str:
        return f"PayloadBlock({len(self.data)} bytes)"


@dataclass
class PreviousNodeBlock(CanonicalBlock):
    """
    Previous Node Block per RFC 9171 Section 4.4.1.

    Contains the EID of the node that forwarded the bundle.
    Used for loop detection and route recording.

    Block type: 6
    """
    from ..core.eid import EndpointID
    previous_node: 'EndpointID' = field(default_factory=lambda: EndpointID.none())

    @property
    def block_type(self) -> BlockType:
        return BlockType.PREVIOUS_NODE

    def get_data(self) -> List:
        """Return previous node EID as CBOR array."""
        return list(self.previous_node.to_cbor_value())

    def __str__(self) -> str:
        return f"PreviousNodeBlock({self.previous_node})"


@dataclass
class BundleAgeBlock(CanonicalBlock):
    """
    Bundle Age Block per RFC 9171 Section 4.4.2.

    Contains the elapsed time since bundle creation in microseconds.
    Required when bundle source has no synchronized clock.

    Block type: 7
    """
    age_microseconds: int = 0

    @property
    def block_type(self) -> BlockType:
        return BlockType.BUNDLE_AGE

    def get_data(self) -> int:
        """Return age in microseconds."""
        return self.age_microseconds

    def __str__(self) -> str:
        return f"BundleAgeBlock({self.age_microseconds} µs)"


@dataclass
class HopCountBlock(CanonicalBlock):
    """
    Hop Count Block per RFC 9171 Section 4.4.3.

    Contains hop limit and current count for loop prevention.
    Bundle is discarded if hop count exceeds limit.

    Block type: 10
    """
    hop_limit: int = 255
    hop_count: int = 0

    @property
    def block_type(self) -> BlockType:
        return BlockType.HOP_COUNT

    def get_data(self) -> List[int]:
        """Return [hop_limit, hop_count] array."""
        return [self.hop_limit, self.hop_count]

    def increment(self) -> bool:
        """
        Increment hop count.

        Returns:
            True if still within limit, False if limit exceeded
        """
        self.hop_count += 1
        return self.hop_count <= self.hop_limit

    @property
    def exceeded(self) -> bool:
        """Check if hop count has exceeded limit."""
        return self.hop_count > self.hop_limit

    def __str__(self) -> str:
        return f"HopCountBlock({self.hop_count}/{self.hop_limit})"
