"""
ID generation utilities for StreamForge backend.

Provides UUID7 generation for time-ordered, unique identifiers.
UUID7 is a time-ordered UUID that combines timestamp with random data.
"""

import uuid
import time
from datetime import datetime


def generate_uuid7() -> str:
    """
    Generate a UUID v7 (time-ordered UUID).

    UUID7 format: tttttttt-tttt-7xxx-yxxx-xxxxxxxxxxxx
    - t: timestamp (48 bits)
    - 7: version
    - x: random data
    - y: variant bits

    UUID7 provides:
    - Time-based ordering (sortable)
    - Uniqueness (random component)
    - Compatibility with existing UUID infrastructure

    Returns:
        str: UUID7 string like "01932e4f-a4c2-7890-b123-456789abcdef"

    Example:
        >>> id1 = generate_uuid7()
        >>> id2 = generate_uuid7()
        >>> id1 < id2  # True (time-ordered)
    """
    # Get current timestamp in milliseconds
    timestamp_ms = int(time.time() * 1000)

    # Generate random bytes for the rest
    random_bytes = uuid.uuid4().bytes

    # Construct UUID7:
    # First 48 bits: timestamp
    # Next 4 bits: version (0111 = 7)
    # Remaining bits: random data with proper variant bits

    # Extract timestamp bytes (48 bits = 6 bytes)
    timestamp_bytes = timestamp_ms.to_bytes(8, byteorder='big')[-6:]

    # Combine timestamp with random data
    # Use format: timestamp (6 bytes) + random (10 bytes)
    uuid_bytes = bytearray(16)

    # Copy timestamp (first 6 bytes)
    uuid_bytes[0:6] = timestamp_bytes

    # Copy random data (remaining 10 bytes)
    uuid_bytes[6:16] = random_bytes[6:16]

    # Set version to 7 (bits 48-51)
    uuid_bytes[6] = (uuid_bytes[6] & 0x0F) | 0x70  # 0111xxxx

    # Set variant to RFC 4122 (bits 64-65)
    uuid_bytes[8] = (uuid_bytes[8] & 0x3F) | 0x80  # 10xxxxxx

    # Convert to UUID and return as string
    result_uuid = uuid.UUID(bytes=bytes(uuid_bytes))

    return str(result_uuid)


def generate_component_id() -> str:
    """
    Generate a unique component ID using UUID7.

    Alias for generate_uuid7() with more descriptive name
    for component generation context.

    Returns:
        str: UUID7 string for component identification
    """
    return generate_uuid7()


# Example usage and testing
if __name__ == "__main__":
    # Generate some UUIDs to verify time-ordering
    print("Generating UUID7 examples:")
    for i in range(5):
        uuid7 = generate_uuid7()
        print(f"  {i+1}. {uuid7}")
        time.sleep(0.01)  # Small delay to show time-ordering

    # Verify they are time-ordered
    uuids = [generate_uuid7() for _ in range(10)]
    sorted_uuids = sorted(uuids)
    print(f"\nTime-ordered: {uuids == sorted_uuids}")
