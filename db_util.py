import time
import random
import string

def encode_base36(num: int) -> str:
    """Function to generate a base 36 string from an int."""
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    if num == 0:
        return "0"
    
    arr: list[str] = []
    while num > 0:
        num, rem = divmod(num, 36)
        arr.append(alphabet[rem])
    return "".join(reversed(arr))

def generate_id() -> str:
    """Function to generate a unique identifier for elements."""
    timestamp_ms = int(time.time() * 1000)
    part1 = encode_base36(timestamp_ms)
    
    base36_chars = string.digits + string.ascii_lowercase
    part2 = "".join(random.choices(base36_chars, k=5))
    
    return f"{part1}-{part2}".upper()