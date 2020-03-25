
import random


def str2bool(v):
    """Parse boolean value from string."""
    return str(v).lower() in ("true", "t", "1")


def random_replicate_name(len=12):
    """Return a random alphanumeric string of length `len`."""
    out = random.choices('abcdefghijklmnopqrtuvwxyzABCDEFGHIJKLMNOPQRTUVWXYZ0123456789', k=len)
    return ''.join(out)
