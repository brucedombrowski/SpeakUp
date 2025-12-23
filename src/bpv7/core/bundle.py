"""
Bundle Container for Bundle Protocol Version 7

Implements the Bundle structure per RFC 9171 Section 4.2.

A bundle is an indefinite-length CBOR array containing:
- Primary block (exactly one, first)
- Payload block (exactly one)
- Extension blocks (zero or more)

Standards:
- RFC 9171 Section 4.2: Bundle Structure
- CCSDS 734.20-O-1 Section 4.2
"""

from typing import List, Optional, Iterator, Any
from dataclasses import dataclass, field

from .eid import EndpointID
from .time import CreationTimestamp, DTNTime
from ..blocks.primary import PrimaryBlock, BundleProcessingFlags, CRCType
from ..blocks.payload import (
    PayloadBlock, CanonicalBlock, BlockType,
    PreviousNodeBlock, BundleAgeBlock, HopCountBlock
)
from ..encoding.cbor import CBOREncoder, CBORDecoder


@dataclass
class Bundle:
    """
    Bundle Protocol Version 7 Bundle.

    A bundle is the protocol data unit of the Bundle Protocol.
    It consists of a primary block followed by one or more
    canonical blocks including exactly one payload block.

    CBOR Structure:
        Indefinite-length array [
            primary_block,
            canonical_block_1,  # payload
            canonical_block_2,  # extension (optional)
            ...
        ]

    Attributes:
        primary: The primary block
        payload: The payload block
        extensions: List of extension blocks
    """
    primary: PrimaryBlock
    payload: PayloadBlock
    extensions: List[CanonicalBlock] = field(default_factory=list)

    def __post_init__(self):
        # Validate payload block number
        if self.payload.block_number != 1:
            raise ValueError("Payload block must have block number 1")

        # Validate extension block numbers
        used_numbers = {0, 1}  # Reserved for primary and payload
        for ext in self.extensions:
            if ext.block_number in used_numbers:
                raise ValueError(f"Duplicate block number: {ext.block_number}")
            used_numbers.add(ext.block_number)

    @classmethod
    def create(
        cls,
        destination: EndpointID,
        source: EndpointID,
        payload: bytes,
        lifetime_ms: int = 3600000,  # 1 hour default
        report_to: Optional[EndpointID] = None,
        flags: BundleProcessingFlags = BundleProcessingFlags.NONE,
    ) -> 'Bundle':
        """
        Create a new bundle with specified parameters.

        Args:
            destination: Destination endpoint
            source: Source endpoint
            payload: Application data
            lifetime_ms: Bundle lifetime in milliseconds
            report_to: Status report destination (defaults to source)
            flags: Bundle processing flags

        Returns:
            New Bundle instance
        """
        if report_to is None:
            report_to = source

        primary = PrimaryBlock(
            destination=destination,
            source=source,
            report_to=report_to,
            creation_timestamp=CreationTimestamp.create(),
            lifetime_ms=lifetime_ms,
            flags=flags,
            crc_type=CRCType.CRC16,
        )

        payload_block = PayloadBlock(
            block_number=1,
            data=payload,
        )

        return cls(primary=primary, payload=payload_block)

    @property
    def destination(self) -> EndpointID:
        """Bundle destination endpoint."""
        return self.primary.destination

    @property
    def source(self) -> EndpointID:
        """Bundle source endpoint."""
        return self.primary.source

    @property
    def creation_time(self) -> CreationTimestamp:
        """Bundle creation timestamp."""
        return self.primary.creation_timestamp

    @property
    def is_fragment(self) -> bool:
        """Check if this bundle is a fragment."""
        return self.primary.is_fragment

    @property
    def is_admin_record(self) -> bool:
        """Check if this bundle contains an administrative record."""
        return self.primary.is_admin_record

    def is_expired(self, current_time: Optional[DTNTime] = None) -> bool:
        """Check if bundle has expired."""
        return self.primary.is_expired(current_time)

    def get_block(self, block_type: BlockType) -> Optional[CanonicalBlock]:
        """
        Get extension block by type.

        Args:
            block_type: Block type to find

        Returns:
            Block if found, None otherwise
        """
        if block_type == BlockType.PAYLOAD:
            return self.payload

        for ext in self.extensions:
            if ext.block_type == block_type:
                return ext
        return None

    def add_extension(self, block: CanonicalBlock) -> None:
        """
        Add an extension block to the bundle.

        Block numbers are automatically assigned if not set.

        Args:
            block: Extension block to add
        """
        if block.block_type == BlockType.PAYLOAD:
            raise ValueError("Cannot add payload as extension")

        # Auto-assign block number if needed
        if block.block_number <= 1:
            used = {0, 1} | {e.block_number for e in self.extensions}
            block.block_number = max(used) + 1

        self.extensions.append(block)

    def blocks(self) -> Iterator[Any]:
        """
        Iterate over all blocks in bundle order.

        Yields blocks in transmission order:
        primary, payload, extensions...
        """
        yield self.primary
        yield self.payload
        yield from self.extensions

    def encode(self) -> bytes:
        """
        Encode bundle to CBOR bytes.

        Returns:
            CBOR-encoded bundle as indefinite-length array
        """
        encoder = CBOREncoder()

        # Start indefinite-length array
        encoder.encode_indefinite_array_start()

        # Encode primary block
        encoder.encode(self.primary.to_cbor_array())

        # Encode payload block
        encoder.encode(self.payload.to_cbor_array())

        # Encode extension blocks
        for ext in self.extensions:
            encoder.encode(ext.to_cbor_array())

        # End indefinite-length array
        encoder.encode_break()

        return encoder.get_bytes()

    @classmethod
    def decode(cls, data: bytes) -> 'Bundle':
        """
        Decode bundle from CBOR bytes.

        Args:
            data: CBOR-encoded bundle

        Returns:
            Decoded Bundle

        Raises:
            ValueError: If bundle structure is invalid
        """
        decoder = CBORDecoder(data)
        blocks = decoder.decode()

        if not isinstance(blocks, list) or len(blocks) < 2:
            raise ValueError("Bundle must contain at least 2 blocks")

        # First block must be primary
        primary = PrimaryBlock.from_cbor_array(blocks[0])

        # Find payload block
        payload = None
        extensions = []

        for block_arr in blocks[1:]:
            block_type = block_arr[0]

            if block_type == BlockType.PAYLOAD:
                if payload is not None:
                    raise ValueError("Multiple payload blocks")
                payload = PayloadBlock.from_cbor_array(block_arr)
            else:
                # Extension block - basic handling
                # Full implementation would dispatch by block type
                extensions.append(block_arr)

        if payload is None:
            raise ValueError("Bundle missing payload block")

        return cls(primary=primary, payload=payload)

    @property
    def bundle_id(self) -> str:
        """
        Generate bundle identifier string.

        The bundle ID uniquely identifies a bundle:
        source-eid/creation-time/sequence/fragment-offset

        Returns:
            Bundle identifier string
        """
        parts = [
            str(self.source),
            str(self.creation_time.time.milliseconds),
            str(self.creation_time.sequence_number),
        ]

        if self.is_fragment:
            parts.append(str(self.primary.fragment_offset))

        return '/'.join(parts)

    def __len__(self) -> int:
        """Return payload length."""
        return len(self.payload)

    def __str__(self) -> str:
        return (
            f"Bundle({self.source} -> {self.destination}, "
            f"{len(self.payload)} bytes, "
            f"{len(self.extensions)} extensions)"
        )

    def __repr__(self) -> str:
        return f"Bundle(id={self.bundle_id})"
