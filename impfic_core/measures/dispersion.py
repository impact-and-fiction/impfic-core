from typing import List


def compute_percentages(part_sizes: List[int]) -> List[float]:
    """Compute the percentages per part.

    :param part_sizes: the list of sizes per part (in number of tokens).
    :type part_sizes: List[int]
    :return: a list of percentages per corpus part.
    :rtype: List[float]
    """
    total_size = sum(part_sizes)
    return [part_size / total_size for part_size in part_sizes]


def compute_dispersion(part_sizes: List[int], part_freqs: List[int]) -> float:
    """Compute the deviation of proportions measure (DP) introduced by Stefan Gries in
    "Dispersions and adjusted frequencies in corpora". International Journal of
    Corpus Linguistics, 13 (4), 403-437.

    Example:

    Consider a corpus with four parts, with respectively 100, 200, 300 and 400 words.
    The total corpus size is then 100+200+300+400=1000 words.

    part_sizes: [100, 200, 300, 400]

    The expected percentages are then:

    [ 100/1000, 200/1000, 300/1000, 400/1000 ] = [0.1, 0.2, 0.3, 0.4]

    The frequency of a token A in each part is 5, 5, 15 and 15.
    The total frequency of A is thus 10+10+15+15 = 50

    part_freqs: [10, 10, 15, 15]

    The expected percentages are then:

    [ 10/50, 10/50, 15/50, 15/50 ] = [0.2, 0.2, 0.3, 0.3]

    The pairwise absolute differences are then:

    [abs(0.1 - 0.2), abs(0.2 - 0.2), abs(0.3 - 0.3), abs(0.4 - 0.3)] = [0.1, 0.0, 0.0, 0.1]

    The dispersion DP is the sum of differences divided by 2:

    (0.1 + 0.0 + 0.0 + 0.1) / 2 = 0.2 / 2 = 0.1

    :param part_sizes: the list of sizes per part (in number of tokens).
    :type part_sizes: List[int]
    :param part_freqs: the list of frequencies of a token per corpus part.
    :type part_freqs: List[int]
    :return: a list of observed percentages per corpus part.
    :rtype: List[float]
    """
    if len(part_sizes) != len(part_freqs):
        raise ValueError(f"part_sizes ({len(part_sizes)}) not same length as "
                   f"part_freqs ({len(part_freqs)}).")
    expected = compute_percentages(part_sizes)
    observed = compute_percentages(part_freqs)
    diffs = [abs(exp - obs) for exp, obs in zip(expected, observed)]
    return sum(diffs) / 2


def compute_dp_norm(part_sizes: List[int], part_freqs: List[int]) -> float:
    """Compute the normalised deviation of proportions measure."""
    expected = compute_percentages(part_sizes)
    observed = compute_percentages(part_freqs)
    diffs = [abs(exp - obs) for exp, obs in zip(expected, observed)]
    dp = sum(diffs) / 2
    return dp / (1 - min(expected))
