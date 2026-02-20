import string

# 62 characters: digits + lowercase + uppercase
# This lets us encode huge numbers into short strings
BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
# "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

SHORT_CODE_LENGTH = 7  # 62^7 = 3.5 trillion possible URLs


def encode(num: int) -> str:
    """
    Convert a database auto-increment ID into a base62 short code.
    
    Example:
        encode(1)        → "0000001"
        encode(1000000)  → "00004c92"  (trimmed to "4c92" then padded)
        encode(999999999) → "15ftgf"
    
    Why base62?
        - Only uses URL-safe characters (no special chars like +, /, =)
        - 7 chars supports 3.5 TRILLION unique URLs
        - No collisions possible (each DB ID is unique)
    """
    if num == 0:
        return BASE62_ALPHABET[0] * SHORT_CODE_LENGTH

    result = []
    while num > 0:
        result.append(BASE62_ALPHABET[num % 62])
        num //= 62

    # Reverse because we built it backwards
    encoded = "".join(reversed(result))

    # Pad with leading zeros to always have consistent length
    return encoded.zfill(SHORT_CODE_LENGTH)


def decode(short_code: str) -> int:
    """
    Convert a base62 short code back to the original integer ID.
    (Useful if you ever need to look up by ID instead of short_code)
    
    Example:
        decode("0000001") → 1
        decode("15ftgf")  → 999999999
    """
    result = 0
    for char in short_code:
        result = result * 62 + BASE62_ALPHABET.index(char)
    return result