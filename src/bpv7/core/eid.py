"""
Endpoint Identifiers (EIDs) for Bundle Protocol Version 7

Implements EID handling per RFC 9171 Section 4.2.5.

EID Schemes:
- dtn: (scheme code 1) - URI-based naming
- ipn: (scheme code 2) - Numeric node/service naming

Standards:
- RFC 9171 Section 4.2.5: Endpoint IDs
- RFC 9171 Section 4.2.5.1: dtn Scheme
- RFC 9171 Section 4.2.5.2: ipn Scheme
- CCSDS 734.20-O-1 Section 4.2.5
"""

import re
from dataclasses import dataclass
from enum import IntEnum


class EIDScheme(IntEnum):
    """
    EID URI Scheme Codes per RFC 9171.

    These are the CBOR-encoded scheme identifiers.
    """
    DTN = 1   # dtn: scheme (URI-based)
    IPN = 2   # ipn: scheme (numeric)


# Special well-known EID for null endpoint
DTN_NONE_SSP = 0  # dtn:none is encoded as [1, 0]


@dataclass(frozen=True)
class EndpointID:
    """
    Bundle Protocol Endpoint Identifier.

    An EID uniquely identifies a bundle endpoint. It consists of:
    - A scheme (dtn or ipn)
    - A scheme-specific part (SSP)

    CBOR Encoding:
    - dtn:none -> [1, 0]
    - dtn:<uri> -> [1, <text-string>]
    - ipn:<node>.<service> -> [2, [<node>, <service>]]

    Attributes:
        scheme: The EID scheme (DTN or IPN)
        ssp: Scheme-specific part (varies by scheme)
    """
    scheme: EIDScheme
    ssp: int | str | tuple[int, int]

    def __post_init__(self):
        # Validate SSP based on scheme
        if self.scheme == EIDScheme.DTN:
            if not isinstance(self.ssp, (int, str)):
                raise ValueError("DTN scheme SSP must be int (0 for none) or string")
            if isinstance(self.ssp, int) and self.ssp != 0:
                raise ValueError("DTN scheme numeric SSP must be 0 (dtn:none)")
        elif self.scheme == EIDScheme.IPN:
            if not isinstance(self.ssp, tuple) or len(self.ssp) != 2:
                raise ValueError("IPN scheme SSP must be (node, service) tuple")
            node, service = self.ssp
            if not isinstance(node, int) or not isinstance(service, int):
                raise ValueError("IPN node and service must be integers")
            if node < 0 or service < 0:
                raise ValueError("IPN node and service must be non-negative")

    @classmethod
    def none(cls) -> 'EndpointID':
        """
        Create the null endpoint (dtn:none).

        The null endpoint is used when no endpoint can be identified,
        such as for anonymous bundles.
        """
        return cls(scheme=EIDScheme.DTN, ssp=0)

    @classmethod
    def dtn(cls, uri: str) -> 'EndpointID':
        """
        Create a dtn: scheme EID.

        Args:
            uri: The URI part after "dtn:" (e.g., "//node/service")

        Returns:
            EndpointID with DTN scheme

        Example:
            EndpointID.dtn("//node1/inbox")  # dtn://node1/inbox
        """
        if not uri:
            raise ValueError("DTN URI cannot be empty (use none() for dtn:none)")
        return cls(scheme=EIDScheme.DTN, ssp=uri)

    @classmethod
    def ipn(cls, node: int, service: int) -> 'EndpointID':
        """
        Create an ipn: scheme EID.

        Args:
            node: Node number (allocating authority assigns)
            service: Service number (demultiplexing identifier)

        Returns:
            EndpointID with IPN scheme

        Example:
            EndpointID.ipn(1, 0)  # ipn:1.0
        """
        return cls(scheme=EIDScheme.IPN, ssp=(node, service))

    @classmethod
    def parse(cls, eid_string: str) -> 'EndpointID':
        """
        Parse an EID from its string representation.

        Supported formats:
        - "dtn:none"
        - "dtn://node/service"
        - "ipn:node.service"

        Args:
            eid_string: String representation of EID

        Returns:
            Parsed EndpointID
        """
        if eid_string == "dtn:none":
            return cls.none()

        if eid_string.startswith("dtn:"):
            uri = eid_string[4:]  # Remove "dtn:" prefix
            return cls.dtn(uri)

        if eid_string.startswith("ipn:"):
            ipn_part = eid_string[4:]  # Remove "ipn:" prefix
            match = re.match(r'^(\d+)\.(\d+)$', ipn_part)
            if not match:
                raise ValueError(f"Invalid IPN EID format: {eid_string}")
            node = int(match.group(1))
            service = int(match.group(2))
            return cls.ipn(node, service)

        raise ValueError(f"Unknown EID scheme: {eid_string}")

    @property
    def is_none(self) -> bool:
        """Check if this is the null endpoint (dtn:none)."""
        return self.scheme == EIDScheme.DTN and self.ssp == 0

    @property
    def is_singleton(self) -> bool:
        """
        Check if this is a singleton endpoint.

        A singleton endpoint can have at most one bundle endpoint
        registered at any time. By convention:
        - dtn: endpoints are singleton if not explicitly multicast
        - ipn: endpoints are always singleton
        """
        # Simple heuristic - more sophisticated logic may be needed
        return self.scheme == EIDScheme.IPN or not str(self).startswith("dtn://~")

    def to_cbor_value(self) -> tuple:
        """
        Return CBOR array representation.

        Returns:
            - dtn:none -> (1, 0)
            - dtn:<uri> -> (1, "<uri>")
            - ipn:<n>.<s> -> (2, (n, s))
        """
        if self.scheme == EIDScheme.DTN:
            if self.ssp == 0:
                return (1, 0)
            return (1, self.ssp)
        else:  # IPN
            return (2, list(self.ssp))

    @classmethod
    def from_cbor_value(cls, value: tuple) -> 'EndpointID':
        """
        Create from CBOR array representation.

        Args:
            value: CBOR array [scheme_code, ssp]

        Returns:
            Decoded EndpointID
        """
        if len(value) != 2:
            raise ValueError("EID must be 2-element array")

        scheme_code, ssp = value

        if scheme_code == EIDScheme.DTN:
            if ssp == 0:
                return cls.none()
            if isinstance(ssp, str):
                return cls.dtn(ssp)
            raise ValueError(f"Invalid DTN SSP type: {type(ssp)}")

        elif scheme_code == EIDScheme.IPN:
            if isinstance(ssp, (list, tuple)) and len(ssp) == 2:
                return cls.ipn(ssp[0], ssp[1])
            raise ValueError(f"Invalid IPN SSP: {ssp}")

        else:
            raise ValueError(f"Unknown EID scheme code: {scheme_code}")

    def __str__(self) -> str:
        """Return string representation (URI format)."""
        if self.scheme == EIDScheme.DTN:
            if self.ssp == 0:
                return "dtn:none"
            return f"dtn:{self.ssp}"
        else:  # IPN
            node, service = self.ssp
            return f"ipn:{node}.{service}"

    def __repr__(self) -> str:
        return f"EndpointID({self})"
