"""
DTN Time and Timestamps for Bundle Protocol Version 7

Implements DTN time per RFC 9171 Section 4.2.6.

DTN Time:
- Epoch: 2000-01-01 00:00:00 UTC (946684800 Unix time)
- Resolution: 1 millisecond (optional sub-millisecond)
- Value 0 is reserved for "unknown" time

Standards:
- RFC 9171 Section 4.2.6: Creation Timestamp
- CCSDS 734.20-O-1 Section 4.2.6
"""

from typing import Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass


# DTN Epoch: 2000-01-01 00:00:00 UTC
DTN_EPOCH_UNIX = 946684800


@dataclass(frozen=True)
class DTNTime:
    """
    DTN Time representation.

    DTN time is milliseconds since 2000-01-01 00:00:00 UTC.
    A value of 0 indicates "unknown" or "no time value available".

    Attributes:
        milliseconds: Milliseconds since DTN epoch (0 = unknown)
    """
    milliseconds: int

    def __post_init__(self):
        if self.milliseconds < 0:
            raise ValueError("DTN time cannot be negative")

    @classmethod
    def now(cls) -> 'DTNTime':
        """Create DTNTime for the current moment."""
        unix_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        dtn_ms = unix_ms - (DTN_EPOCH_UNIX * 1000)
        return cls(milliseconds=dtn_ms)

    @classmethod
    def from_unix(cls, unix_timestamp: float) -> 'DTNTime':
        """Create DTNTime from Unix timestamp (seconds since 1970)."""
        unix_ms = int(unix_timestamp * 1000)
        dtn_ms = unix_ms - (DTN_EPOCH_UNIX * 1000)
        if dtn_ms < 0:
            raise ValueError("Unix timestamp is before DTN epoch (2000-01-01)")
        return cls(milliseconds=dtn_ms)

    @classmethod
    def from_datetime(cls, dt: datetime) -> 'DTNTime':
        """Create DTNTime from a datetime object."""
        if dt.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        return cls.from_unix(dt.timestamp())

    @classmethod
    def unknown(cls) -> 'DTNTime':
        """Create DTNTime representing unknown/unavailable time."""
        return cls(milliseconds=0)

    def to_unix(self) -> float:
        """Convert to Unix timestamp (seconds since 1970)."""
        if self.milliseconds == 0:
            raise ValueError("Cannot convert unknown time to Unix timestamp")
        return (self.milliseconds / 1000) + DTN_EPOCH_UNIX

    def to_datetime(self) -> datetime:
        """Convert to timezone-aware datetime object."""
        if self.milliseconds == 0:
            raise ValueError("Cannot convert unknown time to datetime")
        return datetime.fromtimestamp(self.to_unix(), tz=timezone.utc)

    @property
    def is_unknown(self) -> bool:
        """Check if this represents unknown time."""
        return self.milliseconds == 0

    def __str__(self) -> str:
        if self.is_unknown:
            return "DTNTime(unknown)"
        return f"DTNTime({self.to_datetime().isoformat()})"


@dataclass(frozen=True)
class CreationTimestamp:
    """
    Bundle Creation Timestamp per RFC 9171 Section 4.2.6.

    The creation timestamp is a two-element array:
    1. Bundle creation time (DTN time in milliseconds)
    2. Sequence number (to distinguish bundles with same creation time)

    If the bundle source EID is "dtn:none", the creation timestamp
    must be [0, 0] (unknown time, sequence 0).

    Attributes:
        time: DTN time of bundle creation
        sequence_number: Sequence count for bundles at same time
    """
    time: DTNTime
    sequence_number: int

    def __post_init__(self):
        if self.sequence_number < 0:
            raise ValueError("Sequence number cannot be negative")

    @classmethod
    def create(cls, sequence_number: int = 0) -> 'CreationTimestamp':
        """Create a timestamp for now with given sequence number."""
        return cls(time=DTNTime.now(), sequence_number=sequence_number)

    @classmethod
    def none(cls) -> 'CreationTimestamp':
        """Create a null timestamp for anonymous bundles (dtn:none source)."""
        return cls(time=DTNTime.unknown(), sequence_number=0)

    def to_cbor_array(self) -> Tuple[int, int]:
        """Return as CBOR array representation [time_ms, sequence]."""
        return (self.time.milliseconds, self.sequence_number)

    @classmethod
    def from_cbor_array(cls, arr: Tuple[int, int]) -> 'CreationTimestamp':
        """Create from CBOR array [time_ms, sequence]."""
        if len(arr) != 2:
            raise ValueError("Creation timestamp must be 2-element array")
        return cls(
            time=DTNTime(milliseconds=arr[0]),
            sequence_number=arr[1]
        )

    def __str__(self) -> str:
        return f"CreationTimestamp({self.time}, seq={self.sequence_number})"
