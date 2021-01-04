
VERSION = 'v3.1.0'


def version_to_ints(a):
    a = [int(el) for el in a.split('v')[-1].split('.')]
    return a


def compare_versions(a, b):
    """Return 0 if a == b, 1 if a > b, else -1."""
    a, b = version_to_ints(a), version_to_ints(b)
    for i in range(min(len(a), len(b))):
        if a[i] > b[i]:
            return 1
        elif a[i] < b[i]:
            return -1
    return 0
