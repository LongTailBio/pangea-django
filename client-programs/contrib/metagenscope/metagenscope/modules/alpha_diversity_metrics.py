import math

MIL = 1000 * 1000


def shannon_entropy(row, rarefy=0):
    """Return the shannon entropy of an iterable.
    Shannon entropy is robust to rarefaction but we keep
    the param for consistency.
    """
    row_sum, H = sum(row), 0
    if row_sum == 0:
        return 0
    for val in row:
        val = val / row_sum
        if val == 0:
            continue
        H += val * math.log2(val)
    if H < 0:
        H *= -1
    return H


def richness(row, rarefy=0, count=False):
    """Return the richness of an iterable."""
    if count:
        return sum(row > 0)
    row_sum, R = sum(row), 0
    if row_sum == 0:
        return 0
    for val in row:
        prob_success = val / row_sum
        prob_fail = 1 - prob_success
        prob_detect = 1 - (prob_fail ** rarefy)
        if val and rarefy <= 0:
            R += 1
        else:
            R += prob_detect
    return int(R + 0.5)


def chao1(row, rarefy=0):
    """Return richnes of an iterable"""
    row_sum, R, S, D = sum(row), 0, 0, 0.0000001
    if row_sum == 0:
        return 0
    num_reads = MIL if math.isclose(row_sum, 1) else row_sum  # default to 1M reads if compositional
    num_reads = rarefy if rarefy > 0 else num_reads  # if rarefy is set use that as read count

    for val in row:
        prob_success = val / row_sum
        prob_fail = 1 - prob_success
        prob_detect = 1 - (prob_fail ** num_reads)

        if rarefy:
            R += prob_detect
        elif val:
            R += 1
        S += 1 if val == 1 else 0
        D += 1 if val == 2 else 0
    return R + (S ** 2) / (2 * D)
