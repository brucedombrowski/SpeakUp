"""
CRC Calculation for Bundle Protocol Version 7

Implements CRC-16 (X.25) and CRC-32C (Castagnoli) per RFC 9171 Section 4.2.1.

CRC Calculation Process:
1. Encode block with CRC field containing zeros
2. Calculate CRC over entire encoded block
3. Replace zero bytes with actual CRC value

Standards:
- RFC 9171 Section 4.2.1: CRC
- ITU-T X.25 (CRC-16)
- RFC 3720 (CRC-32C Castagnoli polynomial)
"""



# CRC-16 X.25 (HDLC) polynomial: x^16 + x^12 + x^5 + 1
# Reflected polynomial for LSB-first processing
CRC16_POLY = 0x8408  # Reflected 0x1021
CRC16_INIT = 0xFFFF
CRC16_XOR_OUT = 0xFFFF

# Pre-computed CRC-16 lookup table
_CRC16_TABLE = None


def _init_crc16_table():
    """Initialize CRC-16 X.25 lookup table."""
    global _CRC16_TABLE
    if _CRC16_TABLE is not None:
        return

    _CRC16_TABLE = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ CRC16_POLY
            else:
                crc >>= 1
        _CRC16_TABLE.append(crc)


def crc16_x25(data: bytes) -> int:
    """
    Calculate CRC-16 per ITU-T X.25 (HDLC FCS).

    This is the CRC used by BP when CRC type = 1.
    Uses reflected algorithm (LSB-first).

    Args:
        data: Input bytes

    Returns:
        16-bit CRC value
    """
    _init_crc16_table()

    crc = CRC16_INIT

    for byte in data:
        crc = _CRC16_TABLE[(crc ^ byte) & 0xFF] ^ (crc >> 8)

    return crc ^ CRC16_XOR_OUT


# CRC-32C (Castagnoli) polynomial: 0x1EDC6F41
# This is the iSCSI polynomial, more effective at detecting errors
# than the standard CRC-32 (Ethernet) polynomial
CRC32C_POLY = 0x82F63B78  # Reflected polynomial
CRC32C_INIT = 0xFFFFFFFF
CRC32C_XOR_OUT = 0xFFFFFFFF


# Pre-computed CRC-32C lookup table
_CRC32C_TABLE = None


def _init_crc32c_table():
    """Initialize CRC-32C lookup table."""
    global _CRC32C_TABLE
    if _CRC32C_TABLE is not None:
        return

    _CRC32C_TABLE = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ CRC32C_POLY
            else:
                crc >>= 1
        _CRC32C_TABLE.append(crc)


def crc32c(data: bytes) -> int:
    """
    Calculate CRC-32C (Castagnoli).

    This is the CRC used by BP when CRC type = 2.
    More effective error detection than standard CRC-32.

    Args:
        data: Input bytes

    Returns:
        32-bit CRC value
    """
    _init_crc32c_table()

    crc = CRC32C_INIT

    for byte in data:
        crc = _CRC32C_TABLE[(crc ^ byte) & 0xFF] ^ (crc >> 8)

    return crc ^ CRC32C_XOR_OUT


def calculate_block_crc(encoded_block: bytes, crc_type: int) -> bytes:
    """
    Calculate CRC for an encoded block.

    The block should be encoded with CRC field as zero bytes.

    Args:
        encoded_block: CBOR-encoded block with zero CRC
        crc_type: CRC type (0=none, 1=CRC-16, 2=CRC-32C)

    Returns:
        CRC bytes in network byte order
    """
    if crc_type == 0:
        return b''
    elif crc_type == 1:
        crc = crc16_x25(encoded_block)
        return crc.to_bytes(2, 'big')
    elif crc_type == 2:
        crc = crc32c(encoded_block)
        return crc.to_bytes(4, 'big')
    else:
        raise ValueError(f"Unknown CRC type: {crc_type}")


def verify_block_crc(encoded_block: bytes, crc_type: int) -> bool:
    """
    Verify CRC of an encoded block.

    For a valid block, the CRC calculated over the entire
    encoded block (including CRC field) should equal a
    known residue value.

    Args:
        encoded_block: Complete CBOR-encoded block with CRC
        crc_type: CRC type (0=none, 1=CRC-16, 2=CRC-32C)

    Returns:
        True if CRC is valid
    """
    if crc_type == 0:
        return True  # No CRC to verify

    # Extract CRC size
    if crc_type == 1:
        crc_size = 2
        expected_residue = 0x0F47  # CRC-16 X.25 good residue
    elif crc_type == 2:
        crc_size = 4
        expected_residue = 0x48674BC7  # CRC-32C good residue
    else:
        raise ValueError(f"Unknown CRC type: {crc_type}")

    if len(encoded_block) < crc_size:
        return False

    # Calculate CRC over entire block including CRC field
    if crc_type == 1:
        result = crc16_x25(encoded_block)
    else:
        result = crc32c(encoded_block)

    return result == expected_residue


def replace_crc_in_block(encoded_block: bytes, crc_type: int) -> bytes:
    """
    Replace zero CRC placeholder with calculated CRC.

    Args:
        encoded_block: CBOR-encoded block with zero CRC placeholder
        crc_type: CRC type (0=none, 1=CRC-16, 2=CRC-32C)

    Returns:
        Block with actual CRC value
    """
    if crc_type == 0:
        return encoded_block

    # Determine CRC size
    if crc_type == 1:
        crc_size = 2
    elif crc_type == 2:
        crc_size = 4
    else:
        raise ValueError(f"Unknown CRC type: {crc_type}")

    # Calculate CRC
    crc_bytes = calculate_block_crc(encoded_block, crc_type)

    # Replace the trailing zero bytes with actual CRC
    # The CRC field is the last element, which is a byte string
    # We need to find and replace the zero bytes
    return encoded_block[:-crc_size] + crc_bytes
